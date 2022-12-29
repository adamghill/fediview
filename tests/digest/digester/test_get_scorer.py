import pytest

from digest.digester import _get_scorer
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
def test_get_scorer(scorer_name: str, expected: str):
    actual = _get_scorer(scorer_name)

    assert actual == expected


def test_get_scorer_invalid():
    with pytest.raises(Exception):
        _get_scorer("Unknown")
