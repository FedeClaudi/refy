from rich.progress import track
import pandas as pd

from .utils import from_txt
from .settings import database_path, abstracts_dir


def load_abstracts(ids):
    abstracts = []
    for ID in track(ids, description=f"loading {len(ids)} abstracts..."):
        fpath = abstracts_dir / f"{ID}.txt"
        abstracts.append(from_txt(fpath))

    return abstracts


def load_database():
    return pd.read_hdf(database_path, key="hdf")
