from rich import print
import sys

from rich.spinner import Spinner
from rich.text import Text

from rich.live import Live

from pyinspect.panels import Report
from myterial import orange, salmon, orange_dark

sys.path.append("./")

from refy import download
from refy.suggestions import Suggestions
from refy.authors import Authors


class SimpleQuery:
    """
        Handles printing of simple queryies(i.e. not from .bib files) results
    """

    def __init__(self):
        download.check_files()

    def __rich_console__(self, *args, **kwargs):
        "Simple query"

    def __str__(self):
        "Simple query"

    def __repr__(self):
        "Simple query"

    def fill(self, papers, N, since, to):
        """
            Given a dataframe of papers and some arguments creates and 
            stores an instance of Suggestions and Authors

            Arguments:
                papers: pd. DataFrame of recomended papers
                N: int. Number of papers to suggest
                since: int or None. If an int is passed it must be a year,
                    only papers more recent than the given year are kept for recomendation
                to: int or None. If an int is passed it must be a year,
                    only papers older than that are kept for recomendation
        """
        # create suggestions
        self.suggestions = Suggestions(papers)
        self.suggestions.filter(since=since, to=to)
        self.suggestions.truncate(N)

        # get authors
        self.authors = Authors(self.suggestions.get_authors())

    def start(self, text):
        """ starts a spinner """
        self.live = Live(
            Spinner("bouncingBall", text=Text(text, style=orange)),
            refresh_per_second=30,
            transient=True,
        )

        self.live.start()

    def stop(self):
        """ stops a spinner """
        self.live.stop()

    def print(self, text_title=None, text=None, sugg_title=""):
        """
            Print a summary with some text, suggested papers and authors

            Arguments:
                text_title: str, title for text section
                text: str, text to place in the initial segment of the report
                sugg_title: str, title for the suggestions table
        """
        # print summary
        summary = Report(dim=orange)
        summary.width = 160

        # text
        if text is not None:
            if text_title is not None:
                summary.add(text_title)
            summary.add(text)

        # suggestions
        if sugg_title:
            summary.add(sugg_title)
        summary.add(
            self.suggestions.to_table(), "rich",
        )
        summary.spacer()
        summary.line(orange_dark)
        summary.spacer()

        # authors
        if len(self.authors):
            summary.add(f"[bold {salmon}]:lab_coat:  [u]top authors\n")
            summary.add(self.authors.to_table(), "rich")

        print(summary)
        print("")
