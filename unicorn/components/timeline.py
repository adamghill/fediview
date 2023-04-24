import logging
from datetime import datetime, timedelta, timezone
from os import getenv

from django.core.exceptions import ObjectDoesNotExist
from django.forms import ValidationError
from django.utils.timezone import now
from django_q.models import Success
from django_q.tasks import async_task, fetch
from django_unicorn.components import UnicornView

from account.models import Account, Profile
from digest.digester import (
    Digest,
    InvalidURLError,
    Link,
    UnauthorizedError,
    build_digest,
)

logger = logging.getLogger(__name__)


TASK_TIMEOUT = 60


class TimelineView(UnicornView):
    hours: str = "2"
    scorer: str = "SimpleWeighted"
    threshold: str = "normal"
    timeline: str = "home"  # TODO: Support hashtag:tagName, list:list-name
    url: str = ""
    token: str = ""
    error: str = ""

    show_authorization: bool = True
    show_configure: bool = False
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
                self.show_authorization = False
                self.show_configure = True

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

    def manually_authorize(self):
        self.errors = {}
        self.clean()

        self.reconfigure()

    def reconfigure(self):
        self.show_authorization = False
        self.show_configure = True
        self.has_results = False

        self.call("updateHours")

    def reauthorize(self):
        self.show_authorization = True
        self.show_configure = False
        self.has_results = False

        self.call("saveLocal")

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

        profile = None

        try:
            profile = self.request.user.account.profile
        except Exception:
            pass

        try:
            task_id = async_task(
                build_digest,
                start,
                end,
                self.scorer,
                self.threshold,
                self.timeline,
                self.url,
                self.token,
                profile=profile,
                cached=True,
            )
            logger.info(f"Job enqueued: {task_id}")

            task = fetch(task_id, wait=TASK_TIMEOUT * 1000, cached=True)

            if not task:
                logger.error(f"Run job manually: {task_id}")

                digest = build_digest(
                    start,
                    end,
                    self.scorer,
                    self.threshold,
                    self.timeline,
                    self.url,
                    self.token,
                    profile=profile,
                    skip_recommendations=True,
                )

            if task and task.success and task.result:
                logger.info(f"Job finished: {task_id}")
                digest = task.result

                # Clear result from the database
                task.result = None
                task.save()
            elif digest.ok:
                logger.info(f"Profile id {profile.id}: Task failed, but sync digest ok")
            else:
                if profile:
                    logger.error(
                        f"Profile id {profile.id}: Task failed and sync digest failed"
                    )
                    self.error = "Failed to generate digest. Please try again."
                else:
                    logger.error("Task failed and sync digest failed")
                    self.error = "Failed to generate digest. Please check instance url and application token."

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
        self.show_configure = not self.has_results

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
            "show_authorization",
            "show_configure",
            "are_posts_shown",
            "are_boosts_shown",
            "are_links_shown",
        )
