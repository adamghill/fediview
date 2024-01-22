import pytest
from dateutil.relativedelta import relativedelta
from django.utils.timezone import now

from account.models import Profile

DAILY_DIGEST_HOURS = [
    (1, True),
    (2, True),
    (3, False),
]


@pytest.mark.parametrize("daily_digest_hour, expected", DAILY_DIGEST_HOURS)
@pytest.mark.freeze_time("2024-01-21 02:12:12.516515")
def test_first_send(daily_digest_hour, expected):
    """Is it time to send the daily digest for the first daily digest send"""

    profile = Profile(daily_digest_hour=daily_digest_hour, daily_digest_am=True)
    actual = profile.is_time_to_send_daily_digest

    assert actual is expected


@pytest.mark.parametrize("daily_digest_hour, expected", DAILY_DIGEST_HOURS)
@pytest.mark.freeze_time("2024-01-21 02:12:12.516515")
def test_last_send_23_hours_ago(daily_digest_hour, expected):
    """Is it time to send the daily digest since it's been 23 hours since the last send"""

    yesterday_sent_at = now() + relativedelta(hours=-23)
    profile = Profile(
        daily_digest_hour=daily_digest_hour, daily_digest_am=True, last_daily_digest_sent_at=yesterday_sent_at
    )
    actual = profile.is_time_to_send_daily_digest

    # ignore expected because they should all be False
    assert actual is False


@pytest.mark.parametrize("daily_digest_hour, expected", DAILY_DIGEST_HOURS)
@pytest.mark.freeze_time("2024-01-21 02:12:12.516515")
def test_last_send_24_hours_ago(daily_digest_hour, expected):
    """Is it time to send the daily digest since it's been 24 hours since the last send"""

    yesterday_sent_at = now() + relativedelta(hours=-24)
    profile = Profile(
        daily_digest_hour=daily_digest_hour, daily_digest_am=True, last_daily_digest_sent_at=yesterday_sent_at
    )
    actual = profile.is_time_to_send_daily_digest

    assert actual is expected
