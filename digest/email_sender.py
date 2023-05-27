import logging
from datetime import datetime, timedelta, timezone

from django.conf import settings
from django.template.loader import get_template
from post_office import mail
from post_office.models import EmailTemplate

from account.models import Account
from digest.digester import Digest

from .digester import build_digest

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
    context = {"now": datetime.now()}

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


def send_emails(*account_ids: int) -> None:
    _set_email_template()

    start = datetime.now(timezone.utc) - timedelta(days=1)

    accounts = []

    if account_ids:
        accounts = Account.objects.filter(id__in=account_ids)
    else:
        accounts = (
            Account.objects.filter(profile__has_plus=True)
            .exclude(user__email__isnull=True)
            .exclude(user__email="")
        )

    for account in accounts:
        logger.info(f"Create digest for account id {account.id}")

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

        mail.send(
            recipients=account.user.email,
            sender=settings.SERVER_EMAIL,
            template="digest",
            priority="now",
            context=get_email_context(digest, account.profile.has_plus),
            render_on_delivery=True,
        )

        logger.info(f"Digest email sent to account id {account.id}")
