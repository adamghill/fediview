import logging
from datetime import datetime, timedelta, timezone
from os import getenv
from time import sleep

import django_rq
from django.core.exceptions import ObjectDoesNotExist
from django.forms import ValidationError
from django.utils.timezone import now
from django_unicorn.components import UnicornView
from rq.job import JobStatus

from account.models import Account, Profile
from digest.digester import (
    Digest,
    InvalidURLError,
    Link,
    UnauthorizedError,
    build_digest,
)

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
    links: list[Link] = []
    are_posts_shown: bool = False
    are_boosts_shown: bool = False
    are_links_shown: bool = False

    def mount(self):
        self.url = getenv("MASTODON_INSTANCE_URL", "")
        self.token = getenv("MASTODON_TOKEN", "")

        if self.request.user.is_authenticated:
            account = Account.objects.filter(user=self.request.user).first()

            if account:
                self.url = account.instance.api_base_url
                self.token = account.access_token

                try:
                    if account.profile:
                        self.hours = str(account.profile.hours)
                        self.scorer = account.profile.scorer
                        self.threshold = account.profile.threshold
                        self.timeline = account.profile.timeline
                except ObjectDoesNotExist:
                    pass

    def hydrate(self):
        self.errors = {}

    def display_posts(self):
        self.has_results = True
        self.are_posts_shown = True
        self.are_boosts_shown = False
        self.are_links_shown = False

    def display_boosts(self):
        self.has_results = True
        self.are_posts_shown = False
        self.are_boosts_shown = True
        self.are_links_shown = False

    def display_links(self):
        self.has_results = True
        self.are_posts_shown = False
        self.are_boosts_shown = False
        self.are_links_shown = True

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

        self.has_results = False

        self.are_posts_shown = False
        self.posts = []

        self.are_boosts_shown = False
        self.boosts = []

        self.are_links_shown = False
        self.links = []

        digest = Digest()

        start = datetime.now(timezone.utc) - timedelta(hours=int(self.hours))
        end = None

        try:
            job = django_rq.enqueue(
                build_digest,
                start,
                end,
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
        self.links = digest.links

        self.has_results = digest.ok is True
        self.are_posts_shown = self.has_results

        if self.request.user.is_authenticated:
            account = Account.objects.filter(user=self.request.user).first()

            if account:
                profile = Profile.objects.filter(account=account).first()

                if profile:
                    profile.hours = int(self.hours)
                    profile.scorer = self.scorer
                    profile.threshold = self.threshold
                    profile.timeline = self.timeline
                else:
                    profile = Profile(
                        account=account,
                        hours=int(self.hours),
                        scorer=self.scorer,
                        threshold=self.threshold,
                        timeline=self.timeline,
                    )

                profile.last_retrieval = now()
                profile.save()

    class Meta:
        javascript_exclude = (
            "token",
            "url",
            "posts",
            "boosts",
            "links",
            "has_results",
            "error",
        )
