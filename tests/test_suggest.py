from referee import suggest
from referee.settings import example_path, base_dir
import pandas as pd


def test_suggest():
    # create a path to save the suggestions to
    save_path = base_dir / "ref_test.csv"
    if save_path.exists():
        save_path.unlink()

    # get suggestions
    suggestions = suggest(example_path, N=20, since=2018, savepath=save_path)

    # check suggestions
    assert len(suggestions) == 20
    assert suggestions.year.min == 2018

    # check saved suggestions
    saved = pd.read_csv(save_path)
    assert saved == suggestions

    save_path.unlink()
