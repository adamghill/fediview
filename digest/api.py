from datetime import datetime, timedelta, timezone

from mastodon import Mastodon

from digest.models import Account, Post


def fetch_posts_and_boosts(
    mastodon: Mastodon,
    logged_in_account: Account,
    timeline: str,
    hours: int,
    limit: int = 1000,
) -> tuple[list[Post], list[Post]]:
    """Fetches posts from the home timeline that the account hasn't interacted with."""

    # First, get our filters
    filters = mastodon.filters()

    # Set our start query
    start = datetime.now(timezone.utc) - timedelta(hours=hours)

    posts = []
    boosts = []
    seen_post_urls = set()
    total_posts_seen = 0

    # If timeline name is specified as hashtag:tagName or list:list-name, look-up with
    # those names, else accept 'federated' and 'local' to process from the server public
    # and local timelines.
    #
    # Default to 'home' if the name is unrecognized.
    if ":" in timeline:
        (timeline_type, timeline_id) = timeline.lower().split(":", 1)
    else:
        timeline_type = timeline.lower()

    if timeline_type == "hashtag":
        response = mastodon.timeline_hashtag(timeline_id, min_id=start)
    elif timeline_type == "list":
        if not timeline_id.isnumeric():
            raise TypeError(
                "Cannot load list timeline: ID must be numeric, e.g. https://example.social/lists/4 would be list:4"
            )

        response = mastodon.timeline_list(timeline_id, min_id=start)
    elif timeline_type == "federated":
        response = mastodon.timeline_public(min_id=start)
    elif timeline_type == "local":
        response = mastodon.timeline_local(min_id=start)
    else:
        response = mastodon.timeline(min_id=start)

    # Iterate over our timeline until we run out of posts or we hit the limit
    while response and total_posts_seen < limit:
        # Apply our server-side filters
        if filters:
            filtered_posts = mastodon.filters_apply(response, filters, "home")
        else:
            filtered_posts = response

        for post in filtered_posts:
            total_posts_seen += 1
            is_boosted = False

            if post["reblog"] is not None:
                post = post["reblog"]  # look at the boosted post
                is_boosted = True

            post = Post(post)  # wrap the post data as a `Post`

            if post.url not in seen_post_urls:
                # Ignore logged-in user's posts or posts they've interacted with
                # Also ignore accounts that have explicitly said #nobot
                if (
                    not post.reblogged
                    and not post.favourited
                    and not post.bookmarked
                    and post.account.url != logged_in_account.url
                    and not post.account.is_nobot
                ):
                    # Append to either the boosts list or the posts lists
                    if is_boosted:
                        boosts.append(post)
                    else:
                        posts.append(post)

                    seen_post_urls.add(post.url)

        # fetch the previous (because of reverse chronological) page of results
        response = mastodon.fetch_previous(response)

    return (posts, boosts)
