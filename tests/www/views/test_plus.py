from unittest.mock import patch

import pytest
from django.core.cache import cache


def test_plus(tp):
    tp.get_check_200("www:plus")


@pytest.mark.django_db
def test_plus_auth(tp, settings):
    settings.GITHUB_CLIENT_ID = "fake-github-id"

    user = tp.make_user("user1")

    with tp.login(user):
        tp.get("www:plus_auth")

        assert tp.last_response.status_code == 302

        assert tp.last_response.url.startswith(
            "https://github.com/login/oauth/authorize?client_id=fake-github-id&redirect_uri=https://example.com/plus/oauth&scope=read:user&state="
        )


@pytest.mark.django_db
@patch("www.views._get_access_token", return_value="fake-access_token")
@patch("www.views._get_username", return_value="fake-username")
@patch("www.views.check_sponsorship", return_value=True)
def test_plus_oauth_is_sponsor(
    _get_username,
    _get_access_token,
    check_sponsorship,
    tp,
    settings,
    state,
    code,
    account,
):
    settings.GITHUB_CLIENT_ID = "fake-github-id"

    with tp.login(account.user):
        cache.set(f"github:oauth:{state}", account.user.id)

        tp.get("www:plus_oauth", data={"state": state, "code": code})

        assert tp.last_response.status_code == 302
        assert tp.last_response.url == "/account"


@pytest.mark.django_db
@patch("www.views._get_access_token", return_value="fake-access_token")
@patch("www.views._get_username", return_value="fake-username")
@patch("www.views.check_sponsorship", return_value=False)
def test_plus_oauth_not_sponsor(
    _get_username,
    _get_access_token,
    check_sponsorship,
    tp,
    settings,
    state,
    code,
    account,
):
    settings.GITHUB_CLIENT_ID = "fake-github-id"

    with tp.login(account.user):
        cache.set(f"github:oauth:{state}", account.user.id)

        tp.get("www:plus_oauth", data={"state": state, "code": code})

        assert tp.last_response.status_code == 302
        assert tp.last_response.url == "/plus#sign-up"
