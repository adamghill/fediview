import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.cache import cache
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.timezone import now
from django.views.decorators.http import require_POST
from django_q.tasks import async_task
from fbv.decorators import render_html
from mastodon import Mastodon, MastodonNetworkError
from pytz import common_timezones

from account.models import Account, Instance, User
from activity.indexer import index_posts
from digest.digester import build_digest
from digest.email_sender import get_email_context, send_emails

logger = logging.getLogger(__name__)

DEFAULT_SCOPES = ["read"]
ALLOWED_SCOPES = set(["read", "write"])


def get_redirect_uri(request):
    site_domain = get_current_site(request).domain
    site_url = f"https://{site_domain}"
    auth_path = reverse("account:auth")

    return site_url + auth_path


def get_scopes(request: HttpRequest) -> list:
    scopes = request.POST.get("scopes", DEFAULT_SCOPES[0]).split(",")
    assert not set(scopes) - ALLOWED_SCOPES, "Only read and write scopes are allowed"

    return scopes


@render_html("account/login.html")
def login(request):
    redirect_uri = get_redirect_uri(request)

    if request.is_post:
        api_base_url = request.POST.get("url", "").strip().lower()
        api_base_url = api_base_url.replace("https://", "").replace("http://", "")

        scopes = get_scopes(request)

        if api_base_url.endswith("/"):
            api_base_url = api_base_url[0:-1]

        if "/" in api_base_url:
            api_base_url = api_base_url.split("/")[0]

        instance = Instance.objects.filter(api_base_url__iexact=api_base_url).first()

        if not instance:
            try:
                (client_id, client_secret) = Mastodon.create_app(
                    "fediview.com",
                    scopes=scopes,
                    redirect_uris=redirect_uri,
                    website="https://fediview.com",
                    api_base_url=api_base_url,
                )
            except MastodonNetworkError:
                return {
                    "error": f"Invalid instance url: {api_base_url}",
                }

            instance = Instance(
                api_base_url=api_base_url,
                client_id=client_id,
                client_secret=client_secret,
            )
            instance.save()

        state = str(uuid4())

        mastodon = Mastodon(api_base_url=api_base_url, user_agent="fediview")
        auth_request_url = mastodon.auth_request_url(
            client_id=instance.client_id,
            state=state,
            redirect_uris=redirect_uri,
            scopes=scopes,
        )

        cache.set(f"oauth:{state}", instance.id, timeout=500)

        return redirect(auth_request_url)

    return {
        "scopes": ",".join(request.GET.getlist("scopes", DEFAULT_SCOPES)),
        "instance": request.GET.get("instance"),
    }


@render_html("account/auth.html")
def auth(request):
    redirect_uri = get_redirect_uri(request)

    code = request.GET.get("code")
    state = request.GET.get("state")

    instance_id = cache.get(f"oauth:{state}")
    assert instance_id, "State could not be found in cache"

    instance = Instance.objects.get(id=instance_id)

    mastodon = Mastodon(
        api_base_url=instance.api_base_url,
        client_id=instance.client_id,
        client_secret=instance.client_secret,
        user_agent="fediview",
    )

    scopes = get_scopes(request)

    access_token = mastodon.log_in(
        code=code,
        redirect_uri=redirect_uri,
        scopes=scopes,
    )

    # get username for Django user
    logged_in_account = mastodon.me()
    username = logged_in_account["username"]
    server_host = instance.api_base_url.replace("https://", "").replace("http://", "")
    username = f"@{username}@{server_host}"

    user = User.objects.filter(username__iexact=username).first()

    if not user:
        user = User(username=username)
        user.save()

    account = Account.objects.filter(user=user).first()

    if not account:
        account = Account(user=user, access_token=access_token, instance=instance)
        account.save()

    # force log the user in
    auth_login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])

    messages.success(request, "Login successful")

    return redirect("www:index")


@require_POST
@login_required
def logout(request):
    auth_logout(request)
    messages.success(request, "Logout successful")

    return redirect("www:index")


def query_string_bool_parse(request: HttpRequest, qs: str) -> bool:
    if request.GET.get(qs).lower() == "true":
        return True

    return False


@login_required
@render_html("digest/digest.html")
def sample_email_digest(request):
    assert settings.DEBUG, "No debug, no service"

    start = datetime.now(timezone.utc) - timedelta(days=1)

    account = Account.objects.select_related("profile").filter(user=request.user).first()

    if not (digest := cache.get("digest")) or query_string_bool_parse(request, "no_cache"):
        digest = build_digest(
            start=start,
            end=None,
            scorer_name=account.profile.scorer,
            threshold_name=account.profile.threshold,
            timeline=account.profile.timeline,
            url=account.instance.api_base_url,
            token=account.access_token,
            profile=account.profile,
        )
        cache.set("digest", digest, 60 * 60)

    has_plus = account.profile.has_plus

    if request.GET.get("has_plus"):
        has_plus = query_string_bool_parse(request, "has_plus")

    context = get_email_context(digest, has_plus)

    return context


@login_required
@render_html("account/unsubscribe.html")
def unsubscribe(request):
    if request.is_post:
        if request.POST.get("unsubscribe"):
            profile = request.user.account.profile
            profile.send_daily_digest = False
            profile.save()

            messages.success(request, "Unsubscribed from daily email")

            return redirect("account:account")

    return {"support_email": settings.SUPPORT_EMAIL}


@login_required
@render_html("account/account.html")
def account(request):
    profile = request.user.account.profile

    show_send_sample_email = False

    if profile.last_sample_email_sent_at is None or profile.last_sample_email_sent_at < (now() - timedelta(hours=1)):
        show_send_sample_email = True

    if request.is_post:
        message = "Profile saved"

        if profile.has_plus:
            if request.POST.get("language", "__all__") == "__all__":
                profile.language = None
            else:
                profile.language = request.POST.get("language")

            original_indexing_type = profile.indexing_type
            profile.indexing_type = int(request.POST.get("indexing_type", "1"))

            if profile.indexing_type == profile.IndexingType.NONE.value:
                pass
            elif original_indexing_type != profile.indexing_type:
                # Start indexing posts if the user updated their indexing type
                task_id = async_task(index_posts, profile)

                logger.info(f"Start indexing posts with {task_id}")

                message = f"{message} and start to index posts"

            profile.generate_recommendations = request.POST.get("generate_recommendations", "") == "on"

        profile.send_daily_digest = request.POST.get("send_daily_digest", "") == "on"

        current_hour_and_minute = (profile.daily_digest_hour, profile.daily_digest_minute)
        profile.daily_digest_hour = request.POST.get("daily_digest_hour", "1")
        profile.daily_digest_minute = request.POST.get("daily_digest_minute", "0")
        profile.daily_digest_am = request.POST.get("daily_digest_am", "am") == "am"

        if current_hour_and_minute != (profile.daily_digest_hour, profile.daily_digest_minute):
            # reset the last daily digest sent so that user will get the email the next time they hit hour:minute
            # and not have to wait 24 hours after the last send + hour:minute
            profile.last_daily_digest_sent_at = None

        profile.save()

        profile.account.user.email = request.POST.get("email-address")
        profile.account.user.save()

        if request.POST.get("send_daily_digest_sample") and show_send_sample_email:
            async_task(send_emails, request.user.account.id, force=True)

            profile.last_sample_email_sent_at = now()
            profile.save()

            message = f"{message} and sample email sent"

        messages.success(request, message)

        return redirect("account:account")

    return {"show_send_sample_email": show_send_sample_email, "timezones": common_timezones}


@require_POST
@login_required
def delete(request):
    user_id = request.user.id
    auth_logout(request)

    Account.objects.filter(user__id=user_id).delete()
    User.objects.filter(id=user_id).delete()

    messages.success(request, "Account has been deleted")

    return redirect("www:index")
