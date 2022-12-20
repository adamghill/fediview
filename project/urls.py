from django.urls import include, path

from www import urls as www_urls

urlpatterns = [
    path("unicorn/", include("django_unicorn.urls")),
    path("", include(www_urls)),
]
