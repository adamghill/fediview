from django.conf import settings
from fbv.decorators import render_html


@render_html("www/index.html")
def index(request):
    return {"ANALYTICS_HTML": settings.ANALYTICS_HTML}
