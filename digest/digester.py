import logging
from dataclasses import dataclass, field
from datetime import datetime

from mastodon import Mastodon
from mastodon.errors import MastodonError

from digest.api import fetch_posts_and_boosts
from digest.formatters import FormattedPost, format_posts
from digest.scorers import (
    ExtendedSimpleScorer,
    ExtendedSimpleWeightedScorer,
    Scorer,
    SimpleScorer,
    SimpleWeightedScorer,
)
from digest.thresholds import Threshold

logger = logging.getLogger(__name__)


@dataclass
class Digest:
    ok: bool = False
    error: str = ""
    posts: list[FormattedPost] = field(default_factory=list)
    boosts: list[FormattedPost] = field(default_factory=list)
    rendered_at: datetime = None


def _format_base_url(mastodon_base_url: str) -> str:
    """Format base url."""

    return mastodon_base_url.strip().rstrip("/")


def _get_scorer(scorer_name: str) -> Scorer:
    """Converts the name of a scorer into a class."""

    if scorer_name == "Simple":
        return SimpleScorer
    elif scorer_name == "SimpleWeighted":
        return SimpleWeightedScorer
    elif scorer_name == "ExtendedSimple":
        return ExtendedSimpleScorer
    elif scorer_name == "ExtendedSimpleWeighted":
        return ExtendedSimpleWeightedScorer

    raise Exception("Unknown scorer")


def build_digest(
    hours: str,
    scorer_name: str,
    threshold_name: str,
    mastodon_token: str,
    mastodon_base_url: str,
    mastodon_username: str,
    timeline: str,
) -> dict:
    """Creates a digest of popular posts and boosts the user has not interacted with."""

    hours = int(hours)
    scorer = _get_scorer(scorer_name)
    threshold = Threshold[threshold_name.upper()]
    mastodon_base_url = _format_base_url(mastodon_base_url)

    logger.debug(f"Building digest from the past {hours} hours for {mastodon_username}")

    digest = Digest()

    # 1. Get a Mastodon API instance
    try:
        mastodon = Mastodon(
            access_token=mastodon_token,
            api_base_url=mastodon_base_url,
        )

        digest.ok = True
    except MastodonError as e:
        # MastodonError has multiple args so grab the last one
        digest.error = e.args[-1:][0]
    except Exception as e:
        digest.error = str(e)

    if digest.ok is False:
        return digest

    logger.debug("Mastodon API initialized")

    # 2. Fetch all the posts and boosts from our home timeline
    (posts, boosts) = fetch_posts_and_boosts(
        hours, mastodon, mastodon_username, timeline
    )

    logger.debug("Posts and boosts fetched")

    # 3. Score them and return those that meet our threshold
    threshold_posts = threshold.posts_meeting_criteria(posts, scorer)
    threshold_boosts = threshold.posts_meeting_criteria(boosts, scorer)

    logger.debug("Posts and boosts scored")

    # 4. Format posts and boosts
    formatted_posts = format_posts(threshold_posts, mastodon_base_url)
    formatted_boosts = format_posts(threshold_boosts, mastodon_base_url)

    logger.debug("Posts and boosts formatted")

    # 5. Build the digest
    digest.posts = formatted_posts
    digest.boosts = formatted_boosts
    digest.rendered_at = datetime.utcnow()

    return digest
