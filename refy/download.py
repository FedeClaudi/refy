import multiprocessing
from loguru import logger
import requests
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.append("./")

from refy.settings import (
    database_path,
    abstracts_path,
    remote_url_base,
    example_path,
    d2v_model_path,
    biorxiv_abstracts_path,
    biorxiv_database_path,
    test_database_path,
    test_abstracts_path,
)

from refy.utils import _request, check_internet_connection
from refy.progress import http_retrieve_progress


# get urls
database_url = remote_url_base + "database.ftr"
abstracts_url = remote_url_base + "abstracts.json"
test_database_url = remote_url_base + "test_database.ftr"
test_abstracts_url = remote_url_base + "test_abstracts.json"
biorxiv_database_url = remote_url_base + "biorxiv_database.ftr"
biorxiv_abstracts_url = remote_url_base + "biorxiv_abstracts.json"
d2v_model = remote_url_base + "d2v_model.model"
d2v_vecs = remote_url_base + "d2v_model.model.docvecs.vectors_docs.npy"
d2v_wv = remote_url_base + "d2v_model.model.wv.vectors.npy"
d2v_sin = remote_url_base + "d2v_model.model.trainables.syn1neg.npy"
example_library = remote_url_base + "example_library.bib"

# organize urls and paths
d2v_base = d2v_model_path.parent
data = [
    (example_library, example_path),
    (database_url, database_path),
    (abstracts_url, abstracts_path),
    (test_database_url, test_database_path),
    (test_abstracts_url, test_abstracts_path),
    (biorxiv_database_url, biorxiv_database_path),
    (biorxiv_abstracts_url, biorxiv_abstracts_path),
    (d2v_model, d2v_model_path),
    (d2v_vecs, d2v_base / "d2v_model.model.docvecs.vectors_docs.npy"),
    (d2v_wv, d2v_base / "d2v_model.model.wv.vectors.npy"),
    (d2v_sin, d2v_base / "d2v_model.model.trainables.syn1neg.npy"),
]


def retrieve_over_http(url, response, output_file_path, task_id):
    """
        Download file from remote location, with progress bar.

        Arguments: 
            url: srt. Remote url to download the data from
            response: response object from sending a request to a target url
            output_file_path: Path. Path to where the downloaded data will be stored
            task_id: task id to update multi-line progress bar
    """

    CHUNK_SIZE = 4096

    try:
        with open(output_file_path, "wb") as fout:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                fout.write(chunk)
                http_retrieve_progress.update(task_id, advance=len(chunk))

    except requests.exceptions.ConnectionError:
        output_file_path.unlink()
        raise requests.exceptions.ConnectionError(
            f"Could not download file from {url}"
        )

    http_retrieve_progress.remove_task(task_id)
    logger.debug(f"Done downloading {output_file_path.name}")


def download_all():
    """
        Download all data used by refy, in parallel for speed.
        It checks if all files used by refy are present and if not
        it downloads them from GIN: 
            https://gin.g-node.org/FedeClaudi/refy/src/master/
    """
    logger.debug("Checking that all files are present")

    # download in parallel
    n_cpus = multiprocessing.cpu_count() - 2
    with http_retrieve_progress as progress:
        with ThreadPoolExecutor(max_workers=n_cpus) as pool:
            for (url, output_file_path) in data:

                # check if file was downloaded already
                if output_file_path.exists():
                    logger.debug(
                        f"Not downloading {output_file_path.name} because it exists already"
                    )
                    continue

                # send a request and start a progress bar
                response = _request(url, stream=True,)

                task_id = progress.add_task(
                    "download",
                    start=True,
                    total=int(response.headers.get("content-length", 0)),
                    filename=output_file_path.name,
                )

                # stream data to file
                pool.submit(
                    retrieve_over_http,
                    url,
                    response,
                    output_file_path,
                    task_id,
                )


def check_all():
    """
        Checks that all necessary files are present
    """
    for url, filepath in data:
        if not filepath.exists():
            return False, filepath
        else:
            return True, None


def check_files():
    """
            Checks that all necessary files are present and tries to download them if not
        """
    # download all missing if connection
    if check_internet_connection():
        download_all()

    # check all files are there
    passed, missing = check_all()
    if not passed:
        raise ValueError(
            f"At least one necessary file missing: {missing.name}. Connect to the internet to download"
        )


if __name__ == "__main__":
    download_all()
