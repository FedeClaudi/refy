from referee.database import load_database, load_abstracts
from referee import base_dir
from referee.utils import to_json


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
    abstracts = {paper.ID: abstracts[paper.ID] for i, paper in db.iterrows()}

    # save
    to_json(abstracts, base_dir / "test_abstracts.json")
    db.to_hdf(base_dir / "test_database.h5", key="hdf")


if __name__ == "__main__":
    make()
