import pytest

from account.models import Profile
from activity.text_embeddings_retriever import get_similarity_to_posts_vectors


@pytest.mark.django_db
def test_get_similarity_to_posts_vectors():
    print(Profile.objects.all().count())
    profile = Profile.objects.get(account__user__username="@adamghill@indieweb.social")

    similarity = get_similarity_to_posts_vectors(profile, "Django is cool")

    print(similarity)

    assert type(similarity) is float
