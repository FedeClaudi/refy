import json
import pandas as pd

from .settings import fields_of_study
from .utils import isin

def _parse_single_file(fpath):
    with open(fpath) as datafile:
        data = datafile.readlines()

    # create a dataframe with relevant data
    metadata = dict(
        title=[],
        abstract = [],
        authors = [],
        doi=[],
        url=[],
        field_of_study=[]
    )
    
    # loop over all entries
    for entry in data:
        entry = json.loads(entry)

        # keep only entries in relevant fields
        if not isin(entry['fieldsOfStudy'], fields_of_study):
            continue

        metadata['title'].append(entry['title'])
        metadata['abstract'].append(entry['paperAbstract'])
        metadata['authors'].append([a['name'] for a in entry['authors']])
        metadata['doi'].append(entry['doi'])
        metadata['url'].append(entry['s2Url'])
        metadata['field_of_study'].append(entry['fieldsOfStudy'])

    metadata = pd.DataFrame(metadata)
    
    a = 1


def make_database():
    '''
        Given a folder of zipped files with papers database data
        from 
        http://s2-public-api-prod.us-west-2.elasticbeanstalk.com/corpus/download/
        this function
            1. unzips them
            2. parses each to extract relevant info
            3. stores them in a nice format
    '''
    # extract data from all files

    # compute Term Frequency-Inverse Document Frequency
    # embedding for terms in the abstracts

    # compute cosine-similarity score

    # save metadata and similarity matrix to file
    return
