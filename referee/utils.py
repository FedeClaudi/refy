import json
import sklearn.preprocessing as pp


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
