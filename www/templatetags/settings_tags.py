from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def analytics_html():
    return mark_safe(settings.ANALYTICS_HTML)
