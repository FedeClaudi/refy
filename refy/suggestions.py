from rich.table import Table
from rich.console import Console
from io import StringIO
from rich import print
import pandas as pd

from loguru import logger

from myterial import orange, amber, pink, light_green, blue_grey_lighter

from refy.utils import get_authors


class Suggestions:
    def __init__(self, suggestions):
        """
            Class to represent a set of suggested papers and 
            do operations on it (e.g. cleaning/filtering)
        
            Arguments:
                suggestions: pd.DataFrame with suggestions data
        """
        self.suggestions = suggestions.drop_duplicates(subset="title").copy()
        self.suggestions["score"] = None  # set it as None to begin with

    def __len__(self):
        return len(self.suggestions)

    def __rich_console__(self, *args, **kwargs):
        yield self.to_table()

    def __str__(self):
        buf = StringIO()
        _console = Console(file=buf, force_jupyter=False)
        _console.print(self)

        return buf.getvalue()

    @property
    def titles(self):
        return self.suggestions.title.values

    def _reset_idx(self):
        self.suggestions = self.suggestions.reset_index(drop=True)

    def to_csv(self, filepath):
        """
            Save dataframe to file

            Arguments:
                filepath: str, Path to .csv file
        """
        self.suggestions.to_csv(filepath)

    def truncate(self, N):
        """
            Keep first N suggestions

            Arguments:
                N: int.
        """
        self.suggestions = self.suggestions[:N]

    def set_score(self, score):
        """
            Fills in the score column with given values and sorts
            the suggestions according to the score

            Arguments:
                score: list of float with score for each paper
        """
        self.suggestions["score"] = score
        self.suggestions = self.suggestions.sort_values(
            "score", ascending=False
        )
        self._reset_idx()

    def remove_overlap(self, user_papers):
        """
            Remove suggestions that appear to overlap with input user papers

            Arguments:
                user_papers: pd.DataFrame with user paper metadata
        """
        self.suggestions = self.suggestions.loc[
            ~self.suggestions.title.isin(user_papers.title)
        ]

        # self.suggestions = self.suggestions.loc[
        #     ~self.suggestions.doi.isin(user_papers.doi)
        # ]

        self._reset_idx()

    def filter(self, since=None, to=None):
        """
            Keep a subset of suggested papers matching criteria

            Arguments:
                since: int or None. If an int is passed it must be a year,
                    only papers more recent than the given year are kept for recomendation
                to: int or None. If an int is passed it must be a year,
                    only papers older than that are kept for recomendation
        """

        if since:
            self.suggestions = self.suggestions.loc[
                self.suggestions.year >= int(since)
            ]
        if to:
            self.suggestions = self.suggestions.loc[
                self.suggestions.year <= int(to)
            ]
        self._reset_idx()

    def get_authors(self):
        """
            Gets the authors that appear in the recomended papers
            sorted by how frequently they appear.

            Returns:
                authors: list of str of authors names
        """
        # Get how often authors show up
        authors = {}
        for i, paper in self.suggestions.iterrows():
            for author in get_authors(paper):
                if author in authors.keys():
                    authors[author] += 1
                else:
                    authors[author] = 1

        # sort authors
        authors = pd.Series(authors)
        if authors.empty:
            self.authors = []
        else:
            self.authors = list(pd.Series(authors).sort_values().index)[::-1]
        return self.authors

    def to_table(self, title=None, highlighter=None):
        """
            Creates a Rich table/panel with a nice representation of the papers

            Arguments:
                title: str. Optional input to replace default title
                highlighter: Highlighter for mark keywords

        """
        logger.debug("Suggestions -> table")
        if self.suggestions.empty:
            print(f"[{orange}]Found no papers matching your query, sorry")
            return "no suggestions found"

        # create table
        table = Table(
            show_header=True,
            header_style=f"bold {pink}",
            show_lines=True,
            expand=False,
            box=None,
            caption=f"[{blue_grey_lighter}]{len(self.suggestions)} papers, recommended by refy :ok_hand:",
            caption_style="dim",
            padding=(0, 1),
        )
        table.add_column("#", style=pink)
        table.add_column("score", style="dim", justify="left")
        table.add_column("year", style="dim", justify="center")
        table.add_column(
            "author",
            style=f"{light_green}",
            justify="right",
            width=22,
            overflow="crop",
        )
        table.add_column(
            "title",
            style=f"bold {orange}",
            max_width=80,
            justify="left",
            overflow="fold",
        )
        table.add_column("DOI", style="dim")

        # add papers to table
        for i, paper in self.suggestions.iterrows():
            if paper.score:
                score = f"[{blue_grey_lighter} dim]" + str(
                    round(paper["score"], 3)
                )
            else:
                score = ""

            if paper.doi:
                url = f"[{blue_grey_lighter}][link=https://doi.org/{paper.doi}]{paper.doi}[/]"
            else:
                url = f"[{blue_grey_lighter}][link={paper.url}]link[/]"

            authors = get_authors(paper)
            if len(authors) > 1:
                author = authors[0] + "[dim] et al."
            else:
                author = authors[0]

            if highlighter is None:
                title = paper.title
            else:
                title = highlighter(paper.title)

            table.add_row(
                str(i + 1),
                score,
                f"[dim {amber}]" + str(paper.year),
                author,
                title,
                url,
            )

            # add empty row for spacing
            table.add_row(
                "", "", "", "", "", "",
            )
        return table
