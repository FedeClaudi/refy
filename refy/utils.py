import json
import requests
from rich.table import Table
from rich import print
from rich.panel import Panel

from myterial import salmon, orange, amber

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
        caption=f"{len(papers)} papers, recommended by refy :ok_hand:",
        caption_style="dim",
        padding=(1, 1),
    )
    table.add_column("#")
    table.add_column(":thumbs_up: score", style="dim", justify="center")
    table.add_column("year", style="dim", justify="center")
    table.add_column("title", style=f"bold {orange}", min_width=40)
    table.add_column(
        "DOI/url", style="dim",
    )

    # add papers to table
    for i, paper in papers.iterrows():
        table.add_row(
            str(i + 1),
            "[dim]" + str(round(paper["score"], 3)),
            f"[dim {amber}]" + str(paper.year),
            paper.title,
            f"[dim]https://doi.org/{paper.doi}" if paper.doi else paper.url,
        )

    # fit in a panel
    return Panel(
        table, expand=False, border_style=f"{orange}", padding=(0, 2, 1, 2)
    )


# ----------------------------------- misc ----------------------------------- #


def isin(l1, l2):
    """
        Checks if any element of a list is included in a second list
    """
    return any(x in l2 for x in l1)


# --------------------------------- internet --------------------------------- #
def check_internet_connection(
    url="http://www.google.com/", timeout=2, raise_error=True
):
    """Check that there is an internet connection
    url : str
        url to use for testing (Default value = 'http://www.google.com/')
    timeout : int
        timeout to wait for [in seconds] (Default value = 2).
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


def raise_on_no_connection(func):
    """
        Decorator to avoid running a function when there's no internet
    """

    def inner(*args, **kwargs):
        if not check_internet_connection():
            raise ConnectionError("No internet connection found.")
        else:
            return func(*args, **kwargs)

    return inner


def _request(url, stream=False):
    """
        Sends a request to an url and
        makes sure it worked
    """
    response = requests.get(url, stream=stream)
    if not response.ok:
        raise ValueError(
            f"Failed to get a good response when retrieving from {url}. Response: {response.status_code}"
        )
    return response


@raise_on_no_connection
def request(url):
    """ 
        Sends a request to a URL and returns the JSON
        it fetched (if it went through).
    """
    response = _request(url, stream=False)
    return response.json()


# --------------------------------- File I/O --------------------------------- #


def to_json(obj, fpath):
    """ saves an object to json """
    with open(fpath, "w") as out:
        json.dump(obj, out)


def from_json(fpath):
    """ loads an object from json """
    with open(fpath, "r") as fin:
        return json.load(fin)
