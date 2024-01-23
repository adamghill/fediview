import logging
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.template.loader import get_template
from django.utils.timezone import now
from django_q.tasks import async_task
from post_office import mail
from post_office.models import EmailTemplate

from account.models import Account
from digest.digester import Digest, build_digest
from digest.management.commands.sanitize_generated_emails import sanitize

logger = logging.getLogger(__name__)


def _set_email_template():
    email_template = EmailTemplate.objects.filter(name="digest").first()
    template = get_template("digest/digest.html", using="post_office")

    if not email_template:
        email_template = EmailTemplate.objects.create(name="digest")

    email_template.subject = "Fediview Digest for {{ now|date:'M j, Y' }}"
    email_template.content = ""  # text content
    email_template.html_content = template.template.source
    email_template.save()


def get_email_context(digest: Digest, has_plus: bool) -> dict:
    context = {"now": now()}

    total_posts_count = len(digest.posts)
    total_posts_to_show = len(digest.posts)

    context["has_plus"] = has_plus

    if not has_plus:
        total_posts_to_show = 3

    context["posts"] = digest.posts[:total_posts_to_show]
    context["total_posts_to_show"] = total_posts_to_show
    context["total_posts_count"] = total_posts_count
    context["profile"] = digest.profile

    return context


def send_email(account: Account) -> None:
    profile = account.profile
    assert profile.is_time_to_send_daily_digest, "Ensure that it is time to send the email for this profile"

    # Set a marker to prevent multiple emails being sent at once
    profile.last_daily_digest_sent_at = now()
    profile.save()

    logger.info(f"Create digest for account id {account.id}")

    start = datetime.now(timezone.utc) - timedelta(days=1)

    digest = build_digest(
        start=start,
        end=None,
        scorer_name=account.profile.scorer,
        threshold_name=account.profile.threshold,
        timeline=account.profile.timeline,
        url=account.instance.api_base_url,
        token=account.access_token,
        profile=account.profile,
    )

    logger.info(f"Send digest email to account id {account.id}")

    email = mail.send(
        recipients=account.user.email,
        sender=settings.SERVER_EMAIL,
        template="digest",
        priority="now",
        context=get_email_context(digest, account.profile.has_plus),
    )

    if email.status == 0:
        logger.info(f"Digest email sent to account id {account.id}")

        sanitize(email.id)


def send_emails(*account_ids: int) -> None:
    _set_email_template()

    accounts = []

    if account_ids:
        accounts = Account.objects.filter(id__in=account_ids)
    else:
        accounts = (
            Account.objects.filter(profile__send_daily_digest=True)
            .exclude(user__email__isnull=True)
            .exclude(user__email="")
        )

    for account in accounts:
        if account.profile.is_time_to_send_daily_digest is True:
            async_task(send_email, account)
