from bibtexparser.bparser import BibTexParser
from pathlib import Path
import pandas as pd
import json


# ------------------------------- augment data ------------------------------- #
def augment_data(papers):
    """
        Given a dataframe with papers details, try to find the same papers
        in the papers database, then augment the original dataframe with the
        new details
    """

    return 2


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
    # load from file
    fpath = Path(fpath)
    if fpath.suffix == ".bib":
        data = load_from_bib(fpath)
    else:
        raise NotImplementedError(
            f"Cannot parse input with file type: {fpath.suffix}"
        )

    # Get data
    metadata = dict(authors=[], year=[], journal=[], topic=[],)

    for entry in data.values():
        metadata["authors"].append(entry["author"])
        metadata["year"].append(entry["year"])
        metadata["journal"].append(entry["journal"])
        metadata["authors"].append(entry["author"])

    return pd.DataFrame(metadata)
