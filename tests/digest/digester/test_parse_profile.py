import pytest

from digest.digester import ProfileParseError, _parse_profile


def test_parse_profile():
    profile = "https://mastodon.social/@username"
    expected = ("https://mastodon.social", "@username")
    actual = _parse_profile(profile)
    assert expected == actual


def test_parse_profile_with_spaces():
    profile = "  https://mastodon.social/@username    "
    expected = ("https://mastodon.social", "@username")
    actual = _parse_profile(profile)
    assert expected == actual


def test_parse_profile_without_username():
    profile = "https://mastodon.social/username"

    with pytest.raises(ProfileParseError):
        _parse_profile(profile)


def test_parse_profile_without_https():
    profile = "mastodon.social/@username"

    with pytest.raises(ProfileParseError):
        _parse_profile(profile)


def test_parse_profile_without_dot():
    profile = "mastodonsocial/@username"

    with pytest.raises(ProfileParseError):
        _parse_profile(profile)
