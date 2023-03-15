from collections import Counter

from django_unicorn.components import UnicornView

from activity.models import Acct


def _flatten_list(l: list) -> list:
    return [item for sublist in l for item in sublist]


class ReportsView(UnicornView):
    report_type = None  # bug if type annotated with `str`
    posts = None
    emojis_counter = None
    mentions_counter = None
    tags_counter = None
    top_posts = None
    limit: int = 20

    def mount(self):
        self.posts = []
        account = self.request.user.account

        acct = Acct.objects.filter(account=account).first()

        if acct:
            self.posts = acct.posts.prefetch_related(
                "mentions", "tags", "text_emojis"
            ).all()

    def get_report(self):
        if self.report_type == "emojis":
            self.get_top_emojis()
        elif self.report_type == "mentions":
            self.get_top_mentions()
        elif self.report_type == "posts":
            self.get_top_posts()
        elif self.report_type == "tags":
            self.get_top_tags()

    def get_top_emojis(self):
        text_emojis = [post.text_emojis.all() for post in self.posts]
        text_emojis = _flatten_list(text_emojis)

        self.emojis_counter = Counter(
            [text_emoji.text for text_emoji in text_emojis]
        ).most_common(self.limit)

    def get_top_mentions(self):
        mentions = [post.mentions.all() for post in self.posts]
        mentions = _flatten_list(mentions)

        self.mentions_counter = Counter(
            [mention.acct for mention in mentions]
        ).most_common(self.limit)

    def get_top_tags(self):
        tags = [post.tags.all() for post in self.posts]
        tags = _flatten_list(tags)
        self.tags_counter = Counter([tag.name for tag in tags]).most_common(self.limit)

    def get_top_posts(self):
        self.top_posts = self.posts.all().order_by(
            "-reblogs_count", "-favourites_count"
        )[: self.limit]

    class Meta:
        javascript_exclude = (
            "report_type",
            "posts",
            "emojis_counter",
            "mentions_counter",
            "tags_counter",
            "top_posts",
        )
