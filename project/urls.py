from coltrane.sitemaps import ContentSitemap
from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from fbv.views import favicon_emoji, favicon_file

from account import urls as account_urls
from activity import urls as activity_urls
from www import urls as www_urls

ContentSitemap.protocol = "https"

sitemaps = {
    "content": ContentSitemap,
}

urlpatterns = [
    path(f"{settings.ADMIN_SITE_BASE_URL}/", admin.site.urls),
    path(f"{settings.DJANGO_RQ_SITE_BASE_URL}/", include("django_rq.urls")),
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
    path("account", include(account_urls, namespace="account")),
    path("activity", include(activity_urls, namespace="activity")),
    path("", include(www_urls, namespace="www")),
    path("", include("coltrane.urls")),
]
