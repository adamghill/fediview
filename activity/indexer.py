import logging
from collections.abc import Iterator

from django.utils.html import strip_tags
from django.utils.timezone import now
from emoji import distinct_emoji_list
from mastodon import Mastodon
from mastodon.errors import MastodonAPIError

from account.models import Profile
from activity.models import Acct, Application, Post, Tag, TextEmoji
from activity.text_embeddings_retriever import save_posts_vectors
from digest.models import Post as DigestPost

logger = logging.getLogger(__name__)


def delete_posts(profile: Profile) -> None:
    Post.objects.all(acct__profile=profile).delete()


def _get_account_posts(mastodon: Mastodon, profile: Profile) -> Iterator[DigestPost]:
    if profile.indexing_type == profile.IndexingType.NONE:
        logger.debug(f"Profile id {profile.id}: Skip indexing posts")
        return

    logger.debug(f"Profile id {profile.id}: Login to mastodon")

    if not profile.account.account_id:
        profile.account.account_id = mastodon.me().get("id")
        profile.account.save()

    posts = []
    try:
        posts = mastodon.account_statuses(profile.account.account_id, min_id=profile.last_indexed_at, limit=1000)
    except Exception as e:
        logger.exception(e)

    logger.info(f"Profile id {profile.id}: Got {len(posts)} posts")

    while posts:
        for post in posts:
            yield DigestPost.parse_obj(post)

        try:
            posts = mastodon.fetch_next(posts)
        except Exception as e:
            posts = []
            logger.exception(e)

        if posts:
            logger.info(f"Profile id {profile.id}: Got {len(posts)} posts")


def _get_count(mastodon: Mastodon, status_type: str):
    status_function = None

    if status_type == "favourites":
        status_function = mastodon.favourites
    elif status_type == "bookmarks":
        status_function = mastodon.bookmarks
    else:
        raise Exception("Invalid status type")

    count = 0
    statuses = status_function(limit=1000)

    while statuses:
        count += len(statuses)

        statuses = mastodon.fetch_next(statuses)

    return count


def index_posts(profile: Profile) -> None:
    try:
        if profile.indexing_type == profile.IndexingType.NONE.value:
            logger.info(f"Profile id {profile.id}: Skip indexing posts with {profile.indexing_type} indexing type")
            return

        if not profile.has_plus:
            logger.error(f"Profile id {profile.id}: Skip indexing posts for non-plus profile")
            return

        if profile.last_index_error:
            logger.error(f"Profile id {profile.id}: Skip indexing posts because unauthorized")
            return

        logger.info(f"Profile id {profile.id}: Get posts")

        mastodon = Mastodon(
            access_token=profile.account.access_token,
            api_base_url=profile.account.instance.api_base_url,
            user_agent="fediview",
        )

        try:
            profile.account.favorites_count = _get_count(mastodon, "favourites")
            profile.account.bookmarks_count = _get_count(mastodon, "bookmarks")

            account_dict = mastodon.me()
            profile.account.followers_count = account_dict.get("followers_count")
            profile.account.following_count = account_dict.get("following_count")
            profile.account.save()
        except mastodon.errors.MastodonUnauthorizedError as e:
            profile.account.last_index_error = str(e)
            profile.account.save()

            return

        posts = _get_account_posts(mastodon, profile)
        post_count = 0

        for digest_post in posts:
            acct = Acct.get_or_create(digest_post.account, profile)

            if not digest_post.content:
                # Skip anything without content, e.g. `Announce` statuses
                continue

            if digest_post.visibility not in (
                "public",
                "unlisted",
            ):
                # Skip storing direct messages
                continue

            text_content = strip_tags(digest_post.content)

            post_data = {
                "url": digest_post.url,
                "created_at": digest_post.created_at,
                "reply_id": digest_post.reply_id,
                "is_poll": digest_post.is_poll,
                "visibility": digest_post.visibility or None,
                "replies_count": digest_post.replies_count,
                "reblogs_count": digest_post.reblogs_count,
                "favourites_count": digest_post.favourites_count,
                "edited_at": digest_post.edited_at,
                "is_favourited": digest_post.favourited,
                "is_reblogged": digest_post.reblogged,
                "is_muted": digest_post.muted,
                "is_bookmarked": digest_post.bookmarked,
                "is_pinned": digest_post.pinned,
                "language": digest_post.language,
            }

            if profile.indexing_type == profile.IndexingType.CONTENT:
                post_data.update(
                    {
                        "content": digest_post.content,
                        "text_content": text_content,
                    }
                )

            post = Post.objects.filter(post_id=digest_post.id, acct__acct_id=digest_post.account.id).first()

            if post:
                logger.debug(f"Profile id {profile.id}: Update post {digest_post.id}")

                Post.objects.filter(post_id=digest_post.id, acct__acct_id=digest_post.account.id).update(**post_data)

                post.content = post_data.get("content")
                post.text_content = post_data.get("text_content")
            else:
                logger.debug(f"Profile id {profile.id}: Create post {digest_post.id}")

                post_data.update(
                    {
                        "acct": acct,
                        "post_id": digest_post.id,
                    }
                )
                post = Post(**post_data)
                post.save()

            # Remove all mentions every time to make sure it is as accurate as possible
            post.mentions.all().delete()

            for digest_account in digest_post.mentions:
                acct = Acct.get_or_create(digest_account, profile)

                post.mentions.add(acct)

            # Remove all tags every time to make sure it is as accurate as possible
            post.tags.all().delete()

            for digest_tag in digest_post.tags:
                tag = Tag.objects.filter(name=digest_tag.name).first()

                if not tag:
                    tag = Tag(name=digest_tag.name)
                    tag.save()

                post.tags.add(tag)

            if digest_post.application:
                application = Application.objects.filter(
                    name=digest_post.application.name,
                    website=digest_post.application.website,
                ).first()

                if not application:
                    application = Application(
                        name=digest_post.application.name,
                        website=digest_post.application.website,
                    )
                    application.save()

                post.application = application
                post.save()

            # Remove all emojis every time to make sure it is as accurate as possible
            post.text_emojis.all().delete()

            emojis = distinct_emoji_list(text_content)

            for emoji in emojis:
                text_emoji = TextEmoji.objects.filter(text=emoji).first()

                if not text_emoji:
                    text_emoji = TextEmoji(text=emoji)
                    text_emoji.save()

                post.text_emojis.add(text_emoji)

            post_count += 1

        profile.last_indexed_at = now()
        profile.save()

        logger.info(f"Profile id {profile.id}: Indexed {post_count} posts")

        if post_count > 0:
            logger.info(f"Profile id {profile.id}: Save post vectors")
            save_posts_vectors(profile)
            logger.info(f"Profile id {profile.id}: Post vectors saved")
    except MastodonAPIError as e:
        if "Your login is currently disabled" in str(e):
            logger.info("Setting profile to not get indexed in the future")
            profile.indexing_type = Profile.IndexingType.NONE
            profile.last_index_error = str(e)

            profile.save()
        else:
            raise
