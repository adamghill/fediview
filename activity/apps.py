from django.apps import AppConfig
from django.conf import settings


class Config(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "activity"

    def ready(self):
        if not settings.DEBUG:
            # print("Preload sentence transformer")
            # from activity.text_embeddings_retriever import _get_sentence_transformer

            # _get_sentence_transformer()
            pass
