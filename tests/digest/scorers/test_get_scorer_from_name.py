import pytest

from digest.scorers import get_scorer_from_name

from digest.scorers import (
    ExtendedSimpleScorer,
    ExtendedSimpleWeightedScorer,
    SimpleScorer,
    SimpleWeightedScorer,
)


@pytest.mark.parametrize(
    "scorer_name, expected",
    (
        ("Simple", SimpleScorer),
        ("SimpleWeighted", SimpleWeightedScorer),
        ("ExtendedSimple", ExtendedSimpleScorer),
        ("ExtendedSimpleWeighted", ExtendedSimpleWeightedScorer),
    ),
)
def test_get_scorer_from_name(scorer_name: str, expected: str):
    actual = get_scorer_from_name(scorer_name)

    assert actual == expected


def test_get_scorer_from_name_invalid():
    with pytest.raises(Exception):
        get_scorer_from_name("Unknown")
