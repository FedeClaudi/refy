import pandas as pd
from loguru import logger

from .utils import from_txt
from .settings import database_path, abstracts_dir


def load_abstracts(ids, progress=None):
    """
        Load the abstracts of a list of papers and returns
        them as a list of strings

        Arguments:
            ids: list of str. List of papers IDs from the database

        Returns:
            abstracts: list of str. List of abstracts
    """
    abstracts = []

    if progress is not None:
        abs_task = progress.add_task(
            "Loading abstracts...",
            start=True,
            total=len(ids),
            current_task="loading",
        )

    for n, ID in enumerate(ids):
        fpath = abstracts_dir / f"{ID}.txt"
        abstracts.append(from_txt(fpath))

        if progress is not None:
            progress.update(abs_task, completed=n)

    valid = len([x for x in abstracts if len(x) > 1])
    logger.debug(f"Found {valid}/{len(ids)} valid abstracts")

    if progress is not None:
        progress.remove_task(abs_task)

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
