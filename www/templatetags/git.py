from django.conf import settings
from django import template

register = template.Library()


@register.simple_tag
def git_version():
    sha = settings.GIT_VERSION

    if sha:
        return sha[:8]
