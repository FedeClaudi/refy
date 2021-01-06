import json
import sklearn.preprocessing as pp
import pandas as pd
import gzip
import requests
from rich.progress import (
    BarColumn,
    DownloadColumn,
    TextColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    Progress,
)

# ----------------------------------- misc ----------------------------------- #


def isin(l1, l2):
    """
        Checks if any element of a list is included in a second list
    """
    return any(x in l2 for x in l1)


def cosine_similarities(mat):
    """ computes cosine similarity """
    col_normed_mat = pp.normalize(mat.tocsc(), axis=0)
    return col_normed_mat.T * col_normed_mat


# --------------------------------- internet --------------------------------- #
def check_internet_connection(
    url="http://www.google.com/", timeout=5, raise_error=True
):
    """Check that there is an internet connection
    url : str
        url to use for testing (Default value = 'http://www.google.com/')
    timeout : int
        timeout to wait for [in seconds] (Default value = 5).
    raise_error : bool
        if false, warning but no error.
    """

    try:
        _ = requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        if not raise_error:
            print("No internet connection available.")
        else:
            raise ConnectionError(
                "No internet connection, try again when you are connected to the internet."
            )
    return False


def retrieve_over_http(url, output_file_path):
    """Download file from remote location, with progress bar.
    Parameters
    ----------
    url : str
        Remote URL.
    output_file_path : str or Path
        Full file destination for download.
    """
    # Make Rich progress bar
    progress = Progress(
        TextColumn("[bold]Downloading...", justify="right"),
        BarColumn(bar_width=None),
        "{task.percentage:>3.1f}%",
        "•",
        DownloadColumn(),
        "• speed:",
        TransferSpeedColumn(),
        "• ETA:",
        TimeRemainingColumn(),
    )

    CHUNK_SIZE = 4096
    response = requests.get(url, stream=True)

    try:
        with progress:
            task_id = progress.add_task(
                "download",
                filename=output_file_path.name,
                start=True,
                total=int(response.headers.get("content-length", 0)),
            )

            with open(output_file_path, "wb") as fout:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    fout.write(chunk)
                    progress.update(task_id, advance=len(chunk), refresh=True)

    except requests.exceptions.ConnectionError:
        output_file_path.unlink()
        raise requests.exceptions.ConnectionError(
            f"Could not download file from {url}"
        )


# --------------------------------- File I/O --------------------------------- #


def to_json(obj, fpath):
    """ saves an object to json """
    with open(fpath, "w") as out:
        json.dump(obj, out)


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
