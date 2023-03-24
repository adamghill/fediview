from os import getenv

import pytest
from mastodon import Mastodon

from digest.digester import _add_following_to_account
from digest.models import Account


@pytest.fixture
def mastodon_client():
    token = getenv("MASTODON_TOKEN")
    url = getenv("MASTODON_INSTANCE_URL")

    mastodon = Mastodon(access_token=token, api_base_url=url, user_agent="fediview")

    return mastodon


@pytest.mark.integration
def test_add_following(mastodon_client):
    logged_in_account = Account.parse_obj(mastodon_client.me())

    _add_following_to_account(mastodon_client, logged_in_account)

    assert len(logged_in_account.follows) > 100
