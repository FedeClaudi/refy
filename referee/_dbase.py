import pandas as pd
from loguru import logger
import json

from .settings import database_path, abstracts_path

# from .utils import check_internet_connection, retrieve_over_http

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
# def download_atlas_data(self):
#     """Download and extract atlas from remote url."""
#     utils.check_internet_connection()

#     # Get path to folder where data will be saved
#     destination_path = self.interm_download_dir / COMPRESSED_FILENAME

#     # Try to download atlas data
#     utils.retrieve_over_http(self.remote_url, destination_path)

#     # Uncompress in brainglobe path:
#     tar = tarfile.open(destination_path)
#     tar.extractall(path=self.brainglobe_dir)
#     tar.close()

#     destination_path.unlink()
