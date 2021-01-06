import pandas as pd
from loguru import logger
import json
import tarfile

from .settings import database_path, abstracts_path, base_dir

from .utils import check_internet_connection, retrieve_over_http

# --------------------------------- load data -------------------------------- #


def load_abstracts():
    """
        loads all abstracts from the json file
    
        Returns:
            abstracts: dict with all abstracts
    """
    with open(abstracts_path) as fin:
        abstracts = json.load(fin)

    abstracts = {k: a for k, a in abstracts.items() if a}
    logger.debug(f"Loaded {len(abstracts)} abstracts")
    return abstracts


def load_database():
    """
        Load the search database from file.
        
        Returns:
            database: DataFrame with search database metadata
    """
    dbase = pd.read_hdf(database_path, key="hdf")
    dbase["input"] = False  # differentiate from user input
    logger.debug(f"Loaded database with {len(dbase)} entries")
    return dbase


# ------------------------------- download data ------------------------------ #
def download_database():
    """Download and extract database data from remote url."""
    check_internet_connection()
    print("Download database data")

    # get urls
    remote_url_base = "https://gin.g-node.org/FedeClaudi/Referee/raw/master/"
    database_url = remote_url_base + "database.tar.gz"
    abstracts_url = remote_url_base + "abstracts.tar.gz"

    data = {
        "database": (database_url, database_path),
        "abstracts": (abstracts_url, abstracts_path),
    }

    # download and extract
    for name, (url, path) in data.items():
        logger.debug(f"Downloading and extracting: {name}")

        compressed_path = path.with_suffix(".tar.gz")
        retrieve_over_http(url, compressed_path)

        # Uncompress in brainglobe path:
        tar = tarfile.open(str(compressed_path))
        tar.extractall(path=base_dir)
        tar.close()
