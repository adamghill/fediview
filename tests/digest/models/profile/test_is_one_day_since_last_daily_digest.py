import pytest
from dateutil.relativedelta import relativedelta
from django.utils.timezone import now

from account.models import Profile


@pytest.mark.freeze_time("2024-01-21 02:12:12.516515")
def test_last_sent_24_hours_ago():
    last_daily_digest_sent_at = now() + relativedelta(hours=-24)

    profile = Profile(daily_digest_hour=1, daily_digest_am=True, last_daily_digest_sent_at=last_daily_digest_sent_at)
    actual = profile.is_one_day_since_last_daily_digest

    assert actual is True


@pytest.mark.freeze_time("2024-01-21 02:12:12.516515")
def test_last_sent_23_hours_ago():
    last_daily_digest_sent_at = now() + relativedelta(hours=-23)

    profile = Profile(daily_digest_hour=1, daily_digest_am=True, last_daily_digest_sent_at=last_daily_digest_sent_at)
    actual = profile.is_one_day_since_last_daily_digest

    assert actual is False
