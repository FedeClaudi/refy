import json
import requests
import subprocess
import os
from loguru import logger


def isin(l1, l2):
    """
        Checks if any element of a list is included in a second list,
        returns either True or False

        Arguments:
            l1, l2: lists

        Returns:
            is_in: True or False
    """
    if not l1 or not l2:
        return False
    return any(x in l2 for x in l1)


def get_authors(paper):
    """
        Gets the authors of a paper and returns them as a list

        Arguments:
            paper: pd.Series with paper metadata

        Returns:
            authors: list of str of authors
    """
    if paper.source == "biorxiv":
        splitter = "; "
    else:
        splitter = ", "

    return paper.authors.split(splitter)


# --------------------------------- internet --------------------------------- #


def open_in_browser(url):
    """
        Open an url or .html file in default web browser

        Arguments:
            url: str, Path. url or .html file
    """
    url = str(url)

    try:  # should work on Windows
        os.startfile(url)
    except AttributeError:
        try:  # should work on MacOS and most linux versions
            subprocess.call(["open", url])
        except:
            logger.debug("Could not open URL")


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


def raise_on_no_connection(func):  # pragma: no cover
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
    if response.text == "Error : (2002) Connection refused":
        raise ValueError(f"Bad response from url: {url}")
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
