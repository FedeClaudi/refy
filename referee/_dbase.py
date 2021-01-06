import pandas as pd
from loguru import logger
import json

from .settings import database_path, abstracts_path


def load_abstracts():
    """
        loads all abstracts from the json file
    
        Returns:
            abstracts: dict with all abstracts
    """
    abstracts = json.load(abstracts_path)
    logger.debug(f"Loaded {len(abstracts)} abstracts")
    return abstracts


def load_database():
    """
        Load the search database from file.
        
        Returns:
            database: DataFrame with search database metadata
    """
    dbase = pd.read_hdf(database_path, key="hdf")
    logger.debug(f"Loaded database with {len(dbase)} entries")
    return dbase


def id_from_title(title, database):
    """
        Given a paper title try to find the corresponding entry
        in the search database and return its ID

        Arguments:
            title: str. Paper title
            database: DataFrame with search database data

        Returns:
            ID: str or None. String with paper ID or None if the 
                paper could not be found in the database
    """
    try:
        ID = database.loc[database.title == title]["id"].values[0]
    except IndexError:
        logger.debug(f"Could not find ID for paper with title: {title}")
        return None

    return ID
