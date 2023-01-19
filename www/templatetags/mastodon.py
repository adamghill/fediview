from django import template

register = template.Library()


@register.filter
def username_to_url(username):
    username_splits = username.split("@")
    server = username_splits[2]
    username = username_splits[1]

    url = f"https://{server}/@{username}"

    return url
