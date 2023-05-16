import pytest
from model_bakery import baker


@pytest.fixture()
def user(db, tp):
    return tp.make_user()


@pytest.fixture()
def instance(db):
    return baker.make(
        "account.Instance",
        api_base_url="https://fake-mastodon.social",
        client_id="fake-mastodon-client-id",
        client_secret="fake-mastodon-client-secret",
    )


@pytest.fixture()
def account(db, tp, instance, user):
    return baker.make(
        "account.Account",
        instance=instance,
        user=user,
        access_token="fake-access-token",
    )
