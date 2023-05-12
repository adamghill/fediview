from django.apps import AppConfig
from django.conf import settings


class Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "activity"
