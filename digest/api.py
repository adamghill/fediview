import logging
from datetime import datetime
from typing import Optional

from mastodon import Mastodon

from account.models import Profile
from digest.models import Account, Post

logger = logging.getLogger(__name__)


def get_timeline_posts(
    mastodon: Mastodon, timeline: str, start: datetime, end: Optional[datetime] = None
) -> list[dict]:
    """Get responses from Mastodon for the timeline.

    If timeline name is specified as hashtag:tagName or list:list-name, look-up with
    those names, else accept 'federated' and 'local' to process from the server public
    and local timelines.

    Defaults to the 'home' timeline.
    """

    # Set our start query
    # start = datetime.now(timezone.utc) - timedelta(hours=hours)

    timeline = timeline.lower()

    if ":" in timeline:
        (timeline, timeline_id) = timeline.lower().split(":", 1)

        if timeline == "hashtag":
            return mastodon.timeline_hashtag(timeline_id, min_id=start)
        elif timeline == "list":
            if not timeline_id.isnumeric():
                raise TypeError(
                    "Cannot load list timeline: ID must be numeric, e.g. https://example.social/lists/4 would be list:4"
                )

            return mastodon.timeline_list(timeline_id, min_id=start)

    if timeline == "federated":
        return mastodon.timeline_public(min_id=start)
    elif timeline == "local":
        return mastodon.timeline_local(min_id=start)

    # Default to the home timeline
    return mastodon.timeline(min_id=start)


def fetch_posts_and_boosts(
    mastodon: Mastodon,
    logged_in_account: Account,
    timeline: str,
    start: datetime,
    end: Optional[datetime] = None,
    limit: int = 1000,
    profile: Profile = None,
) -> tuple[list[Post], list[Post]]:
    """Fetches posts from the home timeline that the account hasn't interacted with."""

    # First, get our filters
    filters = mastodon.filters()

    posts = []
    boosts = []
    seen_post_urls = set()
    total_posts_seen = 0

    timeline_posts = get_timeline_posts(mastodon, timeline, start=start, end=end)

    # Iterate over our timeline until we run out of posts or we hit the limit
    while timeline_posts and total_posts_seen < limit:
        # Apply our server-side filters
        if filters:
            # TODO: Use public context for federated timeline?
            filtered_posts = mastodon.filters_apply(timeline_posts, filters, "home")
        else:
            filtered_posts = timeline_posts

        for post_data in filtered_posts:
            total_posts_seen += 1
            is_boosted = False

            if post_data["reblog"] is not None:
                post_data = post_data["reblog"]  # use the reblog data
                is_boosted = True

            # Convert the data into a `Post` model
            try:
                post = Post.parse_obj(post_data)
            except Exception as e:
                logger.exception(e)
                continue

            if post.url not in seen_post_urls:
                # Ignore logged-in user's posts or posts they've interacted with
                # or muted. Ignore accounts that have explicitly said #nobot
                if (
                    not post.reblogged
                    and not post.favourited
                    and not post.bookmarked
                    and post.account.url != logged_in_account.url
                    and not post.account.is_nobot
                    and not post.muted
                ):
                    if (
                        profile
                        and profile.has_plus
                        and profile.language
                        and post.language
                        and profile.language != post.language
                    ):
                        continue

                    # Append to either the boosts list or the posts lists
                    if is_boosted:
                        boosts.append(post)
                    else:
                        posts.append(post)

                    seen_post_urls.add(post.url)

        # Fetch the previous (because of reverse chronological) page of results
        timeline_posts = mastodon.fetch_previous(timeline_posts)

    return (posts, boosts)
