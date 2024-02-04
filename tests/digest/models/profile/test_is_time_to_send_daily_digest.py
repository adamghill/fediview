from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
import time_machine
from dateutil.relativedelta import relativedelta
from django.utils.timezone import now

from account.models import Profile

UTC_TZ = ZoneInfo("UTC")

DAILY_DIGEST_DATA = [
    (1, 15, False),
    (2, 0, True),
    (2, 15, False),
    (3, 0, False),
]


@pytest.mark.parametrize("daily_digest_hour, daily_digest_minute, expected", DAILY_DIGEST_DATA)
@time_machine.travel(datetime(2024, 1, 21, 2, 12, tzinfo=UTC_TZ))
def test_first_send(daily_digest_hour, daily_digest_minute, expected):
    """Is it time to send the daily digest for the first daily digest send"""

    profile = Profile(
        daily_digest_hour=daily_digest_hour, daily_digest_am=True, daily_digest_minute=daily_digest_minute
    )
    actual = profile.is_time_to_send_daily_digest

    assert actual is expected


@pytest.mark.parametrize("daily_digest_hour, daily_digest_minute, expected", DAILY_DIGEST_DATA)
@time_machine.travel(datetime(2024, 1, 21, 2, 0, tzinfo=UTC_TZ))
def test_first_send_exact_time(daily_digest_hour, daily_digest_minute, expected):
    """Is it time to send the daily digest for the first daily digest send"""

    profile = Profile(
        daily_digest_hour=daily_digest_hour, daily_digest_am=True, daily_digest_minute=daily_digest_minute
    )
    actual = profile.is_time_to_send_daily_digest

    assert actual is expected


@pytest.mark.parametrize("daily_digest_hour, daily_digest_minute, expected", DAILY_DIGEST_DATA)
@time_machine.travel(datetime(2024, 1, 21, 4, 12, tzinfo=UTC_TZ))
def test_first_send_later_hour(daily_digest_hour, daily_digest_minute, expected):
    """Is it time to send the daily digest for the first daily digest send"""

    profile = Profile(
        daily_digest_hour=daily_digest_hour, daily_digest_am=True, daily_digest_minute=daily_digest_minute
    )
    actual = profile.is_time_to_send_daily_digest

    assert actual is False


@pytest.mark.parametrize("daily_digest_hour, daily_digest_minute, expected", DAILY_DIGEST_DATA)
@time_machine.travel(datetime(2024, 1, 21, 2, 12, tzinfo=UTC_TZ))
def test_last_send_less_than_an_hour_ago(daily_digest_hour, daily_digest_minute, expected):
    """Is it time to send the daily digest since it's been 59 minutes?

    Should always be `False`
    """

    yesterday_sent_at = now() + relativedelta(minutes=-59)
    profile = Profile(
        daily_digest_hour=daily_digest_hour,
        daily_digest_am=True,
        daily_digest_minute=daily_digest_minute,
        last_daily_digest_sent_at=yesterday_sent_at,
    )
    actual = profile.is_time_to_send_daily_digest

    # Ignore expected because they should all be False because it hasn't been enough time
    assert actual is False


@pytest.mark.parametrize("daily_digest_hour, daily_digest_minute, expected", DAILY_DIGEST_DATA)
@time_machine.travel(datetime(2024, 1, 21, 2, 12, tzinfo=UTC_TZ))
def test_last_send_more_than_an_hour_ago(daily_digest_hour, daily_digest_minute, expected):
    """Is it time to send the daily digest since it's been an hour?"""

    yesterday_sent_at = now() + relativedelta(hours=-1)
    profile = Profile(
        daily_digest_hour=daily_digest_hour,
        daily_digest_am=True,
        daily_digest_minute=daily_digest_minute,
        last_daily_digest_sent_at=yesterday_sent_at,
    )
    actual = profile.is_time_to_send_daily_digest

    assert actual is expected
