import logging
from dataclasses import dataclass, field
from datetime import datetime

from mastodon import Mastodon
from mastodon.errors import MastodonError

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


@dataclass
class Digest:
    ok: bool = False
    error: str = ""
    posts: list[Post] = field(default_factory=list)
    boosts: list[Post] = field(default_factory=list)
    rendered_at: datetime = None


class ProfileParseError(Exception):
    pass


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


def _parse_profile(profile: str) -> tuple[str, str]:
    """Parse the profile into base url and username."""

    base_url = ""
    username = ""
    profile = profile.strip()

    if profile.startswith("@") and len(profile.split("@")) == 3:
        # Handle @username@mastodon.social
        (
            _,
            username,
            base_url,
        ) = profile.split("@")

        username = f"@{username}"
        base_url = f"https://{base_url}"
    elif profile.startswith("https://") and len(profile.split("/@")) == 2:
        # Handle https://mastodon.social/@username
        (
            base_url,
            username,
        ) = profile.split("/@")

        if username and not username.startswith("@"):
            username = f"@{username}"
    else:
        raise ProfileParseError("Profile could not be parsed")

    if not base_url.startswith("https://"):
        raise ProfileParseError("URL must start with https://")

    if "." not in base_url:
        raise ProfileParseError("URL is invalid")

    return (base_url, username)


def build_digest(
    hours: str,
    scorer_name: str,
    threshold_name: str,
    timeline: str,
    profile: str,
    token: str,
) -> Digest:
    """Creates a digest of popular posts and boosts the user has not interacted with."""

    (base_url, username) = _parse_profile(profile)

    hours = int(hours)
    scorer = _get_scorer(scorer_name)
    threshold = Threshold[threshold_name.upper()]

    logger.debug(f"Building digest from the past {hours} hours for {username}")

    digest = Digest()

    # 1. Get a Mastodon API instance
    try:
        mastodon = Mastodon(
            access_token=token,
            api_base_url=base_url,
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
    (posts, boosts) = fetch_posts_and_boosts(hours, mastodon, username, timeline)

    logger.debug("Posts and boosts fetched")

    # 3. Score them and return those that meet our threshold
    threshold_posts = threshold.posts_meeting_criteria(posts, scorer)
    threshold_boosts = threshold.posts_meeting_criteria(boosts, scorer)

    for post in threshold_posts + threshold_boosts:
        post.set_base_url(base_url)

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
