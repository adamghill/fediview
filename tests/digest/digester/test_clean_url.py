import pytest

from digest.digester import InvalidURLError, _clean_url

parameters = (
    ("https://mastodon.social", "mastodon.social"),
    ("http://mastodon.social", "mastodon.social"),
    ("http://mastodon.social/", "mastodon.social"),
    ("mastodon.social/", "mastodon.social"),
    ("http://mastodon.social/@username", "mastodon.social"),
)


@pytest.mark.parametrize("url, expected", parameters)
def test_clean_url(url: str, expected: str):
    actual = _clean_url(url)

    assert expected == actual


def test_clean_url_invalid():
    with pytest.raises(InvalidURLError):
        _clean_url("mastodonsocial")
