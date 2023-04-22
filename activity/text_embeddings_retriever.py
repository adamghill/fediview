import logging
from typing import Union

import tweetnlp
from cache_memoize import cache_memoize
from numpy import ndarray
from tweetnlp.sentence_embedding.model import cosine_similarity

from account.models import Profile
from activity.models import Post

logger = logging.getLogger(__name__)


def save_posts_vectors(profile: Profile):
    posts = Post.objects.filter(acct__account__profile=profile)

    if not posts:
        return

    post_texts = [p.text_content for p in posts]

    logger.debug(f"Generate vectors for {profile}")

    vectors = get_text_embeddings(post_texts)

    logger.debug(f"Save post vectors for {profile}")
    profile.posts_vectors = vectors
    profile.save()


@cache_memoize(60 * 60)
def get_text_embeddings(text: Union[list[str], str]) -> ndarray:
    model = tweetnlp.load_model("sentence_embedding")

    return model.embedding(text)


def get_similarity(vectors_one: ndarray, vectors_two: ndarray) -> float:
    return cosine_similarity(vectors_one, vectors_two)


def get_similarity_to_posts_vectors(profile: Profile, text: str):
    vectors = get_text_embeddings(text)

    return get_similarity(profile.posts_vectors[0], vectors)
