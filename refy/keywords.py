from gensim import summarization
import pandas as pd

from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from io import StringIO

from myterial import salmon, orange


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


class Keywords:
    def __init__(self, keywords):
        """
            Represents a list of keywords extracted from text

            Arguments:
                keywords: dict. Dict of keyword:score keywords
        """

        # sort kws and keep only words
        self.kws = pd.Series(keywords).sort_values().index[::-1]

    def __len__(self):
        return len(self.kws)

    def __rich_console__(self, *args, **kwargs):
        yield self.to_table()

    def __str__(self):
        buf = StringIO()
        _console = Console(file=buf, force_jupyter=False)
        _console.print(self)

        return buf.getvalue()

    def to_table(self):
        # create table
        table = Table(
            show_header=False,
            show_lines=False,
            expand=False,
            box=None,
            title=":mag: keywords",
            title_style=f"bold {salmon}",
        )

        table.add_row(*[Panel.fit(kw) for kw in self.kws[:5]])

        return Panel(
            table, expand=False, border_style=f"{orange}", padding=(0, 0, 0, 0)
        )
