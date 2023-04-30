import logging
from typing import Union

import torch
from cache_memoize import cache_memoize
from numpy import dot, ndarray
from numpy.linalg import norm
from sentence_transformers.SentenceTransformer import SentenceTransformer

from account.models import Profile
from activity.models import Post

logger = logging.getLogger(__name__)

sentence_transformer = None


def save_posts_vectors(profile: Profile):
    POSTS_LIMIT = 100
    posts = (
        Post.objects.filter(acct__account__profile=profile)
        .only("text_content")
        .order_by("-created_at")[0:POSTS_LIMIT]
    )

    if not posts:
        return

    post_texts = [p.text_content for p in posts]

    logger.debug(f"Generate vectors for {profile}")

    vectors = get_text_embeddings(post_texts)

    logger.debug(f"Save post vectors for {profile}")
    profile.posts_vectors = vectors
    profile.save()


def _get_sentence_transformer():
    global sentence_transformer

    if sentence_transformer is None:
        DEFAULT_SENTENCE_MODEL = "cambridgeltl/tweet-roberta-base-embeddings-v1"
        logger.debug("Create sentence transformer")
        sentence_transformer = SentenceTransformer(
            DEFAULT_SENTENCE_MODEL, cache_folder="."
        )
        sentence_transformer.to("cpu")
        sentence_transformer.eval()
    else:
        logger.debug("Use existing sentence transformer")

    return sentence_transformer


@cache_memoize(60 * 60 * 24)
def get_text_embeddings(text: Union[list[str], str]) -> ndarray:
    sentence_transformer = _get_sentence_transformer()

    single_input_flag = type(text) is str
    texts = [text] if single_input_flag else text
    assert all(type(t) is str for t in texts), "All items must be strings"
    batch_size = len(texts)

    with torch.no_grad():
        vectors = sentence_transformer.encode(
            texts, batch_size=batch_size, show_progress_bar=False
        )[0]

    return vectors


def cosine_similarity(
    vectors_one: ndarray, vectors_two: ndarray, eps: float = 1e-5
) -> float:
    # cosine similarity between two vectors

    return dot(vectors_one, vectors_two) / (norm(vectors_two) * norm(vectors_two) + eps)


def get_similarity_to_posts_vectors(profile: Profile, text: str):
    vectors = get_text_embeddings(text)

    return cosine_similarity(profile.posts_vectors, vectors)


def is_text_similar_to_vectors(
    vectors: ndarray, text: str, similarity_threshold: float
) -> bool:
    text_vectors = get_text_embeddings(text)
    similarity = cosine_similarity(vectors, text_vectors)

    if similarity > similarity_threshold:
        return True

    return False
