from rich.table import Table
from rich.console import Console
from rich.columns import Columns
from io import StringIO
from loguru import logger

from myterial import pink, light_green


class Authors:
    def __init__(self, authors):
        """
            Class to represent a list of authors and 
            fetch metadata about them.

            Arguments:
                authors: list of str of authors names
        """
        self.authors = authors
        logger.debug(f"Spawned Authors with: {len(authors)} authors")

    def __len__(self):
        return len(self.authors)

    def __rich_console__(self, *args, **kwargs):
        yield self.to_table()

    def __str__(self):
        buf = StringIO()
        _console = Console(file=buf, force_jupyter=False)
        _console.print(self)

        return buf.getvalue()

    def to_table(self):
        """
            Returns a rich.Columns object storing tables
            with a view of the authors
        """
        logger.debug("authors -> table")

        def make_table():
            # create table
            table = Table(
                show_header=False, show_lines=False, expand=False, box=None,
            )

            table.add_column(
                style=f"b {pink}", overflow="ellipsis", justify="right"
            )
            table.add_column(style=light_green)
            return table

        if not self.authors:
            return "No authors"

        tables, table = [], None
        for n, author in enumerate(self.authors):
            if not author:
                if table is None:
                    table = make_table()  # otherwise it will give errors
                continue

            # change table evry 4 authors
            if n % 4 == 0:
                if n > 0:
                    tables.append(table)
                if len(tables) == 5:
                    break
                table = make_table()

            table.add_row(f"{n+1}. ", author)

        if len(self) <= 4:
            tables.append(table)

        return Columns(tables, width=28, equal=True, align="left")
