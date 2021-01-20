from bibtexparser.bparser import BibTexParser
from pathlib import Path
import pandas as pd
from loguru import logger


def load_from_bib(fpath):
    """
        Reads from a .bib file and returns a dictionary
        with entries
    """
    parser = BibTexParser(common_strings=True)

    with open(fpath, encoding="utf-8") as bibtex_file:
        bib_database = parser.parse_file(bibtex_file)

    return bib_database.entries_dict


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
    logger.debug(f"Loaded user input from file: {fpath} | {len(data)} entries")

    # Clean up data
    data = pd.DataFrame(data.values())
    data = data[["title", "journal", "author", "abstract"]]
    data.columns = ["title", "journal", "authors", "abstract"]
    data["id"] = data["title"]

    # keep only papers with abstract
    has_abs = [
        True if (isinstance(a, str) and len(a) > 1) else False
        for a in data["abstract"].values
    ]

    data = data[has_abs].reset_index()

    # log and return
    logger.debug(f"{len(data)}/{len(has_abs)} user papers have abstracts")

    return data
