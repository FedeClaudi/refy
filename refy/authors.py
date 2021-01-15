from rich.table import Table
from rich.console import Console
from io import StringIO
from scholarly import scholarly

from myterial import salmon, pink, light_blue_light

from refy.utils import check_internet_connection

CONNECTED = check_internet_connection()


def get_scholar(author):
    """
        Uses scholarly to find authors google scholar data

        Arguments:
            author: str. Author name

        Returns:
            author url: str with author's google scholar URL or 
                a message if no internet connection is available
    """
    if CONNECTED:
        try:
            author_data = next(scholarly.search_author(author))
        except StopIteration:
            return None

        return f'https://scholar.google.com/citations?user={author_data["scholar_id"]}&hl=en'
    else:
        return None


class Authors:
    def __init__(self, authors):
        """
            Class to represent a list of authors and 
            fetch metadata about them.

            Arguments:
                authors: list of str of authors names
        """
        self.authors = authors

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
        """
            Returns a rich.Table with a view of the authors
        """
        # create table
        table = Table(
            show_header=False,
            show_lines=False,
            expand=False,
            box=None,
            title=":lab_coat:    authors",
            title_style=f"bold {salmon}",
            title_justify="left",
        )

        table.add_column(style=f"{pink}", justify="right")
        table.add_column(style=f"b {light_blue_light}")
        table.add_column(style="dim")

        for n, author in enumerate(self.authors):
            num = f"{n+1}. "
            gscholar = get_scholar(author)
            if gscholar is not None:
                gscholar = f"[u][link={gscholar}]google[/link]"
            else:
                gscholar = "could not retrieve google scholar account"

            table.add_row(num, author.lstrip(), gscholar)

        return table
