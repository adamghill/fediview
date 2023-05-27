from django.urls import path

from . import views

app_name = "account"

urlpatterns = [
    path("/login", views.login, name="login"),
    path("/logout", views.logout, name="logout"),
    path("/auth", views.auth, name="auth"),
    path("/delete", views.delete, name="delete"),
    path("/unsubscribe", views.unsubscribe, name="unsubscribe"),
    path("/sample_email_digest", views.sample_email_digest, name="sample_email_digest"),
    path("", views.account, name="account"),
]
