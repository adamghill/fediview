from datetime import datetime
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from digest.scorers import Scorer


def _format_media(media):
    url = media["url"]
    description = media["description"] if media["description"] is not None else ""

    formats = {
        "image": f'<div class="media"><a class="glightbox" href="{url}" data-description="{description}" data-desc-position="right"><img src={url} alt="{description}"></img></a></div>',
        "video": f'<div class="media"><video src="{url}" controls width="100%"></video></div>',
        "gifv": f'<div class="media"><video src="{url}" autoplay loop muted playsinline width="100%"></video></div>',
    }

    if formats.__contains__(media.type):
        return formats[media.type]
    else:
        return ""


def _format_display_name(display_name: str, emojis: list) -> str:
    for emoji in emojis:
        display_name = display_name.replace(
            f':{emoji["shortcode"]}:',
            f'<img alt={emoji["shortcode"]} src="{emoji["url"]}">',
        )

    return display_name


class Account:
    additional_posts: list["Post"]
    follows: list["Account"]
    _is_following: bool = None

    def __init__(self, data: dict):
        self._data = data
        self.additional_posts = []
        self.follows = []

    @property
    def is_following(self):
        return self._is_following

    @is_following.setter
    def is_following(self, val):
        self._is_following = val

    @property
    def id(self) -> int:
        return self._data["id"]

    @property
    def acct(self) -> str:
        return self._data["acct"]

    @property
    def followers_count(self) -> int:
        return self._data["followers_count"]

    @property
    def following_count(self) -> int:
        return self._data["following_count"]

    @property
    def username(self) -> str:
        return self._data["username"]

    @property
    def display_name(self) -> str:
        return _format_display_name(self._data["display_name"], self._data["emojis"])

    @property
    def avatar(self) -> str:
        return self._data["avatar"]

    @property
    def followers_count(self) -> int:
        return self._data["followers_count"]

    @property
    def url(self) -> str:
        return self._data["url"].lower()

    def add_additional_post(self, post: "Post") -> None:
        self.additional_posts.append(post)

    def add_follows(self, accounts: list[dict]) -> None:
        self.follows = []

        for data in accounts:
            self.follows.append(Account(data))


class Post:
    base_url = None
    _score = None
    _account = None

    def __init__(self, data: dict):
        self._data = data

    def set_base_url(self, base_url: str) -> None:
        self.base_url = base_url

    def get_score(self, scorer: "Scorer") -> float:
        self._score = scorer.score(self)

        return self._score

    @property
    def home_url(self) -> str:
        if self.base_url is None:
            raise Exception("Post does not have a base_url")

        return f"{self.base_url}/@{self.account.acct}/{self.id}"

    @property
    def score(self) -> float:
        if self._score is None:
            raise Exception("Post has not been scored yet")

        return self._score

    @property
    def url(self) -> str:
        return self._data["url"]

    @property
    def reply_id(self) -> Optional[int]:
        return self._data["in_reply_to_id"]

    @property
    def id(self) -> int:
        return self._data["id"]

    @property
    def replies_count(self) -> int:
        return self._data["replies_count"]

    @property
    def reblogs_count(self) -> int:
        return self._data["reblogs_count"]

    @property
    def favourites_count(self) -> int:
        return self._data["favourites_count"]

    @property
    def content(self) -> str:
        return self._data["content"]

    @property
    def created_at(self) -> datetime:
        return self._data["created_at"]

    @property
    def account(self) -> Account:
        if self._account is None:
            self._account = Account(self._data["account"])

        return self._account

    @property
    def reblogged(self) -> bool:
        return self._data["reblogged"]

    @property
    def favourited(self) -> bool:
        return self._data["favourited"]

    @property
    def bookmarked(self) -> bool:
        return self._data["bookmarked"]

    @property
    def media(self) -> str:
        return "\n".join(
            [_format_media(media) for media in self._data.media_attachments]
        )

    @property
    def tags(self) -> list[str]:
        return [t.name for t in self._data["tags"]]
