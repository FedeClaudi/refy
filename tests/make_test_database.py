import sys

sys.path.append("./")

from refy.database import load_database, load_abstracts
from refy import base_dir
from refy.utils import to_json


def make():
    """
        Save a small portion of the databases for faster testing
    """
    N = 10000

    # load
    db = load_database()
    abstracts = load_abstracts()

    # select
    db = db.sample(N)
    abstracts = {paper.id: abstracts[paper.id] for i, paper in db.iterrows()}

    # save
    to_json(abstracts, base_dir / "test_abstracts.json")
    db.to_feather(base_dir / "test_database.ftr")


if __name__ == "__main__":
    make()
