# From https://github.com/mauforonda/mastodon_digest/blob/main/formatters.py


def format_post(post, mastodon_base_url) -> dict:
    def format_media(media):
        formats = {
            "image": f'<div class="media"><img src={media["url"]} alt={media["description"] if media["description"] != None else ""}></img></div>',
            "video": f'<div class="media"><video src={media["url"]} controls width="100%"></video></div>',
            "gifv": f'<div class="media"><video src={media["url"]} autoplay loop muted playsinline width="100%"></video></div>',
        }
        if formats.__contains__(media.type):
            return formats[media.type]
        else:
            return ""

    def format_displayname(display_name, emojis):
        for emoji in emojis:
            display_name = display_name.replace(
                f':{emoji["shortcode"]}:',
                f'<img alt={emoji["shortcode"]} src="{emoji["url"]}">',
            )
        return display_name

    account_avatar = post.data["account"]["avatar"]
    account_url = post.data["account"]["url"]
    display_name = format_displayname(
        post.data["account"]["display_name"], post.data["account"]["emojis"]
    )
    username = post.data["account"]["username"]
    content = post.data["content"]
    media = "\n".join([format_media(media) for media in post.data.media_attachments])
    created_at = post.data["created_at"].strftime("%B %d, %Y at %H:%M")
    home_link = (
        f'<a href="{post.get_home_url(mastodon_base_url)}" target="_blank">🔗</a>'
    )
    original_link = f'<a href="{post.data.url}" target="_blank">original</a>'
    replies_count = post.data["replies_count"]
    reblogs_count = post.data["reblogs_count"]
    favourites_count = post.data["favourites_count"]

    return dict(
        account_avatar=account_avatar,
        account_url=account_url,
        display_name=display_name,
        username=username,
        content=content,
        media=media,
        created_at=created_at,
        home_link=home_link,
        original_link=original_link,
        replies_count=replies_count,
        reblogs_count=reblogs_count,
        favourites_count=favourites_count,
    )


def format_posts(posts, mastodon_base_url):
    return [format_post(post, mastodon_base_url) for post in posts]
