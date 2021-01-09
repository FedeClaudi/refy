import json
import pandas as pd
from pathlib import Path
import gzip
import multiprocessing
from loguru import logger
from rich.progress import track
from langdetect import detect

from .settings import (
    fields_of_study,
    low_year,
    keywords,
    database_path,
    abstracts_path,
)
from .utils import (
    isin,
    to_json,
    check_internet_connection,
    retrieve_over_http,
)

ABSTRACTS = {}  # store all abstracts before saving

# ----------------------------- download database ---------------------------- #


def download_database():
    """Download and extract database data from remote url."""
    check_internet_connection()
    print("Download database data")

    # get urls
    remote_url_base = "https://gin.g-node.org/FedeClaudi/Referee/raw/master/"
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
        Only select papers based on:
            * field of study
            * publication data
            * if they include keywords in their abstract
            * they are written in english

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

    # keep only entries with keywords in abstract
    if not any((keyword in entry["paperAbstract"]) for keyword in keywords):
        return True

    # keep only english
    try:
        lang = detect(entry["paperAbstract"][:50])
    except Exception:
        return False
    else:
        if lang != "en":
            return True

    # ok all good
    return False


def _parse_single_file(args):
    fpath, dfs_dir, n, N = args
    logger.debug(f"Parsing compressed file: {fpath.name}")

    # check if file was opened before
    name = fpath.name.split(".")[0]
    out = dfs_dir / (name + ".h5")
    # if out.exists():
    #     return pd.read_hdf(out, key='hdf')

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
        title=[], authors=[], doi=[], url=[], field_of_study=[], id=[]
    )

    # loop over all entries
    for entry in data:
        entry = json.loads(entry)

        if exclude(entry):
            continue

        # store abstract
        ABSTRACTS[entry["id"]] = entry["paperAbstract"]

        # keep metadata
        metadata["id"].append(str(entry["id"]))
        metadata["title"].append(str(entry["title"]))
        metadata["authors"].append([str(a["name"]) for a in entry["authors"]])
        metadata["doi"].append(entry["doi"] or "")
        metadata["url"].append(entry["s2Url"] or "")
        metadata["field_of_study"].append(entry["fieldsOfStudy"] or [""])

    metadata = pd.DataFrame(metadata)

    # save
    print(f"Processed {n}/{N} kept {len(metadata)}/{len(data)} papers")
    metadata.to_hdf(out, key="hdf")


def upack_database(folder):
    """
        Opens up .gz with papers metadata info from 
        http://s2-public-api-prod.us-west-2.elasticbeanstalk.com/corpus/download/
        and saves selected papers to dataframes and their abstracts to .txt
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

    n_cpus = multiprocessing.cpu_count()
    with multiprocessing.Pool(processes=n_cpus) as pool:
        args = [(fl, dfs_dir, n, len(files)) for n, fl in enumerate(files)]
        pool.map(_parse_single_file, args)


def make_database(folder):
    """
        Given a database folder filled in by `unpack_database` this function creates the database proper. 
        (https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
        and cosine similarity to create a similarity matrix across papers, which is then saved to file. 

        Arguments:
            folder: str, Path. Path to the folder where the database data is stored.
                User must have run `unpack_database` on the folder's content first. 
    """
    raise NotImplementedError(f"This code is old and needs checking")
    logger.debug(f"Making database from data folder: {folder}")

    folder = Path(folder)
    files = list((folder / "dfs").glob("*.h5"))

    # Load all metadata into a single dataframe
    logger.debug(f"Loading all dataframes ({len(files)} files)")
    dfs = []
    count = 0
    for f in track(files, description="Loading data..."):
        count += len(pd.read_hdf(f, key="hdf"))
        dfs.append(pd.read_hdf(f, key="hdf"))

    # concatenate
    DATA = pd.concat(dfs)
    logger.debug(f"Found {len(DATA)} papers")

    # save data
    DATA.to_hdf(database_path, key="hdf")
    logger.debug(
        f"Saved database at: {database_path}. {len(DATA)} entries in total"
    )

    # save abstract
    to_json(ABSTRACTS, abstracts_path)
