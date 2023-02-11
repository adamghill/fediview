from django import template

register = template.Library()


@register.filter
def username_to_url(username):
    username_splits = username.split("@")

    if len(username_splits) == 3:
        server = username_splits[2]
        username = username_splits[1]

        url = f"https://{server}/@{username}"

        return url


@register.filter
def username_no_server(username):
    username_splits = username.split("@")

    if len(username_splits) == 3:
        username = f"@{username_splits[1]}"

    return username
