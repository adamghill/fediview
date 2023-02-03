from django.urls import path

from . import views

app_name = "www"

urlpatterns = [
    path("plus", views.plus, name="plus"),
    path("", views.index, name="index"),
]
