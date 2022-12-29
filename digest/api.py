from datetime import datetime, timedelta, timezone

from mastodon import Mastodon

from digest.models import Post


def fetch_posts_and_boosts(
    hours: int,
    mastodon_client: Mastodon,
    mastodon_username: str,
    timeline: str,
    limit: int = 1000,
) -> tuple[list[Post], list[Post]]:
    """Fetches posts from the home timeline that the account hasn't interacted with."""

    # First, get our filters
    filters = mastodon_client.filters()

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
        timelineType, timelineId = timeline.lower().split(":", 1)
    else:
        timelineType = timeline.lower()

    if timelineType == "hashtag":
        response = mastodon_client.timeline_hashtag(timelineId, min_id=start)
    elif timelineType == "list":
        if not timelineId.isnumeric():
            raise TypeError(
                "Cannot load list timeline: ID must be numeric, e.g. https://example.social/lists/4 would be list:4"
            )

        response = mastodon_client.timeline_list(timelineId, min_id=start)
    elif timelineType == "federated":
        response = mastodon_client.timeline_public(min_id=start)
    elif timelineType == "local":
        response = mastodon_client.timeline_local(min_id=start)
    else:
        response = mastodon_client.timeline(min_id=start)

    # Iterate over our timeline until we run out of posts or we hit the limit
    while response and total_posts_seen < limit:
        # Apply our server-side filters
        if filters:
            filtered_posts = mastodon_client.filters_apply(response, filters, "home")
        else:
            filtered_posts = response

        for post in filtered_posts:
            total_posts_seen += 1
            is_boosted = False

            if post["reblog"] is not None:
                post = post["reblog"]  # look at the boosted post
                is_boosted = True

            post = Post(post)  # wrap the post data as a Post

            if post.url not in seen_post_urls:
                # Apply our local filters
                # Basically ignore my posts or posts I've interacted with
                if (
                    not post.reblogged
                    and not post.favourited
                    and not post.bookmarked
                    and post.account.acct.strip().lower()
                    != mastodon_username.strip().lower()
                ):
                    # Append to either the boosts list or the posts lists
                    if is_boosted:
                        boosts.append(post)
                    else:
                        posts.append(post)

                    seen_post_urls.add(post.url)

        # fetch the previous (because of reverse chronological) page of results
        response = mastodon_client.fetch_previous(response)

    return (posts, boosts)
