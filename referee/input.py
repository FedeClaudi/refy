from bibtexparser.bparser import BibTexParser
from pathlib import Path
import pandas as pd
import json
from loguru import logger

# ------------------------------- augment data ------------------------------- #


def augment_data(papers, database):
    """
        Given a dataframe with papers details, try to find the same papers
        in the papers database, then return a dataframe with matched papers
    """
    logger.debug("Expanding user input")

    # Match user entries
    matches = database.loc[database.title.isin(papers["title"])]
    valid = len(matches)
    logger.debug(f"Found IDs for {valid}/{len(papers)} papers")
    print(
        f"Matched {valid}/{len(papers)} papers with entries in the database.\n"
        f"Using {valid} papers for search."
    )

    return matches


# --------------------------------- load data -------------------------------- #


def load_from_bib(fpath):
    """
        Reads from a .bib file and returns a dictionary
        with entries
    """
    parser = BibTexParser(common_strings=True)

    with open(fpath) as bibtex_file:
        bib_database = parser.parse_file(bibtex_file)

    return bib_database.entries_dict


def load_from_json(fpath):
    """
        Reads from a .json file and returns a dictionary
        with entries
    """
    with open(fpath) as json_file:
        json_database = json.load(json_file)

    return json_database


def load_user_input(fpath):
    """
        Parse an input library to extract authors and topics.
        From the path to a bib file extract a dictionary of bib-like entries
        and create a dataframe from these

        Arguments:
            fpath: str, Path. Path to a .bib file
    """

    def fill_missing(entry):
        ks = entry.keys()
        if "title" not in ks:
            entry["title"] = "no title"

        if "journal" not in ks:
            entry["journal"] = "no journal"

        if "authors" not in ks:
            entry["authors"] = "no authors"

        return entry

    # load from file
    fpath = Path(fpath)
    if fpath.suffix == ".bib":
        data = load_from_bib(fpath)
    else:
        raise NotImplementedError(
            f"Cannot parse input with file type: {fpath.suffix}"
        )
    logger.debug(
        f"Loading user input from file: {fpath} | {len(data)} entries"
    )

    # Get data
    metadata = dict(authors=[], journal=[], title=[],)

    for entry in data.values():
        entry = fill_missing(entry)
        metadata["title"].append(entry["title"])
        metadata["journal"].append(entry["journal"])
        metadata["authors"].append(entry["authors"])

    return pd.DataFrame(metadata)
