import pandas as pd
from loguru import logger

from refy.settings import (
    database_path,
    abstracts_path,
    biorxiv_abstracts_path,
    biorxiv_database_path,
    test_abstracts_path,
    test_database_path,
)
from refy import settings
from refy.utils import from_json


# --------------------------------- load data -------------------------------- #


def load_abstracts():
    """
        loads all abstracts from the json files
    
        Returns:
            abstracts: dict with all abstracts
    """
    if not settings.TEST_MODE:  # pragma: no cover
        abstracts = from_json(abstracts_path)
        abstracts.update(from_json(biorxiv_abstracts_path))
    else:
        logger.debug("loading abstracts in TEST MODE")
        abstracts = from_json(test_abstracts_path)

    # remove empy abstracts
    logger.debug(f"Loaded {len(abstracts)} abstracts")
    return abstracts


def load_database():
    """
        Load papers databases from files.
        
        Returns:
            database: DataFrame with search database metadata
    """
    if not settings.TEST_MODE:  # pragma: no cover
        # download semanthic scholar database
        dbase = pd.read_hdf(database_path, key="hdf")
        dbase["source"] = "semanthic scholar"

        # download biorxiv database
        biorxiv_dbase = pd.read_hdf(biorxiv_database_path, key="hdf")
        del biorxiv_dbase["category"]
        biorxiv_dbase["source"] = "biorxiv"

        # merge
        dbase = pd.concat([dbase, biorxiv_dbase], sort=True).reset_index()
    else:
        logger.debug(f"Loading database in TEST MODE")
        dbase = pd.read_hdf(test_database_path, key="hdf")

    # clean up years column
    years = [int(p.year) if p.year else 0 for i, p in dbase.iterrows()]
    dbase["year"] = years

    dbase["input"] = False  # differentiate from user input

    logger.debug(f"Loaded database with {len(dbase)} entries")
    return dbase
