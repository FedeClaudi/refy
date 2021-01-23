import json
import pandas as pd
from pathlib import Path
import gzip
import multiprocessing
from loguru import logger
from rich.progress import track
from langdetect import detect
from rich import print

import sys

sys.path.append("./")

from refy.settings import (
    fields_of_study,
    low_year,
    keywords,
    database_path,
    abstracts_path,
)
from refy.utils import (
    isin,
    to_json,
    from_json,
)

ABSTRACTS = {}  # store all abstracts before saving

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
    if not isin([l.lower() for l in entry["fieldsOfStudy"]], fields_of_study):
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
    ab_low = abstract.lower()
    if not any((keyword in ab_low) for keyword in keywords):
        return True

    # keep only english
    try:
        lang = detect(abstract[:50])
    except Exception:
        return True
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
    out = dfs_dir / (name + ".ftr")
    out_abs = dfs_dir / (name + "_abstracts.json")

    # load data
    if fpath.suffix == ".gz":
        with gzip.open(fpath, "r") as datafile:
            data = datafile.readlines()
        data = [d.decode("utf-8") for d in data]
    else:
        with open(fpath) as datafile:
            data = datafile.readlines()

    # create a dataframe with relevant data
    metadata = dict(title=[], authors=[], doi=[], url=[], id=[], year=[])

    # loop over all entries
    abstracts = {}
    for entry in data:
        entry = json.loads(entry)

        if exclude(entry):
            continue

        # store abstract
        abstracts[entry["id"]] = entry["paperAbstract"]

        # keep metadata
        metadata["year"].append(
            str(entry["year"]) if "year" in entry.keys() else ""
        )
        metadata["id"].append(str(entry["id"]))
        metadata["title"].append(str(entry["title"]))
        metadata["authors"].append(
            ";".join([str(a["name"]) for a in entry["authors"]])
        )
        metadata["doi"].append(entry["doi"] or "")
        metadata["url"].append(entry["s2Url"] or "")

    # save
    metadata = pd.DataFrame(metadata)
    metadata.to_feather(out)

    to_json(abstracts, out_abs)

    logger.debug(
        f"Uncompressed: {fpath.name} [{n}/{N}]. Kept {len(metadata)}/{len(data)} papers and {len(abstracts)} abstracts"
    )


def upack_database(folder):
    """
        Opens up .gz with papers metadata info from 
        http://s2-public-api-prod.us-west-2.elasticbeanstalk.com/corpus/download/
        and saves is at a .ftr file. 
        The operation is parallelized to speed things up. 

        For each .gz file:
            1. open the file and load the data
            2. select papers that match the criteria set in settings.py
            3. save the selected papers' metadata to .ftr (pandas dataframe) in folder/dfs
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

    # ? for debugging
    # args = (files[0], dfs_dir, 0, len(files))
    # _unpack_single_file(args)

    n_cpus = multiprocessing.cpu_count() - 2
    with multiprocessing.Pool(processes=n_cpus) as pool:
        args = [(fl, dfs_dir, n, len(files)) for n, fl in enumerate(files)]
        pool.map(_unpack_single_file, args, chunksize=1)


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
    files = list((folder / "dfs").glob("*.ftr"))
    logger.debug(f"Found {len(files)} files")

    # Load all metadata into a single dataframe
    dfs = []
    for f in track(files, description="Loading data..."):
        dfs.append(pd.read_feather(f))

    # concatenate
    DATA = pd.concat(dfs)
    logger.debug(f"Found {len(DATA)} papers")
    print(
        "\n\n[b green]Titles samples:",
        *DATA.title.values[:15],
        "\n",
        sep="\n\n",
    )

    # remove duplicates
    DATA = DATA.drop_duplicates(subset="title")
    logger.debug(f"After dropping duplicates  {len(DATA)} papers are left")

    # load and save abstracts
    logger.debug("Loading abstracts")
    abs_list = [from_json(f) for f in (folder / "dfs").glob("*.json")]
    abstracts = {k: v for d in abs_list for k, v in d.items()}
    logger.debug(f"Loaded {len(abstracts)} abstracts")

    # keep only papers that have an abstract
    logger.debug("Cleaning up data")
    DATA = DATA.loc[DATA["id"].isin(abstracts.keys())]

    # save data
    logger.debug("Saving database")
    DATA.to_feather(database_path)
    logger.debug(
        f"Saved database at: {database_path}. {len(DATA)} entries in total"
    )

    # and only abstracts that have a paper
    logger.debug("Cleaning up abstracts")
    cleaned_abstracts = {k: abstracts[k] for k in DATA["id"].values}

    if len(cleaned_abstracts) != len(DATA):
        raise ValueError(
            f"Found {len(cleaned_abstracts)} abstracts and {len(DATA)} papers !!"
        )

    logger.debug(
        f"Saving {len(cleaned_abstracts)} abstracts to file: {abstracts_path}"
    )
    to_json(cleaned_abstracts, abstracts_path)


if __name__ == "__main__":
    import refy

    refy.set_logging("DEBUG")

    fld = "M:\\PAPERS_DBASE"
    upack_database(fld)

    # make_database(fld)
