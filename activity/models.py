from django.db import models
from model_utils.models import TimeStampedModel

from account.models import Account, Profile


class Acct(TimeStampedModel):
    """
    Named `Acct` to not conflict with Account.Account.
    """

    account = models.OneToOneField(
        Account, blank=True, null=True, related_name="acct", on_delete=models.CASCADE
    )
    acct_id = models.BigIntegerField()
    username = models.CharField(max_length=1024)
    url = models.URLField()
    acct = models.CharField(max_length=1024)

    @staticmethod
    def get_or_create(digest_account, current_profile: Profile):
        acct = Acct.objects.filter(acct_id=digest_account.id).first()
        known_account = None

        if current_profile.account.account_id == digest_account.id:
            known_account = current_profile.account

        if acct:
            if not acct.account and known_account:
                acct.account = known_account
                acct.save()
        else:
            acct = Acct(
                acct_id=digest_account.id,
                username=digest_account.username,
                url=digest_account.url,
                acct=digest_account.acct,
                account=known_account,
            )

            acct.save()

        return acct


class Application(TimeStampedModel):
    name = models.CharField(max_length=1024)
    website = models.CharField(blank=True, null=True, max_length=1024)


class Tag(TimeStampedModel):
    name = models.CharField(max_length=1024)


class TextEmoji(TimeStampedModel):
    text = models.CharField(max_length=1024)


class Post(TimeStampedModel):
    acct = models.ForeignKey(Acct, related_name="posts", on_delete=models.CASCADE)
    post_id = models.BigIntegerField()
    content = models.TextField()
    text_content = models.TextField()
    url = models.URLField()
    created_at = models.DateTimeField()
    reply_id = models.BigIntegerField(blank=True, null=True)
    is_poll = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    # public, private, etc
    visibility = models.CharField(max_length=255)
    replies_count = models.BigIntegerField(default=0)
    reblogs_count = models.BigIntegerField(default=0)
    favourites_count = models.BigIntegerField(default=0)
    edited_at = models.DateTimeField(blank=True, null=True)
    is_favourited = models.BooleanField(default=False)
    is_reblogged = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)
    is_bookmarked = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    language = models.CharField(blank=True, null=True, max_length=32)
    tags = models.ManyToManyField(Tag)
    mentions = models.ManyToManyField(Acct)
    text_emojis = models.ManyToManyField(TextEmoji)
