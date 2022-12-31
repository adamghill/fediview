from django.urls import include, path, re_path
from fbv.views import favicon_emoji, favicon_file

from www import urls as www_urls

urlpatterns = [
    path("unicorn/", include("django_unicorn.urls")),
    path("favicon.ico", favicon_emoji, {"emoji": "🐘"}),
    path(r"apple-touch-icon.png", favicon_emoji, {"emoji": "🐘"}),
    path(r"apple-touch-icon-precomposed.png", favicon_emoji, {"emoji": "🐘"}),
    path("robots.txt", favicon_file, {"file_path": "www/robots.txt"}),
    path("", include(www_urls)),
    path("", include("coltrane.urls")),
]
