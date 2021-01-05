import bibtexparser
from bibtexparser.bparser import BibTexParser
from pathlib import Path
import pandas as pd
import json

# -------------------------------- parse data -------------------------------- #

def get_metadata(data):
    '''
        Given a dictionary of bib-like entries, extract
            * authors
            * year
            * journal 
            * topic
        and return as a pandas dataframe
    '''
    parsed = dict(
        authors=[],
        year=[],
        journal=[],
        topic=[],
    )

    for entry in data.values():
        parsed['authors'].append(entry['author'])
        parsed['year'].append(entry['year'])
        parsed['journal'].append(entry['journal'])


        parsed['authors'].append(entry['author'])

        a = 1


# ---------------------------------- loaders --------------------------------- #

def load_from_bib(fpath):
    '''
        Reads from a .bib file and returns a dictionary
        with entries
    '''
    parser = BibTexParser(common_strings=True)

    with open(fpath) as bibtex_file:
        bib_database = parser.parse_file(bibtex_file)

    return bib_database.entries_dict

def load_from_json(fpath):
    '''
        Reads from a .json file and returns a dictionary
        with entries
    '''
    with open(fpath) as json_file:
        json_database = json.load(json_file)

    return json_database

# --------------------------------- main func -------------------------------- #

def parse(fpath):
    '''
        Parse an input library to extract authors and topics
    '''
    # load from file
    fpath = Path(fpath)
    if fpath.suffix == ".bib":
        data = load_from_bib(fpath)
    else:
        raise NotImplementedError(f'Cannot parse input with file type: {fpath.suffix}')

    # Get data
    data = get_metadata(data)
    a = 1
    # if fpat.ext