import subprocess
import os
from loguru import logger
from datetime import datetime


def string_to_date(string):
    return datetime.strptime(string, "%Y-%m-%d").date()


def date_to_string(date):
    return date.strftime("%Y-%m-%d")


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
