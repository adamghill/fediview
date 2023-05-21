import logging

from django.core.management.base import BaseCommand

from ...email_sender import send_emails

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        send_emails()
