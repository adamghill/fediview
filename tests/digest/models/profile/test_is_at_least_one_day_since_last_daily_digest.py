from datetime import datetime
from zoneinfo import ZoneInfo

import time_machine
from dateutil.relativedelta import relativedelta
from django.utils.timezone import now

from account.models import Profile

UTC_TZ = ZoneInfo("UTC")


@time_machine.travel(datetime(2024, 1, 21, 2, 12, tzinfo=UTC_TZ))
def test_last_sent_24_hours_ago():
    last_daily_digest_sent_at = now() + relativedelta(hours=-24)

    profile = Profile(daily_digest_hour=1, daily_digest_am=True, last_daily_digest_sent_at=last_daily_digest_sent_at)
    actual = profile.is_at_least_one_day_since_last_daily_digest

    assert actual is True


@time_machine.travel(datetime(2024, 1, 21, 2, 12, tzinfo=UTC_TZ))
def test_last_sent_23_hours_ago():
    last_daily_digest_sent_at = now() + relativedelta(hours=-23)

    profile = Profile(daily_digest_hour=1, daily_digest_am=True, last_daily_digest_sent_at=last_daily_digest_sent_at)
    actual = profile.is_at_least_one_day_since_last_daily_digest

    assert actual is False
