from account.models import Profile


def test_morning():
    expected = 1

    profile = Profile(daily_digest_hour=1, daily_digest_am=True)
    actual = profile.daily_digest_zero_based_index_hour

    assert actual == expected


def test_afternoon():
    expected = 13

    profile = Profile(daily_digest_hour=1, daily_digest_am=False)
    actual = profile.daily_digest_zero_based_index_hour

    assert actual == expected
