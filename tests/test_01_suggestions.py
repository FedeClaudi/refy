from refy.suggestions import Suggestions
import pandas as pd
import sys

sys.path.append("./")
from tests import DB
import rich

import pytest


@pytest.fixture
def suggestions():
    sugg = Suggestions(DB)
    sugg.truncate(1000)
    return sugg


def test_suggestions_class_base(suggestions):
    len(suggestions)

    assert isinstance(suggestions.suggestions, pd.DataFrame)

    str(suggestions.truncate(20))
    rich.print(suggestions.truncate(10))

    print(suggestions.titles)


def test_suggestions_class_methods(suggestions):

    suggestions.set_score([1 for i in range(len(suggestions))])

    suggestions.filter(since=2015, to=2019)
    assert suggestions.suggestions.year.min() == 2015
    assert suggestions.suggestions.year.max() == 2019

    suggestions.get_authors()

    suggestions.truncate(10)
    assert len(suggestions) == 10


def test_remove_overlap(suggestions):
    suggestions.remove_overlap(DB)
    assert len(suggestions) == 0, "remove overlap didnt work very well.."
