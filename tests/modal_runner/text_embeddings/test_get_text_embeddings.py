import pytest

from modal_runner.text_embeddings import Roberta


@pytest.fixture()
def roberta():
    _roberta = Roberta()
    _roberta.cache_folder = "./.model"
    _roberta.__enter__()

    return _roberta


def test_get_text_embeddings_string(roberta):
    vectors = roberta.get_text_embeddings("some test text here")

    assert len(vectors) > 50


def test_get_text_embeddings_list(roberta):
    vectors = roberta.get_text_embeddings(["some test text here", "more text here"])

    assert len(vectors) > 50
