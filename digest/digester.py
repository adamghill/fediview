import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from random import shuffle
from typing import Optional
from urllib.parse import urlparse

from dateutil.parser import parse
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.html import strip_tags
from mastodon import Mastodon
from mastodon.errors import (
    MastodonError,
    MastodonNetworkError,
    MastodonUnauthorizedError,
)

from account.models import Profile
from activity.models import PostVectors
from activity.text_embeddings_retriever import cosine_similarity, get_text_embeddings
from digest.api import fetch_posts_and_boosts
from digest.models import Account, Card, Post
from digest.scorers import get_scorer_from_name
from digest.thresholds import get_threshold_from_name

logger = logging.getLogger(__name__)


class UnauthorizedError(Exception):
    pass


class InvalidURLError(Exception):
    pass


@dataclass
class Link:
    url: str
    posts: list[Post] = field(default_factory=list)

    @property
    def card(self) -> Optional[Card]:
        for post in self.posts:
            if post.card and post.card.url in self.url:
                return post.card

    @property
    def title(self) -> str:
        _card = self.card

        if _card and _card.title:
            return _card.title

        return self.url

    @property
    def count(self) -> int:
        return len(self.posts)

    @property
    def most_recent_post(self) -> Post:
        assert self.posts, "There should always be at least one post"
        return sorted(self.posts, key=lambda p: p.created_at, reverse=True)[0]

    @property
    def most_recent_created_at(self) -> datetime:
        if isinstance(self.most_recent_post.created_at, str):
            return parse(self.most_recent_post.created_at)

        return self.most_recent_post.created_at


@dataclass
class Digest:
    """Includes all the digest information."""

    ok: bool = False
    error: str = ""
    posts: list[Post] = field(default_factory=list)
    boosts: list[Post] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    rendered_at: datetime = None


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


def _add_following_to_account(mastodon, account) -> None:
    """Add accounts that the specified account is following to `Account`."""

    response = mastodon.account_following(account.id, limit=80)

    # This could take a long time if the account is following a lot of accounts
    following_accounts = mastodon.fetch_remaining(response)

    account.add_follows(following_accounts)


def _catalog_links(posts: list[Post]) -> list[Link]:
    """Build a list of links that were included posts."""

    links: list[Link] = []
    all_post_ids = set()
    link_regex = r'(?<=<a href=")([^\"]*)(?=" rel="nofollow noopener noreferrer")'

    for post in posts:
        for url in re.findall(link_regex, post.content):
            link = next(filter(lambda l: l.url == url, links), None)

            if post.id not in all_post_ids:
                all_post_ids.add(post.id)

                if link:
                    link.posts.append(post)
                else:
                    links.append(Link(url, [post]))

    return links


def build_digest(
    start: datetime,
    end: Optional[datetime],
    scorer_name: str,
    threshold_name: str,
    timeline: str,
    url: str,
    token: str,
    profile: Profile = None,
    skip_recommendations: bool = False,
) -> Digest:
    """Creates a digest of popular posts and boosts the user has not interacted with."""

    scorer = get_scorer_from_name(scorer_name)
    threshold = get_threshold_from_name(threshold_name)
    assert timeline in ("home", "local", "federated"), "Invalid timeline"
    url = _clean_url(url)

    logger.info(f"Building digest for {start} to {end}")

    digest = Digest()

    # Get a Mastodon API instance
    try:
        mastodon = Mastodon(access_token=token, api_base_url=url, user_agent="fediview")

        logger.debug("Mastodon API initialized")

        logged_in_account = Account.parse_obj(mastodon.me())
        _add_following_to_account(mastodon, logged_in_account)

        logger.debug("User followings retrieved")

        # Fetch all the posts and boosts from the timeline
        (posts, boosts) = fetch_posts_and_boosts(
            mastodon,
            logged_in_account,
            timeline,
            start,
            end=end,
            profile=profile,
        )

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

    # Score posts and return those that meet our threshold
    threshold_posts = threshold.posts_meeting_criteria(posts, scorer)
    logger.info(f"Threshold posts count: {len(threshold_posts)}")

    threshold_boosts = threshold.posts_meeting_criteria(boosts, scorer)
    logger.info(f"Threshold boosts count: {len(threshold_boosts)}")

    # Get recommended posts
    recommended_posts = []

    if (
        profile
        and profile.posts_vectors is not None
        and not skip_recommendations
        and profile.generate_recommendations
    ):
        similarity_threshold = 0.8

        # Lower the similarity threshold if there aren't many threshold posts
        # TODO: Allow this to be configurable by user
        if len(threshold_posts) < 3:
            similarity_threshold = 0.6

        threshold_post_ids = set([p.id for p in threshold_posts])
        remaining_posts = [p for p in posts if p.id not in threshold_post_ids]
        logger.debug(f"Remaining posts count: {len(remaining_posts)}")

        # Shuffle the posts and only grab 50 of them
        shuffle(remaining_posts)
        remaining_posts = remaining_posts[0:50]

        for post in remaining_posts:
            try:
                post_vectors = PostVectors.objects.filter(post_id=str(post.id)).first()
                vectors = None

                if post_vectors:
                    logger.debug(f"Use existing vectors for {post.id}")
                    vectors = post_vectors.vectors
                else:
                    logger.debug(f"Get text embeddings for {post.id}")
                    post_content = strip_tags(post.content)
                    vectors = get_text_embeddings(post_content)

                    PostVectors(post_id=str(post.id), vectors=vectors).save()

                logger.debug(f"Get similarity for {post.id}")
                similarity = cosine_similarity(profile.posts_vectors, vectors)

                post.is_recommendation = similarity > similarity_threshold
            except Exception as e:
                logger.exception(e)

        recommended_posts = [p for p in remaining_posts if p.is_recommendation]

    logger.debug(f"Recommended posts count: {len(recommended_posts)}")

    # Update metadata
    for post in threshold_posts + threshold_boosts + recommended_posts:
        post.set_base_url(mastodon.api_base_url)

        if post.account.is_following is None:
            post.account.set_is_following(logged_in_account)

    logger.debug("Post metadata is updated")

    """
    # Get unique posts from unique accounts
    unique_account_posts = []
    sorted_posts = sorted(threshold_posts, key=lambda p: p.score, reverse=True)

    users_hash: dict[int, Post] = {}

    for post in sorted_posts:
        if post.account.id in users_hash:
            users_hash[post.account.id].account.add_additional_post(post)
        else:
            users_hash[post.account.id] = post

    for post in users_hash.values():
        unique_account_posts.append(post)
    """

    # Sort posts and boosts
    sorted_posts = sorted(
        threshold_posts + recommended_posts, key=lambda p: p.created_at, reverse=True
    )
    sorted_boosts = sorted(threshold_boosts, key=lambda p: p.created_at, reverse=True)

    logger.debug("Posts and boosts sorted")

    # Build catalog of links
    links = _catalog_links(posts + boosts)
    sorted_links = sorted(links, key=lambda l: l.count, reverse=True)
    sorted_links = sorted(links, key=lambda l: l.most_recent_created_at, reverse=True)

    # Set metadata for posts in links
    for link in sorted_links:
        for p in link.posts:
            p.set_base_url(mastodon.api_base_url)

    logger.debug("Links built and sorted")

    # Build the digest
    digest.posts = sorted_posts
    digest.boosts = sorted_boosts
    digest.links = sorted_links
    digest.rendered_at = datetime.utcnow()

    return digest
