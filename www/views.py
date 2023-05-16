from uuid import uuid4

import httpx
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.cache import cache
from django.http import HttpRequest
from django.shortcuts import redirect
from fbv.decorators import render_html

from account.models import GitHubAccount
from unicorn.components.sponsor import check_sponsorship


@render_html("www/index.html")
def index(request):
    return {}


def _get_redirect_uri(request):
    site = get_current_site(request)
    redirect_uri = f"https://{site.domain}/plus/oauth"

    return redirect_uri


@render_html("www/plus.html")
def plus(request):
    return {}


@login_required
def plus_auth(request):
    client_id = settings.GITHUB_CLIENT_ID
    redirect_uri = _get_redirect_uri(request)
    state = str(uuid4())

    cache.set(f"github:oauth:{state}", request.user.id, timeout=500)

    url = f"https://github.com/login/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&scope=read:user&state={state}"

    return redirect(url)


def _get_access_token(request: HttpRequest) -> str:
    redirect_uri = _get_redirect_uri(request)

    code = request.GET.get("code")
    assert code, "code is required"

    res = httpx.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": redirect_uri,
        },
        headers={"Accept": "application/json"},
    )

    res.raise_for_status()
    data = res.json()

    access_token = data["access_token"]

    return access_token


def _get_username(access_token: str) -> str:
    res = httpx.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
        },
    )

    res.raise_for_status()
    user_json = res.json()
    github_username = user_json["login"]

    return github_username


@login_required
def plus_oauth(request):
    state = request.GET.get("state")
    assert state, "state is required"

    user_id = cache.get(f"github:oauth:{state}")

    if not user_id:
        raise Exception("Invalid state")

    assert request.user.id == user_id, "Oauth user not same as logged in user"

    access_token = _get_access_token(request)

    github_username = _get_username(access_token)

    github_account = GitHubAccount(
        account=request.user.account,
        access_token=access_token,
        username=github_username,
    )
    github_account.save()

    if check_sponsorship(github_username):
        messages.success(request, "Thank you for sponsoring me!")

        return redirect("/account")

    return redirect("/plus#sign-up")
