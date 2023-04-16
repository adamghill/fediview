import logging

import cronitor
from django_rq import job

from account.models import Profile
from activity.postgres_indexer import index_posts

logger = logging.getLogger(__name__)


@job
def index_posts_for_plus_profiles():
    profiles = Profile.objects.filter(has_plus=True).exclude(
        indexing_type=Profile.IndexingType.NONE
    )

    logger.info(f"Found {len(profiles)} profiles for indexing")

    for profile in profiles:
        index_posts(profile)
