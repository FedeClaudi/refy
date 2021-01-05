import json
import pandas as pd
from pathlib import Path
import gzip
import multiprocessing
from sklearn.feature_extraction.text import TfidfVectorizer
from loguru import logger

from .settings import fields_of_study, base_dir, low_year, keywords
from .utils import isin, to_txt
from ._dbase import load_abstracts


def exclude(entry):
    '''
        Only select papers based on:
            * field of study
            * publication data
            * if they include keywords in their abstract

        the parameters are set in settings.py

        Arguments:
            entry: dict with paper's metadata

        Returns:
            exclude: bool. True if the entry fails any of the criteria
    '''
    # keep only entries in relevant fields
    if not isin(entry['fieldsOfStudy'], fields_of_study):
        return True

    # Keep only recent papers
    entry['year'] = entry['year'] or 0
    if entry['year'] < low_year: 
        return True

    # keep only entries with keywords in abstract
    if not any((keyword in entry['paperAbstract']) for keyword in keywords):
        return True

    # ok all good
    return False



def _parse_single_file(args):
    fpath, abstracts_dir, dfs_dir, n, N = args
    logger.debug(f"Parsing compressed file: {fpath.name}")

    # check if file was opened before
    name = fpath.name.split('.')[0]
    out = dfs_dir / (name + '.h5')
    # if out.exists():
    #     return pd.read_hdf(out, key='hdf')

    # load data
    if fpath.suffix == '.gz':
        with gzip.open(fpath,'r') as datafile:
            data = datafile.readlines()
        data = [d.decode('utf-8') for d in data]
    else:
        with open(fpath) as datafile:
            data = datafile.readlines()

    # create a dataframe with relevant data
    metadata = dict(
        title=[],
        authors = [],
        doi=[],
        url=[],
        field_of_study=[],
        id=[]
    )
    
    # loop over all entries
    for entry in data:
        entry = json.loads(entry)

        if exclude(entry):
            continue

        # save abstract to file
        to_txt(str(entry['paperAbstract']), abstracts_dir / f'{entry["id"]}.txt')

        # keep metadata
        metadata['id'].append(str(entry['id']))
        metadata['title'].append(str(entry['title']))
        metadata['authors'].append([str(a['name']) for a in entry['authors']])
        metadata['doi'].append(entry['doi'] or '')
        metadata['url'].append(entry['s2Url'] or '')
        metadata['field_of_study'].append(entry['fieldsOfStudy'] or [''])

    metadata = pd.DataFrame(metadata)

    # save 
    print(f'Processed {n}/{N} kept {len(metadata)}/{len(data)} papers')
    metadata.to_hdf(out, key='hdf')


def upack_database(folder):
    '''
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
    '''
    loguru.debug(f'Unpacking database in {folder}')

    # get folders
    folder = Path(folder)
    
    dfs_dir = folder / 'dfs'
    dfs_dir.mkdir(exist_ok=True)

    abstracts_dir = folder / 'abstracts'
    abstracts_dir.mkdir(exist_ok=True)

    # extract data from all files
    files = list((folder/'compressed').glob('*.gz'))

    # for debugging
    # _parse_single_file((files[0], abstracts_dir, dfs_dir, 0, len(files)))

    n_cpus = multiprocessing.cpu_count()
    with multiprocessing.Pool(processes=n_cpus) as pool:
        args = [(fl, abstracts_dir, dfs_dir, n, len(files)) for n, fl in enumerate(files)]
        results = pool.map(_parse_single_file, args)


def make_database(folder):
    '''
        Given a database folder filled in by `unpack_database` this function creates the database proper. 
        It loads the dataframes and abstracts saved by `unpack_database` and uses 
        erm Frequency-Inverse Document Frequency (TF-IDF) embedding
        (https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
        and cosine similarity to create a similarity matrix across papers, which is then saved to file. 

        Arguments:
            folder: str, Path. Path to the folder where the database data is stored.
                User must have run `unpack_database` on the folder's content first. 
    '''
    logger.debug(f"Making database in folder: {folder}")

    folder = Path(folder)
    abstracts_dir = folder / 'abstracts'

    files = (folder / 'dfs').glob('*.h5')

    # Get the ID of each paper
    ids = []
    for f in files:
        ids.extend(list(pd.read_hdf(f, key='hdf')['id'].values))
    logger.debug(f"Found {len(ids)} papers")

    ids = ids[:10] # ! for debugging

    # Load each paper's abstract to create embedding
    logger.debug('Loading abstracts')
    abstracts = load_abstracts(ids, abstracts_dir)

    # create embedding
    # Define a TF-IDF Vectorizer Object. Remove all english stop words such as 'the', 'a'
    tfidf = TfidfVectorizer(stop_words='english')

    # Construct the required TF-IDF matrix by fitting and transforming the data
    logger.debug('Fitting TfidfVectorizer model')
    tfidf_matrix = tfidf.fit_transform(abstracts)

    # compute cosine similarity

    
    # save results

    a = 1
    # dfs = []
    # for n, fl in track(enumerate(files), description='opening compressed', total=len(files)):
    #     dfs.append(_parse_single_file(fl, abstracts_dir, dfs_dir))

    # # save all dfs
    # pd.concat(dfs).to_hdf(folder/'database.h5', key='hdf')
    # a = 1

    # compute Term Frequency-Inverse Document Frequency
    # embedding for terms in the abstracts

    # compute cosine-similarity score

    # save metadata and similarity matrix to file
    return
