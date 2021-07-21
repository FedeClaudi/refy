from rich import print
from rich.console import Console
import sys
from loguru import logger

from rich.terminal_theme import TerminalTheme


from pyinspect.panels import Report
from myterial import orange, salmon, orange_dark

sys.path.append("./")

from refy.suggestions import Suggestions
from refy.authors import Authors


# define a theme for HTML exports
# see: https://github.com/willmcgugan/rich/blob/d9d59c6eda/rich/terminal_theme.py
TERMINAL_THEME = TerminalTheme(
    (30, 30, 30),
    (0, 0, 0),
    [
        (255, 255, 255),
        (128, 0, 0),
        (0, 128, 0),
        (128, 128, 0),
        (0, 0, 128),
        (128, 0, 128),
        (0, 128, 128),
        (192, 192, 192),
    ],
    [
        (128, 128, 128),
        (255, 0, 0),
        (0, 255, 0),
        (255, 255, 0),
        (0, 0, 255),
        (255, 0, 255),
        (0, 255, 255),
        (255, 255, 255),
    ],
)


class Results:
    def __init__(self):
        """
            Base class handling the printing and saving of 
            results from queries and suggest calls. 
        """

    def fill(self, papers, N=10, since=None, to=None, ignore_authors=False):
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
                ignore_authors: bool. If true the authors information is not extracted
        """
        # create suggestions
        self.suggestions = Suggestions(papers)
        self.suggestions.filter(since=since, to=to)
        self.suggestions.truncate(N)

        # get authors
        if ignore_authors:
            self.authors = []
        else:
            self.authors = Authors(self.suggestions.get_authors())

    def _make_summary(self, text_title=None, text=None, sugg_title=""):
        """
            Creates a summary with some text, suggested papers and authors

            Arguments:
                text_title: str, title for text section
                text: str, text to place in the initial segment of the report
                sugg_title: str, title for the suggestions table

            Returns:
                summary: pyinspect.Report with content
        """
        # try to get an highlighter
        try:
            highlighter = self.keywords.get_highlighter()
        except:
            highlighter = None

        # print summary
        summary = Report(dim=orange)
        summary.width = 160

        # text
        if text is not None:
            if text_title is not None:
                summary.add(text_title)
            summary.add(text)

        # keywords
        if self.keywords is not None:
            summary.add(f"[bold {salmon}]:mag:  [u]keywords\n")
            summary.add(self.keywords.to_table(), "rich")
            summary.spacer()
            summary.line(orange_dark)
            summary.spacer()

        # suggestions
        if sugg_title:
            summary.add(sugg_title)
        summary.add(
            self.suggestions.to_table(highlighter=highlighter), "rich",
        )

        # authors
        if len(self.authors):
            summary.spacer()
            summary.line(orange_dark)
            summary.spacer()

            summary.add(f"[bold {salmon}]:lab_coat:  [u]top authors\n")
            summary.add(self.authors.to_table(), "rich")

        return summary

    def print(self, text_title=None, text=None, sugg_title=""):
        """
            Print a summary with some text, suggested papers and authors

            Arguments:
                text_title: str, title for text section
                text: str, text to place in the initial segment of the report
                sugg_title: str, title for the suggestions table
        """
        summary = self._make_summary(
            text_title=text_title, text=text, sugg_title=sugg_title
        )

        print(summary)
        print("")

    def to_html(self, html_path, text_title=None, text=None, sugg_title=""):
        """
            Saves the summary view of the query's content to an html file


            Arguments:
                text_title: str, title for text section
                text: str, text to place in the initial segment of the report
                sugg_title: str, title for the suggestions table
        """
        logger.debug(f"Saving query to .HTML at: {html_path}")
        summary = self._make_summary(
            text_title=text_title, text=text, sugg_title=sugg_title
        )

        console = Console(record=True, width=170)
        console.print(summary)
        console.save_html(html_path, theme=TERMINAL_THEME)

    def to_csv(self, csv_path):
        """
            Saves suggestions to a .csv file
        """
        self.suggestions.to_csv(csv_path)
