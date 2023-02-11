from uuid import uuid4

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.cache import cache
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from fbv.decorators import render_html
from mastodon import Mastodon

from account.models import Account, Instance, User

SCOPES = ["read", "write"]


def get_redirect_uri(request):
    site_domain = get_current_site(request).domain
    site_url = f"https://{site_domain}"
    auth_path = reverse("account:auth")

    return site_url + auth_path


@render_html("account/login.html")
def login(request):
    redirect_uri = get_redirect_uri(request)

    if request.is_post:
        api_base_url = request.POST.get("url").strip()

        api_base_url = api_base_url.replace("https://", "").replace("http://", "")

        if api_base_url.endswith("/"):
            api_base_url = api_base_url[0:-1]

        instance = Instance.objects.filter(api_base_url=api_base_url).first()

        if not instance:
            (client_id, client_secret) = Mastodon.create_app(
                "fediview.com",
                scopes=SCOPES,
                redirect_uris=redirect_uri,
                website="https://fediview.com",
                api_base_url=api_base_url,
            )

            instance = Instance(
                api_base_url=api_base_url,
                client_id=client_id,
                client_secret=client_secret,
            )
            instance.save()

        state = str(uuid4())

        mastodon = Mastodon(api_base_url=api_base_url)
        auth_request_url = mastodon.auth_request_url(
            client_id=instance.client_id,
            state=state,
            redirect_uris=redirect_uri,
            scopes=SCOPES,
        )

        cache.set(f"oauth:{state}", instance.id, timeout=500)

        return redirect(auth_request_url)

    return {"ANALYTICS_HTML": settings.ANALYTICS_HTML}


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
    )

    access_token = mastodon.log_in(
        code=code,
        redirect_uri=redirect_uri,
        scopes=SCOPES,
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

        if not profile.has_plus:
            raise Exception(f"User {request.user.id} is not plus")
        
        if request.POST.get("language", "__all__") == "__all__":
            profile.language = None
        else:    
            profile.language = request.POST.get("language")
        
        profile.save()
        messages.success(request, "Profile saved")

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
