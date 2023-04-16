import logging

import cronitor
from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from account.models import Profile
from activity.postgres_indexer import index_posts

logger = logging.getLogger(__name__)


@db_periodic_task(crontab(minute="57"))
def index_posts_for_plus_profiles():
    monitor = cronitor.Monitor("fediview:index_posts_for_plus_profiles")
    monitor.ping(state="run")

    try:
        profiles = Profile.objects.filter(has_plus=True).exclude(
            indexing_type=Profile.IndexingType.NONE
        )

        logger.info(f"Found {len(profiles)} profiles for indexing")

        for profile in profiles:
            logger.info(f"Index posts for {profile} with huey")
            index_posts(profile)

        monitor.ping(state="complete")
    except Exception:
        monitor.ping(state="fail")
