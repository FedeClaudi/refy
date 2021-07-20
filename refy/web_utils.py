import requests


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
    except (requests.ConnectionError, requests.ReadTimeout):
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


@raise_on_no_connection
def request(url, to_json=False):
    """
        Sends a request to an url and
        makes sure it worked
    """
    response = requests.get(url)
    if not response.ok:
        raise ValueError(
            f"Failed to get a good response when retrieving from {url}. Response: {response.status_code}"
        )
    if not to_json:
        return response.content.decode("utf-8")
    else:
        return response.json()
