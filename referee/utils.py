from pathlib import Path

import sklearn.preprocessing as pp


def cosine_similarities(mat):
    col_normed_mat = pp.normalize(mat.tocsc(), axis=0)
    return col_normed_mat.T * col_normed_mat


def to_txt(string, fpath, overwrite=False):
    """
        Saves a string to a .txt file at a given location
    """
    if Path(fpath).exists() and not overwrite:
        return

    with open(fpath, "w", encoding="utf-8") as out:
        out.write(string)


def from_txt(fpath):
    try:
        with open(fpath, "r", encoding="utf-8") as fin:
            return fin.read()
    except FileNotFoundError:
        # logger.debug(f'Could not load text from file: {fpath.name}')
        return ""


def isin(l1, l2):
    """
        Checks if any element of a list is included in a second list
    """
    return any(x in l2 for x in l1)
