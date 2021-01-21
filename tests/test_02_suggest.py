from refy import suggest
from refy.settings import example_path, base_dir
import pandas as pd


def test_suggest_save():
    # create a path to save the suggestions to
    save_path = base_dir / "ref_test.csv"
    if save_path.exists():
        save_path.unlink()

    # get suggestions
    suggestions = suggest(example_path, N=20, csv_path=save_path).suggestions

    # check suggestions
    assert len(suggestions) == 20, "wrong number of sugg"

    # check saved suggestions
    assert save_path.exists(), "didnt save"
    saved = pd.read_csv(save_path)

    assert len(saved) == 20, "loaded has wrong length"

    save_path.unlink()


def test_suggest_criteria():

    # test criterias
    suggestions = suggest(example_path, N=20, since=2015, to=2019).suggestions

    assert suggestions.suggestions.year.min() == 2015, "since doesnt work"
    assert suggestions.suggestions.year.max() == 2019, "to doesnt work"
