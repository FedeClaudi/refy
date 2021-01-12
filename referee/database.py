import pandas as pd
from loguru import logger

from referee.settings import (
    database_path,
    abstracts_path,
    biorxiv_abstracts_path,
    biorxiv_database_path,
)
from referee.utils import from_json

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
    # download semanthic scholar database
    dbase = pd.read_hdf(database_path, key="hdf")
    dbase["source"] = "semanthic scholar"

    # download biorxiv database
    biorxiv_dbase = pd.read_hdf(biorxiv_database_path, key="hdf")
    del biorxiv_dbase["category"]
    biorxiv_dbase["source"] = "biorxiv"

    # merge
    dbase = pd.concat([dbase, biorxiv_dbase], sort=True).reset_index()
    dbase["input"] = False  # differentiate from user input
    logger.debug(f"Loaded database with {len(dbase)} entries")
    return dbase
