from os import getenv
from pathlib import Path

from django.forms import ValidationError
from django_unicorn.components import UnicornView
from mastodon.errors import MastodonError

from mastodon_digest import run as mastodon_digest_run
from mastodon_digest.formatters import format_posts
from mastodon_digest.run import run, sys
from mastodon_digest.scorers import (
    ExtendedSimpleScorer,
    ExtendedSimpleWeightedScorer,
    SimpleScorer,
    SimpleWeightedScorer,
)
from mastodon_digest.thresholds import Threshold


class Digester:
    """
    Wraps `mastodon_digest.run`.
    """

    def __init__(
        self,
        timeline: str,
        scorer: str,
        threshold: str,
        hours: str,
        mastodon_base_url: str,
        mastodon_username: str,
        mastodon_token: str,
    ):
        self.scorer = self._get_scorer(scorer)
        self.threshold = Threshold[threshold.upper()]
        self.hours = hours
        self.timeline = timeline
        self.mastodon_base_url = mastodon_base_url
        self.mastodon_username = mastodon_username
        self.mastodon_token = mastodon_token
        self.error = ""

    def _get_scorer(self, scorer_name):
        if scorer_name == "Simple":
            return SimpleScorer
        elif scorer_name == "SimpleWeighted":
            return SimpleWeightedScorer
        elif scorer_name == "ExtendedSimple":
            return ExtendedSimpleScorer
        elif scorer_name == "ExtendedSimpleWeighted":
            return ExtendedSimpleWeightedScorer

        raise Exception("Unknown scorer")

    def make_digest(self) -> dict:
        global exit_message
        exit_message = ""

        global digest_context
        digest_context = {}

        def _sys_exit(s):
            # print(s)

            global exit_message
            exit_message = s

        setattr(sys, "exit", _sys_exit)

        def _render_digest(context: dict, output_dir: Path) -> None:
            global digest_context
            digest_context = context

        setattr(mastodon_digest_run, "render_digest", _render_digest)

        try:
            run(
                hours=int(self.hours),
                scorer=self.scorer,
                threshold=self.threshold,
                mastodon_token=self.mastodon_token,
                mastodon_base_url=self.mastodon_base_url,
                mastodon_username=self.mastodon_username,
                timeline=self.timeline,
                output_dir=None,
            )

            self.error = exit_message
            digest_context["ok"] = True
        except MastodonError as e:
            digest_context["ok"] = False
            self.error = e.args[-1:][0]
        except Exception as e:
            digest_context["ok"] = False
            self.error = str(e)

        digest_context["error"] = self.error

        return digest_context


class TimelineView(UnicornView):
    hours: str = "2"
    scorer: str = "Simple"
    threshold: str = "normal"
    timeline: str = "home"  # TODO: Support hashtag:tagName, list:list-name
    mastodon_base_url: str = ""
    mastodon_username: str = ""
    mastodon_token: str = ""
    error: str = ""

    # digester: Digester = None
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

        digester = Digester(
            self.timeline,
            self.scorer,
            self.threshold,
            self.hours,
            self.mastodon_base_url,
            self.mastodon_username,
            self.mastodon_token,
        )

        digest = digester.make_digest()
        self.error = digest.get("error", "")

        if self.error.startswith("Version check failed"):
            self.error = f"URL might be invalid: {self.error}"

        if digest.get("ok", False) is True:
            scored_posts = digest.get("posts", [])
            self.posts = format_posts(scored_posts, self.mastodon_base_url)

            scored_boosts = digest.get("boosts", [])
            self.boosts = format_posts(scored_boosts, self.mastodon_base_url)

            self.has_results = True

    class Meta:
        javascript_exclude = (
            "mastodon_base_url",
            "mastodon_token",
            "mastodon_username",
            "error",
        )
