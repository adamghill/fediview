from django.urls import path

from . import views

app_name = "www"

urlpatterns = [
    path("plus/auth", views.plus_auth, name="plus_auth"),
    path("plus/oauth", views.plus_oauth, name="plus_oauth"),
    path("plus", views.plus, name="plus"),
    path("", views.index, name="index"),
]
