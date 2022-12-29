from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def git_version():
    sha = settings.GIT_VERSION

    if sha:
        return sha[:8]
