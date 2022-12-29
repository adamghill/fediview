from os import getenv

from django.forms import ValidationError
from django_unicorn.components import UnicornView

from digest.digester import Digest, ProfileParseError, build_digest


class TimelineView(UnicornView):
    hours: str = "2"
    scorer: str = "Simple"
    threshold: str = "normal"
    timeline: str = "home"  # TODO: Support hashtag:tagName, list:list-name
    mastodon_profile: str = ""
    mastodon_token: str = ""
    error: str = ""

    has_results: bool = False
    posts: list[dict] = []
    boosts: list[dict] = []

    def mount(self):
        self.mastodon_profile = getenv("MASTODON_PROFILE", "")
        self.mastodon_token = getenv("MASTODON_TOKEN", "")

    def clean(self) -> None:
        validation_errors = {}

        if not self.mastodon_profile:
            validation_errors["mastodon_profile"] = "Missing profile"

        if not self.mastodon_token:
            validation_errors["mastodon_token"] = "Missing token"

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
                self.mastodon_profile,
                self.mastodon_token,
            )
        except ProfileParseError as e:
            raise ValidationError({"mastodon_profile": str(e)}, code="invalid")

        self.error = digest.error

        if self.error.startswith("Version check failed"):
            self.error = f"URL might be invalid: {self.error}"

        self.posts = digest.posts
        self.boosts = digest.boosts
        self.has_results = digest.ok is True

    class Meta:
        javascript_exclude = (
            "mastodon_token",
            "mastodon_profile",
            "posts",
            "boosts",
            "has_results",
            "error",
        )
