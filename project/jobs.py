import logging

import cronitor
from django_rq import job

from account.models import Profile
from activity.postgres_indexer import index_posts
from digest.digester import build_digest

logger = logging.getLogger(__name__)


@job
@cronitor.job("fediview:index_posts_for_plus_profiles")
def index_posts_for_plus_profiles():
    profiles = Profile.objects.filter(has_plus=True).exclude(
        indexing_type=Profile.IndexingType.NONE
    )

    logger.info(f"Found {len(profiles)} profiles for indexing")

    for profile in profiles:
        index_posts(profile)


@job
def get_digests_for_plus_profiles():
    profiles = Profile.objects.filter(has_plus=True)

    # TODO: Check for scheduled delivery time (daily, weekly? every Monday?)

    logger.info(f"Found {len(profiles)} profiles for digests")

    for profile in profiles:
        # index_posts(profile)
        # run digest and send email here

        digest = build_digest(
            start=start,
            scorer_name="",
            threshold_name="",
            timeline="",
            url="",
            token="",
            profile=profile,
        )

        # send email
