from rich.progress import track

from .utils import from_txt


def load_abstracts(ids, abstracts_dir):
    abstracts = []
    for ID in track(ids, description=f'loading {len(ids)} abstracts...'):
        fpath = abstracts_dir / f'{ID}.txt'
        abstracts.append(from_txt(fpath))

    return abstracts