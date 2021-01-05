from referee.database import upack_database, make_database
from referee._dbase import load_database
from referee.settings import database_path, abstracts_dir
from rich.progress import track
from pathlib import Path
from shutil import copyfile
import multiprocessing


database = load_database()

old_abstracts_dir = Path(r'M:\PAPERS_DBASE\abstracts')


def copy(ID):
    ID, n, N = ID

    if n % 1000 == 0:
        print(f'{n}/{N}')

    IN = old_abstracts_dir / f'{ID}.txt'
    OUT = abstracts_dir/f'{ID}.txt'

    if OUT.exists():
        return
    try:
        copyfile(
            IN, 
            
            OUT)
    except:
        print(f'Did not find file: {IN}')
        pass

if __name__ == '__main__':
    n_cpus = multiprocessing.cpu_count()
    with multiprocessing.Pool(processes=n_cpus) as pool:
        pool.map(copy, ((ID, n, len(database)) for n, ID in enumerate(database['id'].values)))


# if __name__ == "__main__":
#     fld = r"M:\PAPERS_DBASE"
#     # upack_database(fld)

#     make_database(fld)

