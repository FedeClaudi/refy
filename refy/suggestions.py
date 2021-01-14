from rich.table import Table
from rich.console import Console
from io import StringIO
from rich import print

from loguru import logger

from myterial import salmon, orange, amber, salmon_lighter


class Suggestions:
    def __init__(self, suggestions):
        """
            Class to represent a set of suggested papers and 
            do operations on it (e.g. cleaning/filtering)
        
            Arguments:
                suggestions: pd.DataFrame with suggestions data
        """
        self.suggestions = suggestions.drop_duplicates(subset="title")
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

        self.suggestions = self.suggestions.loc[
            ~self.suggestions.doi.isin(user_papers.doi)
        ]

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
            header_style=f"bold {salmon_lighter}",
            show_lines=True,
            expand=False,
            box=None,
            title=title or ":memo:    recomended papers",
            title_style=f"bold {salmon}",
            title_justify="left",
            caption=f"{len(self.suggestions)} papers, recommended by refy :ok_hand:",
            caption_style="dim",
            padding=(0, 1),
        )
        table.add_column("#")
        table.add_column("score", style="dim", justify="left")
        table.add_column("year", style="dim", justify="center")
        table.add_column("title", style=f"bold {orange}", min_width=40)
        table.add_column(
            "DOI/url", style="dim",
        )

        # add papers to table
        for i, paper in self.suggestions.iterrows():
            if paper.score:
                score = "[dim]" + str(round(paper["score"], 3))
            else:
                score = ""

            if paper.doi:
                url = f"[link=https://doi.org/{paper.doi}]https://doi.org/{paper.doi}[/]"
            else:
                url = f"[link={paper.url}]{paper.url}"

            table.add_row(
                str(i + 1),
                score,
                f"[dim {amber}]" + str(paper.year),
                paper.title
                if highlighter is None
                else highlighter(paper.title),
                url,
            )

        # fit in a panel
        return table
