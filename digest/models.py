import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, ValidationError, parse_obj_as

if TYPE_CHECKING:
    # Only import during type-checking to prevent circular import
    from digest.scorers import Scorer

logger = logging.getLogger(__name__)


class Account(BaseModel):
    id: str
    acct: str
    username: str
    url: HttpUrl

    # optionals
    followers_count: Optional[int]
    following_count: Optional[int]
    display_name: Optional[str]
    avatar: Optional[str]
    emojis: list[dict] = Field(default_factory=list)
    note: Optional[str]
    discoverable: Optional[bool]

    # gets set after init
    is_following: Optional[bool]
    additional_posts: list["Post"] = Field(default_factory=list)
    follows: list["Account"] = Field(default_factory=list)
    is_nobot: bool = Field(default=False)

    def __init__(self, **data: Any):
        super().__init__(**data)

        self.display_name = self._format_display_name()

        if self.note:
            _note = self.note.lower()
            self.is_nobot = "#nobot" in _note or "#nobots" in _note

    def _format_display_name(self) -> str:
        for emoji in self.emojis:
            self.display_name = self.display_name.replace(
                f':{emoji["shortcode"]}:',
                f'<img alt={emoji["shortcode"]} src="{emoji["url"]}">',
            )

        return self.display_name

    def set_is_following(self, logged_in_account: "Account"):
        self.is_following = any(self == a for a in logged_in_account.follows)

    def add_additional_post(self, post: "Post") -> None:
        self.additional_posts.append(post)

    def add_follows(self, accounts: list[dict]) -> None:
        self.follows = []

        for data in accounts:
            self.follows.append(Account.parse_obj(data))

    def __eq__(self, obj: object) -> bool:
        return isinstance(obj, Account) and self.url.lower() == obj.url.lower()


class Card(BaseModel):
    url: HttpUrl
    embed_url: Union[Optional[str], HttpUrl]
    provider_url: Union[Optional[str], HttpUrl]
    blurhash: Optional[str]
    type: str
    title: str
    description: str
    author_name: str
    author_url: Union[Optional[str], HttpUrl]
    provider_name: str
    html: str
    image: Optional[str]
    height: int
    width: int

    def __init__(self, **data: Any):
        super().__init__(**data)

        self.parse_and_set_url("embed_url")
        self.parse_and_set_url("provider_url")
        self.parse_and_set_url("author_url")

    def parse_and_set_url(self, field_name: str) -> None:
        url = getattr(self, field_name)

        if url:
            try:
                http_url = parse_obj_as(HttpUrl, url)
                setattr(self, field_name, http_url)
            except ValidationError:
                # Skip validation errors
                pass
            except Exception as e:
                logger.exception(e)


class Tag(BaseModel):
    name: str


class Application(BaseModel):
    name: str
    website: Union[Optional[str], HttpUrl]


class Post(BaseModel):
    id: str
    url: Optional[str]
    reply_id: Optional[str] = Field(alias="in_reply_to_id")
    replies_count: int
    reblogs_count: int
    favourites_count: int
    content: str
    created_at: datetime
    reblogged: bool
    favourited: bool
    bookmarked: bool
    media_attachments: list  # = Field(default_factory=list)
    account: Account
    card: Optional[Card]
    muted: bool
    language: Optional[str]
    tags: list[Tag]
    mentions: list[Account]
    application: Optional[Application]
    edited_at: Optional[datetime]
    visibility: str
    pinned: bool = False

    # gets set after init
    is_poll: bool = False
    base_url: Optional[str]
    score: Optional[float]
    home_url: Optional[str]
    is_recommendation: Optional[str]

    def __init__(self, **data: Any):
        super().__init__(**data)

        self.is_poll = data["poll"] is not None

    def set_base_url(self, base_url: str) -> None:
        self.base_url = base_url

    def get_score(self, scorer: "Scorer") -> float:
        self.score = scorer.score(self)

        return self.score

    @property
    def home_url(self) -> str:
        if self.base_url is None:
            raise Exception("Post does not have a base_url")

        return f"{self.base_url}/@{self.account.acct}/{self.id}"

    @property
    def media(self) -> str:
        return "\n".join([Post.format_media(media) for media in self.media_attachments])

    @staticmethod
    def format_media(media: dict) -> str:
        url = media["url"]
        description = media["description"] if media["description"] is not None else ""
        description = description.replace('"', "'")

        formats = {
            "image": f'<div class="media"><a class="glightbox" href="{url}" data-description="{description}" data-desc-position="right"><img src={url} alt="{description}"></img></a></div>',
            "video": f'<div class="media"><video src="{url}" controls width="100%"></video></div>',
            "gifv": f'<div class="media"><video src="{url}" autoplay loop muted playsinline width="100%"></video></div>',
        }

        if media.type in formats:
            return formats[media.type]
        else:
            return ""
