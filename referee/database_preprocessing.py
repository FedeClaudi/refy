import json
import pandas as pd
from pathlib import Path
import gzip
import multiprocessing
from loguru import logger
from rich.progress import track
from langdetect import detect

import sys

sys.path.append("./")

from referee.settings import (
    fields_of_study,
    low_year,
    keywords,
    database_path,
    abstracts_path,
    remote_url_base,
)
from referee.utils import (
    isin,
    to_json,
    from_json,
    raise_on_no_connection,
    retrieve_over_http,
)

ABSTRACTS = {}  # store all abstracts before saving

# ----------------------------- download database ---------------------------- #


@raise_on_no_connection
def download():
    """Download and extract pre-processed database data from remote url."""
    print("Download database data")

    # get urls
    database_url = remote_url_base + "database.h5"
    abstracts_url = remote_url_base + "abstracts.json"

    data = {
        "database": (database_url, database_path),
        "abstracts": (abstracts_url, abstracts_path),
    }

    # download and extract
    for name, (url, path) in data.items():
        logger.debug(f"Downloading and extracting: {name}")

        retrieve_over_http(url, path)


# ---------------------------- preprocess database --------------------------- #


def exclude(entry):
    """
        Select papers based on:
            * field of study
            * publication data
            * if they include keywords in their abstract
            * they are written in english
            * if they have an abstract

        the parameters are set in settings.py

        Arguments:
            entry: dict with paper's metadata

        Returns:
            exclude: bool. True if the entry fails any of the criteria
    """
    # keep only entries in relevant fields
    if not isin(entry["fieldsOfStudy"], fields_of_study):
        return True

    # Keep only recent papers
    entry["year"] = entry["year"] or 0
    if entry["year"] < low_year:
        return True

    # Keep only entries that have an abstract
    abstract = entry["paperAbstract"].lower()
    if len(abstract) < 1:
        return True

    # keep only entries with keywords in abstract
    if not any((keyword in abstract) for keyword in keywords):
        return True

    # keep only english
    try:
        lang = detect(abstract[:50])
    except Exception:
        return False
    else:
        if lang != "en":
            return True

    # ok all good
    return False


def _unpack_single_file(args):
    """
        Unpacks a single .gz file and filters it
        to only keep relevant papers.
        The (ugly) way the arguments are passed to this
        function is to facilitate multiprocessing
    """
    fpath, dfs_dir, n, N = args

    # prepare paths
    name = fpath.name.split(".")[0]
    out = dfs_dir / (name + ".h5")

    # load data
    if fpath.suffix == ".gz":
        with gzip.open(fpath, "r") as datafile:
            data = datafile.readlines()
        data = [d.decode("utf-8") for d in data]
    else:
        with open(fpath) as datafile:
            data = datafile.readlines()

    # create a dataframe with relevant data
    metadata = dict(
        title=[], authors=[], doi=[], url=[], field_of_study=[], id=[], year=[]
    )

    # loop over all entries
    for entry in data:
        entry = json.loads(entry)

        if exclude(entry):
            continue

        # store abstract
        ABSTRACTS[entry["id"]] = entry["paperAbstract"]

        # keep metadata
        metadata["year"].append(
            str(entry["year"]) if "year" in entry.keys() else ""
        )
        metadata["id"].append(str(entry["id"]))
        metadata["title"].append(str(entry["title"]))
        metadata["authors"].append(
            ", ".join([str(a["name"]) for a in entry["authors"]])
        )
        metadata["doi"].append(entry["doi"] or "")
        metadata["url"].append(entry["s2Url"] or "")
        metadata["field_of_study"].append(entry["fieldsOfStudy"] or [""])

    # save
    metadata = pd.DataFrame(metadata)
    metadata.to_hdf(out, key="hdf")
    logger.debug(
        f"Uncompressed: {fpath.name} [{n}/{N}]. kept {len(metadata)}/{len(data)} papers"
    )


def upack_database(folder):
    """
        Opens up .gz with papers metadata info from 
        http://s2-public-api-prod.us-west-2.elasticbeanstalk.com/corpus/download/
        and saves is at a .h5 file. 
        The operation is parallelized to speed things up. 

        For each .gz file:
            1. open the file and load the data
            2. select papers that match the criteria set in settings.py
            3. save the selected papers' metadata to .h5 (pandas dataframe) in folder/dfs
            4. save the selcted papers's abstracct to .txt in folder/abstracts

        Arguments:
            folder: str, Path. Path to the folder where the database data will be stored.
                It must include a subfolder called 'compressed' in which the .gz files live. 
    """
    logger.debug(f"Unpacking database in {folder}")

    # get folders
    folder = Path(folder)

    dfs_dir = folder / "dfs"
    dfs_dir.mkdir(exist_ok=True)

    # extract data from all files
    files = list((folder / "compressed").glob("*.gz"))
    logger.debug(f"Uncompressing {len(files)} files")

    n_cpus = multiprocessing.cpu_count() - 2
    with multiprocessing.Pool(processes=n_cpus) as pool:
        args = [(fl, dfs_dir, n, len(files)) for n, fl in enumerate(files)]
        pool.map(_unpack_single_file, args)

    # save abstract
    logger.debug(f"Saving {len(ABSTRACTS)} to json file")
    to_json(ABSTRACTS, folder / abstracts_path.name)


def make_database(folder):
    """
        Given a database folder filled in by `unpack_database` 
        this function creates the database proper. 

        Arguments:
            folder: str, Path. Path to the folder where the database data is stored.
                User must have run `unpack_database` on the folder's content first. 
    """
    logger.debug(f"Making database from data folder: {folder}")

    folder = Path(folder)
    files = list((folder / "dfs").glob("*.h5"))
    logger.debug(f"Found {len(files)} files")

    # Load all metadata into a single dataframe
    dfs = []
    for f in track(files, description="Loading data..."):
        dfs.append(pd.read_hdf(f, key="hdf"))

    # concatenate
    DATA = pd.concat(dfs)
    logger.debug(f"Found {len(DATA)} papers")

    # remove duplicates
    DATA = DATA.drop_duplicates(subset="title")

    # save abstracts to correct path
    abstracts = from_json(folder / abstracts_path.name)

    abstracts = {k: a for k, a in abstracts.items() if a}
    to_json(abstracts, abstracts_path)
    logger.debug(f"Kept {len(abstracts)} abstracts")

    # keep only papers that have an abstract
    DATA = DATA.loc[DATA["id"].isin(abstracts.keys())]

    # save data
    DATA.to_hdf(database_path, key="hdf")
    logger.debug(
        f"Saved database at: {database_path}. {len(DATA)} entries in total [{len(abstracts)} abstracts]"
    )


if __name__ == "__main__":
    fld = "M:\\PAPERS_DBASE"
    upack_database(fld)
