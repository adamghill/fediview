from os import getenv

from django.forms import ValidationError
from django_unicorn.components import UnicornView

from digest.digester import build_digest


class TimelineView(UnicornView):
    hours: str = "2"
    scorer: str = "Simple"
    threshold: str = "normal"
    timeline: str = "home"  # TODO: Support hashtag:tagName, list:list-name
    mastodon_base_url: str = ""
    mastodon_username: str = ""
    mastodon_token: str = ""
    error: str = ""

    has_results: bool = False
    posts: list[dict] = []
    boosts: list[dict] = []

    def mount(self):
        self.mastodon_base_url = getenv("MASTODON_BASE_URL", "")
        self.mastodon_username = getenv("MASTODON_USERNAME", "")
        self.mastodon_token = getenv("MASTODON_TOKEN", "")

    def clean(self) -> None:
        validation_errors = {}

        if not self.mastodon_username:
            validation_errors["mastodon_username"] = "Missing username"
        elif not self.mastodon_username.startswith("@"):
            validation_errors["mastodon_username"] = "Username must start with @"

        if not self.mastodon_base_url:
            validation_errors["mastodon_base_url"] = "Missing base URL"
        elif not self.mastodon_base_url.startswith("https://"):
            validation_errors["mastodon_base_url"] = "URL must start with https://"

        if not self.mastodon_token:
            validation_errors["mastodon_token"] = "Missing token"

        if validation_errors:
            raise ValidationError(validation_errors, code="invalid")

    def get_results(self):
        self.errors = {}
        self.clean()

        digest = build_digest(
            self.hours,
            self.scorer,
            self.threshold,
            self.mastodon_token,
            self.mastodon_base_url,
            self.mastodon_username,
            self.timeline,
        )

        self.error = digest.error

        if self.error.startswith("Version check failed"):
            self.error = f"URL might be invalid: {self.error}"

        self.posts = digest.posts
        self.boosts = digest.boosts
        self.has_results = digest.ok is True

    class Meta:
        javascript_exclude = (
            "mastodon_base_url",
            "mastodon_token",
            "mastodon_username",
            "error",
        )
