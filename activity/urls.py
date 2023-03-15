from django.urls import path

from . import views

app_name = "activity"

urlpatterns = [
    path("/search", views.search, name="search"),
    path("/delete", views.delete, name="delete"),
    path("/refresh", views.refresh, name="refresh"),
    path("", views.activity, name="activity"),
]
