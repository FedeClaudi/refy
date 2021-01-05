from pathlib import Path

def to_txt(string, fpath, overwrite=False):
    '''
        Saves a string to a .txt file at a given location
    '''
    if Path(fpath).exists() and not overwrite:
        return
        
    with open(fpath, 'w', encoding='utf-8') as out:
        out.write(string)

def from_txt(fpath):
    with open(fpath, 'r', encoding='utf-8') as fin:
        return fin.read()

def isin(l1, l2):
    '''
        Checks if any element of a list is included in a second list
    '''
    return any(x in l2 for x in l1)