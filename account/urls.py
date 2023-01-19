from django.urls import path

from . import views

app_name = "account"

urlpatterns = [
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
    path("auth", views.auth, name="auth"),
]
