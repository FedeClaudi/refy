from rich import print
from rich.console import Console
import sys
from loguru import logger

from rich.spinner import Spinner
from rich.text import Text
from rich.terminal_theme import TerminalTheme
from rich.live import Live

from pyinspect.panels import Report
from myterial import orange, salmon, orange_dark

sys.path.append("./")

from refy import download
from refy.suggestions import Suggestions
from refy.authors import Authors
from refy.keywords import Keywords, get_keywords_from_text


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


class SimpleQuery:
    def __init__(self, csv_path=None, html_path=None):
        """
            Base class handling the printing and saving of 
            results from queries and suggest calls. 

            Arguments:
                csv_path: str, Path. Path to a .csv where to save
                    the results
                html_path: str, Path. Path to a .HTML to save formatted
                    results to.
        """
        # get all fils
        download.check_files()

        self.csv_path = csv_path
        self.html_path = html_path
        self.keywords = None

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
        summary.spacer()
        summary.line(orange_dark)
        summary.spacer()

        # authors
        if len(self.authors):
            summary.add(f"[bold {salmon}]:lab_coat:  [u]top authors\n")
            summary.add(self.authors.to_table(), "rich")

        return summary

    def get_keywords(self, papers):
        """
            Extracts set of keywords that best represent the user papers.
            These can be used to improve the search and to improve the
            print out from the query. 

            Arguments:
                papers: pd.DataFrame with papers metadata
        """
        keywords = {}
        for n, (idx, user_paper) in enumerate(papers.iterrows()):
            kwds = get_keywords_from_text(user_paper.abstract, N=10)

            for m, kw in enumerate(kwds):
                if kw in keywords.keys():
                    keywords[kw] += 10 - m
                else:
                    keywords[kw] = 1

        # sort keywords
        self.keywords = Keywords(keywords)

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

    def to_html(self, text_title=None, text=None, sugg_title=""):
        """
            Saves the summary view of the query's content to an html file


            Arguments:
                text_title: str, title for text section
                text: str, text to place in the initial segment of the report
                sugg_title: str, title for the suggestions table
        """
        if self.html_path is None:
            return

        logger.debug(f"Saving query to .HTML at: {self.html_path}")
        summary = self._make_summary(
            text_title=text_title, text=text, sugg_title=sugg_title
        )

        console = Console(record=True, width=170)
        console.print(summary)
        console.save_html(self.html_path, theme=TERMINAL_THEME)

    def to_csv(self):
        """
            Saves suggestions to a .csv file
        """
        if self.csv_path is not None:
            self.suggestions.to_csv(self.csv_path)
