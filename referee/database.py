import pandas as pd
from loguru import logger
import json

from .settings import database_path, abstracts_path


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
