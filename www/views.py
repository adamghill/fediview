from django.conf import settings
from fbv.decorators import render_html


@render_html("www/index.html")
def index(request):
    return {}


@render_html("www/plus.html")
def plus(request):
    return {}
