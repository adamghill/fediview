import logging
from datetime import datetime, timedelta, timezone
from os import getenv

from dateparser import parse
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import validate_email
from django.forms import ValidationError
from django.utils.timezone import now
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


TASK_TIMEOUT = 60 * 5


class TimelineView(UnicornView):
    account: Account = None
    email_address: str = None

    hours: str = "2"
    scorer: str = "SimpleWeighted"
    threshold: str = "normal"
    timeline: str = "home"  # TODO: Support hashtag:tagName, list:list-name
    url: str = ""
    token: str = ""
    error: str = ""

    checking_for_results: bool = False
    task_id: str = None
    task_started_at: datetime = None
    digest = None

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
            self.account = Account.objects.filter(user=self.request.user).first()

            if self.account:
                self.url = self.account.instance.api_base_url
                self.token = self.account.access_token
                self.show_authorization = False
                self.show_configure = True

                self.email_address = self.account.user.email.strip()

                try:
                    if self.account.profile:
                        self.hours = str(self.account.profile.hours)
                        self.scorer = self.account.profile.scorer
                        self.threshold = self.account.profile.threshold
                        self.timeline = self.account.profile.timeline
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

    def check_results(self):
        if self.task_id is None:
            return

        try:
            # Make sure that `task_started_at` is a `datetime`
            if self.task_started_at and type(self.task_started_at) is str:
                self.task_started_at = parse(self.task_started_at)
        except Exception:
            pass

        task = fetch(self.task_id)

        if task:
            self.checking_for_results = False

            if task.success and task.result:
                logger.info(f"Job finished: {task.id}")
                self.digest = task.result

                # Clear result from the database
                task.result = None
                task.save()

                self.show_digest()
            else:
                logger.error(f"{task.id} failed")
                self.error = f"Error generating task {task.id}. Please try again."
        elif self.task_started_at + timedelta(seconds=TASK_TIMEOUT) <= datetime.now():
            self.checking_for_results = False

            logger.error(f"{task.id} timed out")
            self.error = f"Task {task.id} timed out. Please try again."

    def show_digest(self):
        if self.digest.error:
            self.error = self.digest.error

            if self.error.startswith("Version check failed"):
                self.error = f"URL might be invalid: {self.error}"

        self.posts = self.digest.posts
        self.boosts = self.digest.boosts
        self.links = self.digest.links

        self.has_results = self.digest.ok is True
        self.are_posts_shown = self.has_results
        self.show_configure = not self.has_results

        if self.request.user.is_authenticated:
            account = Account.objects.filter(user=self.request.user).first()

            if account:
                self.profile = Profile.objects.filter(account=account).first()

                if self.profile:
                    self.profile.hours = int(self.hours)
                    self.profile.scorer = self.scorer
                    self.profile.threshold = self.threshold
                    self.profile.timeline = self.timeline
                else:
                    self.profile = Profile(
                        account=account,
                        hours=int(self.hours),
                        scorer=self.scorer,
                        threshold=self.threshold,
                        timeline=self.timeline,
                    )

                self.profile.last_retrieval = now()
                self.profile.save()

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

        self.digest = Digest()

        self.start = datetime.now(timezone.utc) - timedelta(hours=int(self.hours))
        self.end = None

        self.profile = None

        try:
            self.profile = self.request.user.account.profile
        except Exception:
            pass

        self.task_started_at = datetime.now()

        try:
            self.task_id = async_task(
                build_digest,
                self.start,
                self.end,
                self.scorer,
                self.threshold,
                self.timeline,
                self.url,
                self.token,
                profile=self.profile,
            )
            logger.info(f"Job enqueued: {self.task_id}")

            self.checking_for_results = True
        except UnauthorizedError as e:
            raise ValidationError({"token": str(e)}, code="invalid") from e
        except InvalidURLError as e:
            raise ValidationError({"url": str(e)}, code="invalid") from e

    def enable_daily_emails(self):
        if self.email_address:
            try:
                validate_email(self.email_address)

                user = self.account.user
                user.email = self.email_address
                user.save()

                self.profile = self.account.profile
                self.profile.send_daily_digest = True
                self.profile.save()

                self.call("notify", "Subscribed to daily emails", "success")
            except Exception as e:
                logger.exception(e)
                self.call("notify", "Subscribing to daily emails failed", "error")
        else:
            self.call("notify", "Invalid email address", "error")

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
            "digest",
            "task_id",
            "task_started_at",
            "account",
        )
