import logging
from datetime import datetime, timedelta, timezone

from django.core.management.base import BaseCommand
from django.db.models import Q
from post_office.models import STATUS, Email

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        emails = Email.objects.filter(
            status=STATUS.sent, last_updated__lte=yesterday
        ).exclude(Q(message="") & Q(html_message="") & Q(context__isnull=True))

        logger.info(f"Found {len(emails)} emails to sanitize")

        for email in emails:
            logger.info(f"Sanitize email id {email.id}")
            email.html_message = ""
            email.message = ""
            email.context = None
            email.save()

        logger.info("Done sanitizing")
