from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from mastodon import MastodonError

from digest.digester import build_digest

INIT_KWARGS = {
    "start": datetime.now(timezone.utc) - timedelta(hours=1),
    "end": None,
    "scorer_name": "Simple",
    "threshold_name": "lax",
    "timeline": "home",
    "url": "https://fake-url.social",
    "token": "fake-token",
}


@patch("digest.digester.Mastodon")
@patch("digest.digester.fetch_posts_and_boosts", return_value=([], []))
def test_make_digest_ok_true(fetch_posts_and_boosts, Mastodon):
    actual = build_digest(**INIT_KWARGS)

    assert actual
    assert actual.ok is False
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
