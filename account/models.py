from django.contrib.auth.models import AbstractUser
from django.db import models
from model_utils.models import TimeStampedModel


class User(AbstractUser):
    pass


class Instance(TimeStampedModel):
    api_base_url = models.URLField()
    client_id = models.CharField(max_length=1024)
    client_secret = models.CharField(max_length=1024)


class Account(TimeStampedModel):
    instance = models.ForeignKey(
        Instance, related_name="accounts", on_delete=models.PROTECT
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=1024)
    account_id = models.BigIntegerField(blank=True, null=True)


class Profile(TimeStampedModel):
    class IndexingType(models.IntegerChoices):
        NONE = 1
        METADATA = 2
        CONTENT = 3

    account = models.OneToOneField(
        Account, related_name="profile", on_delete=models.CASCADE
    )
    hours = models.IntegerField()
    scorer = models.CharField(max_length=255)
    threshold = models.CharField(max_length=255)
    timeline = models.CharField(max_length=255)
    last_retrieval = models.DateTimeField(blank=True, null=True)
    has_plus = models.BooleanField(default=False)
    language = models.CharField(blank=True, null=True, max_length=10)
    indexing_type = models.IntegerField(
        choices=IndexingType.choices, default=IndexingType.NONE
    )
