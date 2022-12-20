from pathlib import Path

from django_unicorn.components import UnicornView

from mastodon_digest import run as mastodon_digest_run
from mastodon_digest.models import ScoredPost
from mastodon_digest.run import run, sys
from mastodon_digest.scorers import (
    ExtendedSimpleScorer,
    ExtendedSimpleWeightedScorer,
    SimpleScorer,
    SimpleWeightedScorer,
)
from mastodon_digest.thresholds import Threshold


class TimelineView(UnicornView):
    hours: int = 6
    scorer: str = "SimpleWeighted"
    threshold: str = "normal"
    timeline: str = "home"  # TODO: Support hashtag:tagName, list:list-name
    mastodon_base_url: str = ""
    mastodon_username: str = ""
    mastodon_token: str = ""
    message: str = ""

    has_results: bool = False
    posts: list[dict] = []
    boosts: list[dict] = []

    def _convert_scored_post_to_dict(self, scored_post: ScoredPost) -> dict:
        scorer = self._get_scorer()

        return {
            "url": scored_post.url,
            "home_url": scored_post.get_home_url(self.mastodon_base_url),
            "score": float(scored_post.get_score(scorer)),
        }

    def _get_scorer(self):
        if self.scorer == "Simple":
            return SimpleScorer
        elif self.scorer == "SimpleWeighted":
            return SimpleWeightedScorer
        elif self.scorer == "ExtendedSimple":
            return ExtendedSimpleScorer
        elif self.scorer == "ExtendedSimpleWeighted":
            return ExtendedSimpleWeightedScorer

        raise Exception("Unknown scorer")

    def get_results(self):
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
                scorer=self._get_scorer(),
                threshold=Threshold[self.threshold.upper()],
                mastodon_token=self.mastodon_token,
                mastodon_base_url=self.mastodon_base_url,
                mastodon_username=self.mastodon_username,
                timeline=self.timeline,
                output_dir=None,
            )

            self.message = exit_message
        except Exception as e:
            self.message = str(e)

        # print("unicorn digest_context", digest_context)

        scored_posts = digest_context.get("posts", [])
        self.posts = [self._convert_scored_post_to_dict(p) for p in scored_posts]

        scored_boosts = digest_context.get("boosts", [])
        self.boosts = [self._convert_scored_post_to_dict(p) for p in scored_boosts]

        self.rendered_at = digest_context.get("rendered_at")

        self.has_results = True

    class Meta:
        javascript_exclude = (
            "mastodon_base_url",
            "mastodon_token",
            "mastodon_username",
        )
