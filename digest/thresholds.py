from enum import Enum

from scipy import stats

from digest.models import Post
from digest.scorers import Scorer


class Threshold(Enum):
    LAX = 90
    NORMAL = 95
    STRICT = 98

    def get_name(self):
        return self.name.lower()

    def posts_meeting_criteria(self, posts: list[Post], scorer: Scorer) -> list[Post]:
        """Returns a list of `Posts` that meet this `Threshold` with the given `Scorer`."""

        all_post_scores = [p.get_score(scorer) for p in posts]

        # TODO: use p.score here
        threshold_posts = [
            p
            for p in posts
            if stats.percentileofscore(all_post_scores, p.score) >= self.value
        ]

        return threshold_posts


def get_thresholds() -> dict:
    """Returns a dictionary mapping lowercase threshold names to values."""

    return {i.get_name(): i.value for i in Threshold}


def get_threshold_from_name(name: str) -> Threshold:
    """Returns `Threshold` for a given named string."""

    return Threshold[name.upper()]
