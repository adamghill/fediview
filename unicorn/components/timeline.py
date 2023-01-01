from os import getenv

from django.forms import ValidationError
from django_unicorn.components import UnicornView

from digest.digester import Digest, InvalidURLError, UnauthorizedError, build_digest


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
            digest = build_digest(
                self.hours,
                self.scorer,
                self.threshold,
                self.timeline,
                self.url,
                self.token,
            )
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
