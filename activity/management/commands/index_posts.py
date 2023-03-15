import logging

from django.core.management.base import BaseCommand

from account.models import Profile
from activity.postgres_indexer import index_posts

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = ""

    def add_arguments(self, parser):
        parser.add_argument("profile_id", type=int)

    def handle(self, *args, **options):
        profile_id = options["profile_id"]

        profile = Profile.objects.get(id=profile_id)

        index_posts(profile)
