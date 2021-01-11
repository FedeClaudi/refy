import pandas as pd
from loguru import logger

from .settings import (
    database_path,
    abstracts_path,
    biorxiv_abstracts_path,
    biorxiv_database_path,
)
from .utils import from_json

# --------------------------------- load data -------------------------------- #


def load_abstracts():
    """
        loads all abstracts from the json files
    
        Returns:
            abstracts: dict with all abstracts
    """
    abstracts = from_json(abstracts_path)
    abstracts.update(from_json(biorxiv_abstracts_path))

    # remove empy abstracts
    logger.debug(f"Loaded {len(abstracts)} abstracts")
    return abstracts


def load_database():
    """
        Load papers databases from files.
        
        Returns:
            database: DataFrame with search database metadata
    """
    dbase = pd.read_hdf(database_path, key="hdf")
    dbase.append(pd.read_hdf(biorxiv_database_path, key="hdf"))

    dbase["input"] = False  # differentiate from user input
    logger.debug(f"Loaded database with {len(dbase)} entries")
    return dbase
