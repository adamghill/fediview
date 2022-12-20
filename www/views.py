from fbv.decorators import render_html


@render_html("www/index.html")
def index(request):
    return {}
