from unittest.mock import patch

from digest.digester import build_digest
from mastodon import MastodonError

INIT_KWARGS = {
    "hours": "1",
    "scorer_name": "Simple",
    "threshold_name": "lax",
    "mastodon_token": "fake-token",
    "mastodon_base_url": "https://fake-url.social",
    "mastodon_username": "@fake-username",
    "timeline": "home",
}


@patch("digest.digester.Mastodon")
@patch("digest.digester.fetch_posts_and_boosts", return_value=([], []))
def test_make_digest_ok_true(fetch_posts_and_boosts, Mastodon):
    actual = build_digest(**INIT_KWARGS)

    assert actual
    assert actual.ok is True
    assert actual.posts == []
    assert actual.boosts == []


@patch("digest.digester.Mastodon")
def test_build_digest_throws_mastodon_error(Mastodon):
    Mastodon.side_effect = MastodonError("error 1", "error 2")

    actual = build_digest(**INIT_KWARGS)

    assert actual
    assert actual.ok is False
    assert actual.error == "error 2"


@patch("digest.digester.Mastodon")
def test_build_digest_throws_exception(Mastodon):
    Mastodon.side_effect = Exception("some random error")

    actual = build_digest(**INIT_KWARGS)

    assert actual
    assert actual.ok is False
    assert actual.error == "some random error"
