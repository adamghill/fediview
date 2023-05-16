import logging
from typing import Union

import modal
from numpy import dot, ndarray
from numpy.linalg import norm

from account.models import Profile
from activity.models import Post

logger = logging.getLogger(__name__)


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

    try:
        vectors = get_text_embeddings(post_texts)

        logger.debug(f"Save post vectors for {profile}")
        profile.posts_vectors = vectors
        profile.save()
    except Exception as e:
        logger.exception(e)


def get_text_embeddings(text: Union[list[str], str]) -> ndarray:
    modal_get_text_embeddings_fn = modal.Function.lookup(
        "text-embeddings", "Roberta.get_text_embeddings"
    )

    vectors = modal_get_text_embeddings_fn.call(text)

    if vectors is None:
        raise Exception("Invalid vectors")

    return vectors


def cosine_similarity(
    vectors_one: ndarray, vectors_two: ndarray, eps: float = 1e-5
) -> float:
    # cosine similarity between two vectors

    return dot(vectors_one, vectors_two) / (norm(vectors_two) * norm(vectors_two) + eps)


def get_similarity_to_posts_vectors(profile: Profile, text: str):
    vectors = get_text_embeddings(text)

    return cosine_similarity(profile.posts_vectors, vectors)
