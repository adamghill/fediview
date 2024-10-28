import logging
from time import sleep

from django.core.management.base import BaseCommand

from digest.email_sender import send_emails

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = ""

    def handle(self, *args, **options):
        # while True:
        #     send_emails()

        #     sleep(60)
        pass
