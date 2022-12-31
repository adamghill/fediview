from fbv.decorators import render_html
from django.conf import settings


@render_html("www/index.html")
def index(request):
    return {"ANALYTICS_HTML": settings.ANALYTICS_HTML}
