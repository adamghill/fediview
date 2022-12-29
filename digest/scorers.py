import importlib
import inspect
from abc import ABC, abstractmethod
from math import sqrt

from scipy import stats

from digest.models import Post


class Weight(ABC):
    @classmethod
    @abstractmethod
    def weight(cls, post: Post):
        pass


class UniformWeight(Weight):
    @classmethod
    def weight(cls, post: Post) -> "UniformWeight":
        return 1


class InverseFollowerWeight(Weight):
    @classmethod
    def weight(cls, post: Post) -> "InverseFollowerWeight":
        # Zero out posts by accounts with zero followers that somehow made it to my feed
        if post.account.followers_count == 0:
            weight = 0
        else:
            # inversely weight against how big the account is
            weight = 1 / sqrt(post.account.followers_count)

        return weight


class Scorer(ABC):
    @classmethod
    @abstractmethod
    def score(cls, post: Post):
        pass

    @classmethod
    def get_name(cls):
        return cls.__name__.replace("Scorer", "")


class SimpleScorer(UniformWeight, Scorer):
    @classmethod
    def score(cls, post: Post) -> "SimpleScorer":
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
    @classmethod
    def score(cls, post: Post) -> "SimpleWeightedScorer":
        return super().score(post) * super().weight(post)


class ExtendedSimpleScorer(UniformWeight, Scorer):
    @classmethod
    def score(cls, post: Post) -> "ExtendedSimpleScorer":
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
    @classmethod
    def score(cls, post: Post) -> "ExtendedSimpleWeightedScorer":
        return super().score(post) * super().weight(post)


def get_scorers():
    all_classes = inspect.getmembers(importlib.import_module(__name__), inspect.isclass)
    scorers = [c for c in all_classes if c[1] != Scorer and issubclass(c[1], Scorer)]

    return {scorer[1].get_name(): scorer[1] for scorer in scorers}
