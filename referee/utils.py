import json
import sklearn.preprocessing as pp
import pandas as pd
import gzip


def cosine_similarities(mat):
    col_normed_mat = pp.normalize(mat.tocsc(), axis=0)
    return col_normed_mat.T * col_normed_mat


def to_json(obj, fpath):
    with open(fpath, "w") as out:
        json.dump(obj, out)


def from_txt(fpath):
    # try:
    with open(fpath, "r", encoding="utf-8") as fin:
        return fin.read()
    # except FileNotFoundError:
    #     # logger.debug(f'Could not load text from file: {fpath.name}')
    #     return ""


def isin(l1, l2):
    """
        Checks if any element of a list is included in a second list
    """
    return any(x in l2 for x in l1)


def compress_pandas(fpath):
    """
        Loads and re-saves a pandas from a .h5
        to a compressed .tar.gz file
    """
    name = fpath.name.split(".")[0]
    new_path = fpath.parent / (name + "tar.gz")

    pd.read_hdf(fpath, key="hdf").to_hdf(
        new_path, key="hdf", compression="gzip"
    )


def compress_json(fpath):
    """
        Loads and re-saves a josn from a .json
        to a compressed .tar.gz file
    """
    name = fpath.name.split(".")[0]
    new_path = fpath.parent / (name + ".tar.gz")

    with open(fpath, "r") as fin:
        with gzip.open(new_path, "wt", encoding="UTF-8") as fout:
            json.dump(json.load(fin), fout)
