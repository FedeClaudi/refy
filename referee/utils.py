import json
import requests
from rich.table import Table
from rich import print
from rich.panel import Panel

from myterial import orange, salmon

from .progress import http_retrieve_progress

# ------------------------------- print papers ------------------------------- #


def to_table(papers):
    """
        prints a dataframe with papers metadata in a pretty format

        Arguments:
            papers: pd.DataFrame

    """
    # create table
    table = Table(
        show_header=True,
        header_style="bold dim",
        show_lines=True,
        expand=False,
        box=None,
        title="Recomended papers",
        title_style=f"bold {salmon}",
    )
    table.add_column("#", style="dim")
    table.add_column("title", style=f"bold {orange}")
    table.add_column("DOI")

    # add papers to table
    for i, paper in papers.iterrows():
        table.add_row(
            str(i),
            paper.title,
            paper.doi if isinstance(paper.doi, str) else "",
        )

    # fit in a panel
    return Panel(
        table, expand=True, border_style=f"{orange}", padding=(0, 2, 1, 2)
    )


# ----------------------------------- misc ----------------------------------- #


def isin(l1, l2):
    """
        Checks if any element of a list is included in a second list
    """
    return any(x in l2 for x in l1)


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
    CHUNK_SIZE = 4096
    response = requests.get(url, stream=True,)
    if not response.ok:
        raise ValueError(
            f"Failed to get a good response when retrieving from {url}. Response: {response.status_code}"
        )

    try:
        with http_retrieve_progress as progress:
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
