from django.urls import include, path
from fbv.views import favicon_emoji, favicon_file
from coltrane.sitemaps import ContentSitemap
from django.contrib.sitemaps.views import sitemap

from www import urls as www_urls

ContentSitemap.protocol = "https"

sitemaps = {
    "content": ContentSitemap,
}

urlpatterns = [
    path("unicorn/", include("django_unicorn.urls")),
    path("favicon.ico", favicon_emoji, {"emoji": "🐘"}),
    path(r"apple-touch-icon.png", favicon_emoji, {"emoji": "🐘"}),
    path(r"apple-touch-icon-precomposed.png", favicon_emoji, {"emoji": "🐘"}),
    path("robots.txt", favicon_file, {"file_path": "www/robots.txt"}),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("", include(www_urls)),
    path("", include("coltrane.urls")),
]
