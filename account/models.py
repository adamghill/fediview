from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.timezone import now
from model_utils.models import TimeStampedModel
from ndarraydjango.fields import NDArrayField


class User(AbstractUser):
    pass


class Instance(TimeStampedModel):
    api_base_url = models.URLField()
    client_id = models.CharField(max_length=1024)
    client_secret = models.CharField(max_length=1024)


class Account(TimeStampedModel):
    instance = models.ForeignKey(Instance, related_name="accounts", on_delete=models.PROTECT)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=1024)
    account_id = models.BigIntegerField(blank=True, null=True)
    followers_count = models.BigIntegerField(blank=True, null=True)
    following_count = models.BigIntegerField(blank=True, null=True)
    favorites_count = models.BigIntegerField(blank=True, null=True)
    bookmarks_count = models.BigIntegerField(blank=True, null=True)

    def url(self):
        username_splits = self.user.username.split("@")

        if len(username_splits) == 3:
            server = username_splits[2]
            username = username_splits[1]

            return f"https://{server}/@{username}"

    def __str__(self):
        return self.user.username


class Profile(TimeStampedModel):
    class IndexingType(models.IntegerChoices):
        NONE = 1
        METADATA = 2
        CONTENT = 3

    account = models.OneToOneField(Account, related_name="profile", on_delete=models.CASCADE)
    hours = models.IntegerField()
    scorer = models.CharField(max_length=255)
    threshold = models.CharField(max_length=255)
    timeline = models.CharField(max_length=255)
    last_retrieval = models.DateTimeField(blank=True, null=True)
    has_plus = models.BooleanField(default=False)
    language = models.CharField(blank=True, null=True, max_length=10)
    indexing_type = models.IntegerField(choices=IndexingType.choices, default=IndexingType.NONE)
    last_indexed_at = models.DateTimeField(blank=True, null=True)
    last_index_error = models.TextField(blank=True, null=True)
    generate_recommendations = models.BooleanField(default=False)
    last_sample_email_sent_at = models.DateTimeField(blank=True, null=True)

    # daily digest
    send_daily_digest = models.BooleanField(default=False)
    daily_digest_hour = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0), MaxValueValidator(11)])
    daily_digest_minute = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(60)]
    )
    daily_digest_am = models.BooleanField(default=True)
    daily_digest_timezone = models.CharField(default="UTC")  # currently unused
    last_daily_digest_sent_at = models.DateTimeField(blank=True, null=True)

    # Vectors
    posts_vectors = NDArrayField(blank=True, null=True)

    @property
    def daily_digest_hour_with_afternoon(self) -> int:
        # `daily_digest_hour` is 0-based index like `datetime.hour`
        hour = self.daily_digest_hour

        # Handle afternoon hours
        if self.daily_digest_am is False:
            hour = hour + 12

        return hour

    @property
    def is_at_least_one_hour_since_last_daily_digest(self) -> bool:
        """Whether there is no last send date or it has been at least an hour since the last send.

        This is to prevent duplicate emails from being sent for the same day.
        """

        if self.last_daily_digest_sent_at is None:
            return True

        next_daily_digest_send_at = self.last_daily_digest_sent_at + relativedelta(hours=1)

        if now() >= next_daily_digest_send_at:
            return True

        return False

    @property
    def is_time_to_send_daily_digest(self) -> bool:
        if self.is_at_least_one_hour_since_last_daily_digest:
            if now().hour == self.daily_digest_hour_with_afternoon:
                if now().minute >= self.daily_digest_minute:
                    return True

        return False

    def __str__(self):
        return str(self.account)


class GitHubAccount(TimeStampedModel):
    account = models.OneToOneField(Account, related_name="github_account", on_delete=models.CASCADE)
    access_token = models.CharField(max_length=1024)
    username = models.CharField(max_length=1024)

    def __str__(self):
        return self.username
