import pytest
from django.utils.timezone import now

from digest.models import Account, Post


@pytest.fixture
def account():
    return Account(
        id="1", acct="test-acct", username="test-username", url="https://test.com"
    )


@pytest.fixture
def post(account, content):
    return Post(
        id="1",
        content=content,
        replies_count=0,
        reblogs_count=0,
        favourites_count=0,
        created_at=now(),
        reblogged=False,
        favourited=False,
        bookmarked=False,
        media_attachments=[],
        account=account,
        muted=False,
        tags=[],
        mentions=[],
        visibility="public",
        poll={},
    )


@pytest.mark.parametrize("content", ["*test content*", "_test content_"])
def test_convert_content_markdown_italics(post):
    expected = "<em>test content</em>"

    post.convert_content_markdown()

    assert expected == post.content


@pytest.mark.parametrize("content", ["**test content**", "__test content__"])
def test_convert_content_markdown_bold(post):
    expected = "<strong>test content</strong>"

    post.convert_content_markdown()

    assert expected == post.content
