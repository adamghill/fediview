import logging
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from mastodon import Mastodon
from mastodon.errors import (
    MastodonError,
    MastodonNetworkError,
    MastodonUnauthorizedError,
)

from digest.api import fetch_posts_and_boosts
from digest.models import Post
from digest.scorers import (
    ExtendedSimpleScorer,
    ExtendedSimpleWeightedScorer,
    Scorer,
    SimpleScorer,
    SimpleWeightedScorer,
)
from digest.thresholds import Threshold

logger = logging.getLogger(__name__)


class UnauthorizedError(Exception):
    pass


class InvalidURLError(Exception):
    pass


@dataclass
class Digest:
    ok: bool = False
    error: str = ""
    posts: list[Post] = field(default_factory=list)
    boosts: list[Post] = field(default_factory=list)
    rendered_at: datetime = None


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


def _clean_url(url: str) -> str:
    """Cleans the url to make sure it is usable as a base URL for the mastodon.py."""

    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"https://{url}"

    try:
        URLValidator(schemes=["http", "https"])(url)
    except ValidationError as e:
        raise InvalidURLError("Invalid URL") from e

    url = urlparse(url).hostname

    return url


def build_digest(
    hours: str,
    scorer_name: str,
    threshold_name: str,
    timeline: str,
    url: str,
    token: str,
) -> Digest:
    """Creates a digest of popular posts and boosts the user has not interacted with."""

    hours = int(hours)
    scorer = _get_scorer(scorer_name)
    threshold = Threshold[threshold_name.upper()]
    url = _clean_url(url)

    logger.debug(f"Building digest for the past {hours} hours")

    digest = Digest()

    # 1. Get a Mastodon API instance
    try:
        mastodon = Mastodon(
            access_token=token,
            api_base_url=url,
        )

        logger.debug("Mastodon API initialized")

        # 2. Fetch all the posts and boosts from our home timeline
        (posts, boosts) = fetch_posts_and_boosts(mastodon, timeline, hours)

        logger.debug("Posts and boosts fetched")

        digest.ok = True
    except MastodonUnauthorizedError as e:
        # `MastodonError` has multiple args so grab the last one
        raise UnauthorizedError(e.args[-1:][0]) from e
    except MastodonNetworkError as e:
        # `MastodonError` has multiple args so grab the last one
        raise InvalidURLError("Invalid URL") from e
    except MastodonError as e:
        # `MastodonError` has multiple args so grab the last one
        digest.error = e.args[-1:][0]
    except Exception as e:
        digest.error = str(e)

    if digest.ok is False:
        return digest

    # 3. Score them and return those that meet our threshold
    threshold_posts = threshold.posts_meeting_criteria(posts, scorer)
    threshold_boosts = threshold.posts_meeting_criteria(boosts, scorer)

    for post in threshold_posts + threshold_boosts:
        post.set_base_url(url)

    logger.debug("Posts and boosts scored")

    # 4. Get unique posts from unique accounts
    # unique_account_posts = []
    # sorted_posts = sorted(threshold_posts, key=lambda p: p.score, reverse=True)

    # users_hash: dict[int, Post] = {}

    # for post in sorted_posts:
    #     if post.account.id in users_hash:
    #         users_hash[post.account.id].account.add_additional_post(post)
    #     else:
    #         users_hash[post.account.id] = post

    # for post in users_hash.values():
    #     unique_account_posts.append(post)

    sorted_posts = sorted(threshold_posts, key=lambda p: p.score, reverse=True)
    sorted_boosts = sorted(threshold_boosts, key=lambda p: p.score, reverse=True)

    # 5. Build the digest
    digest.posts = sorted_posts
    digest.boosts = sorted_boosts
    digest.rendered_at = datetime.utcnow()

    return digest
