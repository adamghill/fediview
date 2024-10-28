import logging

from django_q.brokers import get_broker
from django_q.tasks import async_task

from account.models import Profile
from activity.indexer import index_posts

logger = logging.getLogger(__name__)


def index_posts_for_plus_profiles():
    profiles = Profile.objects.filter(has_plus=True, last_index_error__isnull=True).exclude(
        indexing_type=Profile.IndexingType.NONE
    )

    logger.info(f"Found {len(profiles)} profiles for indexing")

    broker = get_broker()

    for profile in profiles:
        async_task(index_posts, profile, broker=broker)
