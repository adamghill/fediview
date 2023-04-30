import logging
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
from django.views.decorators.http import require_POST
from django_q.tasks import async_task
from fbv.decorators import render_html
from mastodon import Mastodon, MastodonNetworkError

from account.models import Account, Instance, User
from activity.indexer import index_posts

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
        api_base_url = request.POST.get("url", "").strip()
        api_base_url = api_base_url.replace("https://", "").replace("http://", "")

        scopes = get_scopes(request)

        if api_base_url.endswith("/"):
            api_base_url = api_base_url[0:-1]

        if "/" in api_base_url:
            api_base_url = api_base_url.split("/")[0]

        instance = Instance.objects.filter(api_base_url=api_base_url).first()

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

    user = User.objects.filter(username=username).first()

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


@login_required
@render_html("account/account.html")
def account(request):
    if request.is_post:
        profile = request.user.account.profile
        assert profile.has_plus, "Plus is required"

        message = "Profile saved"

        if request.POST.get("language", "__all__") == "__all__":
            profile.language = None
        else:
            profile.language = request.POST.get("language")

        original_indexing_type = profile.indexing_type
        profile.indexing_type = int(request.POST.get("indexing_type", "1"))

        if profile.indexing_type == profile.IndexingType.NONE.value:
            pass
        else:
            # Start indexing posts if the user updated their indexing type
            if original_indexing_type != profile.indexing_type:
                task_id = async_task(index_posts, profile)

                logger.info(f"Start indexing posts with {task_id}")

                message = f"{message} and start to index posts"

        profile.save()
        messages.success(request, message)

        return redirect("account:account")

    return {}


@require_POST
@login_required
def delete(request):
    user_id = request.user.id
    auth_logout(request)

    Account.objects.filter(user__id=user_id).delete()
    User.objects.filter(id=user_id).delete()

    messages.success(request, "Account has been deleted")

    return redirect("www:index")
