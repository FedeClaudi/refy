from gensim import summarization
import pandas as pd
from loguru import logger

from rich.table import Table
from rich.console import Console
from io import StringIO

from myterial import pink, light_blue_light

# -------------------------------- Highlighter ------------------------------- #
"""
    A highlighter to highlight keywords in paper titles
"""


class Highlighter:
    color = light_blue_light

    def __init__(self, words):
        """
            Highlights pieces of text to mark keywords

            Arguments:
                words: list of str of words to mark
        """
        self.words = words

    def __call__(self, text):
        """
            Highlights a piece of text

            Arguments:
                text: str to highlight

            Returns
                text: highlighted string
        """
        for word in self.words:
            text = text.replace(
                " " + word + " ", f"[{self.color}] {word} [/{self.color}]"
            )
        return text


# -------------------------------- get keyword ------------------------------- #


def get_keywords_from_text(text, N):
    """
        Returns a list of N keywords extracted from a string of text

        Arguments:
            text: str
            N: int, number of keywords.

        Returns:
            keywords: list of str of keywords
    """
    return summarization.keywords(text, words=N, split=True)


# ---------------------------------------------------------------------------- #
#                                   Keywords                                   #
# ---------------------------------------------------------------------------- #


class Keywords:
    keep_n = 8  # number of keywords to keep

    def __init__(self, keywords):
        """
            Represents a list of keywords extracted from text

            Arguments:
                keywords: dict. Dict of keyword:score keywords
        """

        # sort kws and keep only words
        self.kws = pd.Series(keywords).sort_values().index[::-1]

        self._kws = self.kws.copy()
        self.kws = self.kws[: self.keep_n]

    def __len__(self):
        return len(self.kws)

    def __rich_console__(self, *args, **kwargs):
        yield self.to_table()

    def __str__(self):
        buf = StringIO()
        _console = Console(file=buf, force_jupyter=False)
        _console.print(self)

        return buf.getvalue()

    def get_highlighter(self):
        """
            Returns a rich.Console that highlights keywords

            Returns:
                console: rich.Console with highlighter
        """
        return Highlighter(self.kws)

    def to_table(self):
        """
            Returns a rich.Table with a view of the keywords
        """
        logger.debug("keywords -> table")
        # create table
        table = Table(
            show_header=False, show_lines=False, expand=False, box=None,
        )
        table.add_row()

        words = [
            f"[{pink}]    [b]{n+1}.[/b] [u {light_blue_light}]{kw}"
            for n, kw in enumerate(self.kws)
        ]
        table.add_row(*words)

        return table
