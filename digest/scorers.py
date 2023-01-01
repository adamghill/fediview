import importlib
import inspect
from abc import ABC, abstractmethod
from math import sqrt

from scipy import stats

from digest.models import Post


class Weight(ABC):
    @classmethod
    @abstractmethod
    def weight(cls, post: Post) -> float:
        pass


class UniformWeight(Weight):
    @classmethod
    def weight(cls, post: Post) -> float:
        return 1.0


class InverseFollowerWeight(Weight):
    """Weight posts by a user with not a lot of followers higher than those with a lot of followers.

    Helps to surface posts by less "well known" accounts.
    """

    @classmethod
    def weight(cls, post: Post) -> float:
        # Zero out posts by accounts with zero followers that somehow made it to the feed
        if post.account.followers_count == 0:
            weight = 0
        else:
            # Inversely weight against how big the account is
            weight = 1 / sqrt(post.account.followers_count)

        return weight


class Scorer(ABC):
    @classmethod
    @abstractmethod
    def score(cls, post: Post) -> float:
        pass

    @classmethod
    def get_name(cls) -> str:
        return cls.__name__.replace("Scorer", "")


class SimpleScorer(UniformWeight, Scorer):
    """Weighted geometric mean of a post's boosts and favorites."""

    @classmethod
    def score(cls, post: Post) -> float:
        if post.reblogs_count or post.favourites_count:
            # If there's at least one metric
            # We don't want zeros in other metrics to multiply that out
            # Inflate every value by 1
            metric_average = stats.gmean(
                [
                    post.reblogs_count + 1,
                    post.favourites_count + 1,
                ]
            )
        else:
            metric_average = 0

        return metric_average * super().weight(post)


class SimpleWeightedScorer(InverseFollowerWeight, SimpleScorer):
    """Weighted geometric mean of a post's boosts and favorites where accounts with less followers are prioritized."""

    @classmethod
    def score(cls, post: Post) -> float:
        return super().score(post) * super().weight(post)


class ExtendedSimpleScorer(UniformWeight, Scorer):
    """Weighted geometric mean of a post's boosts, favorites, and replies."""

    @classmethod
    def score(cls, post: Post) -> float:
        if post.reblogs_count or post.favourites_count or post.replies_count:
            # If there's at least one metric
            # We don't want zeros in other metrics to multiply that out
            # Inflate every value by 1
            metric_average = stats.gmean(
                [
                    post.reblogs_count + 1,
                    post.favourites_count + 1,
                    post.replies_count + 1,
                ],
            )
        else:
            metric_average = 0

        return metric_average * super().weight(post)


class ExtendedSimpleWeightedScorer(InverseFollowerWeight, ExtendedSimpleScorer):
    """Weighted geometric mean of a post's boosts, favorites, and replies where accounts with less followers are prioritized."""

    @classmethod
    def score(cls, post: Post) -> float:
        return super().score(post) * super().weight(post)


def get_scorer_names() -> list[str]:
    all_classes = inspect.getmembers(importlib.import_module(__name__), inspect.isclass)
    scorers = [c for c in all_classes if c[1] != Scorer and issubclass(c[1], Scorer)]

    return [scorer[1].get_name() for scorer in scorers]


def get_scorer_from_name(name: str) -> Scorer:
    """Converts the name of a scorer into a class."""

    if name == "Simple":
        return SimpleScorer
    elif name == "SimpleWeighted":
        return SimpleWeightedScorer
    elif name == "ExtendedSimple":
        return ExtendedSimpleScorer
    elif name == "ExtendedSimpleWeighted":
        return ExtendedSimpleWeightedScorer

    raise Exception("Unknown scorer")
