import logging
from datetime import datetime, timedelta
from os import getenv
from time import sleep

import django_rq
from django.forms import ValidationError
from django_unicorn.components import UnicornView
from rq.job import JobStatus

from digest.digester import Digest, InvalidURLError, UnauthorizedError, build_digest

logger = logging.getLogger(__name__)


JOB_TIMEOUT = 30


class TimelineView(UnicornView):
    hours: str = "2"
    scorer: str = "SimpleWeighted"
    threshold: str = "normal"
    timeline: str = "home"  # TODO: Support hashtag:tagName, list:list-name
    url: str = ""
    token: str = ""
    error: str = ""

    has_results: bool = False
    posts: list[dict] = []
    boosts: list[dict] = []

    def mount(self):
        self.url = getenv("MASTODON_INSTANCE_URL", "")
        self.token = getenv("MASTODON_TOKEN", "")

    def hydrate(self):
        self.errors = {}
        self.posts = []
        self.boosts = []
        self.has_results = False

    def clean(self) -> None:
        validation_errors = {}

        if not self.url:
            validation_errors["url"] = "Missing URL"

        if not self.token:
            validation_errors["token"] = "Missing token"

        if validation_errors:
            raise ValidationError(validation_errors, code="required")

    def get_results(self):
        self.errors = {}
        self.clean()

        digest = Digest()

        try:
            job = django_rq.enqueue(
                build_digest,
                self.hours,
                self.scorer,
                self.threshold,
                self.timeline,
                self.url,
                self.token,
            )
            logger.info(f"Job enqueued: {job.id}")

            # Job gets put into cancel state when `ASYNC=False` and if
            # the worker times out
            JOB_OK_STATES = (
                JobStatus.FINISHED.value,
                JobStatus.CANCELED.value,
            )

            while job.get_status() not in JOB_OK_STATES:
                sleep(0.5)

                if job.enqueued_at + timedelta(0, JOB_TIMEOUT) < datetime.now():
                    logger.error(f"Run job manually: {job.id}")

                    # Explicitly run the worker since the job hasn't been picked up, yet
                    job.perform()
                    job.cancel()

                    break

            # Job gets put into cancel state when `ASYNC=False` and if
            # the worker times out, but there should still be a result
            if job.get_status() in JOB_OK_STATES and job.result:
                logger.info(f"Job finished: {job.id}")
                digest = job.result
        except UnauthorizedError as e:
            raise ValidationError({"token": str(e)}, code="invalid") from e
        except InvalidURLError as e:
            raise ValidationError({"url": str(e)}, code="invalid") from e

        if digest.error:
            self.error = digest.error

            if self.error.startswith("Version check failed"):
                self.error = f"URL might be invalid: {self.error}"

        self.posts = digest.posts
        self.boosts = digest.boosts
        self.has_results = digest.ok is True

    class Meta:
        javascript_exclude = (
            "token",
            "url",
            "posts",
            "boosts",
            "has_results",
            "error",
        )
