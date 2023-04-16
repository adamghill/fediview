import logging

from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from account.models import Profile
from activity.postgres_indexer import index_posts

logger = logging.getLogger(__name__)


@db_periodic_task(crontab(minute="*/1"))
def every_one_min():
    profiles = Profile.objects.filter(has_plus=True).exclude(
        indexing_type=Profile.IndexingType.NONE
    )

    logger.info(f"Found {len(profiles)} profiles for indexing")

    for profile in profiles:
        print(f"Index posts for {profile} with huey")
        index_posts(profile)
