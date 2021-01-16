from loguru import logger
from rich import print
import sys
import pandas as pd


from myterial import orange, salmon, amber_light

sys.path.append("./")
from refy.database import load_database
from refy import doc2vec as d2v
from refy.utils import get_authors, isin
from refy._query import SimpleQuery


class query_author(SimpleQuery):
    def __init__(self, *authors, N=20, since=None, to=None, savepath=None):
        """
            Print all authors in the database from a list of authors

            Arguments:
                authors: variable number of str with author names
                N: int. Number of papers to suggest
                since: int or None. If an int is passed it must be a year,
                    only papers more recent than the given year are kept for recomendation
                to: int or None. If an int is passed it must be a year,
                    only papers older than that are kept for recomendation
                savepath: str, Path. Path pointing to a .csv file where the recomendations
                    will be saved
        """

        def cleans(string):
            """ clean a single string """
            for pun in "!()-[]{};:,<>./?@#$%^&*_~":
                string = string.replace(pun, "")
            return string.lower()

        def clean(paper):
            """
                Clean the papers['authors_clean'] entry of the database
                by removing punctuation, forcing lower case etc.
            """
            return [cleans(a) for a in paper.authors_clean]

        SimpleQuery.__init__(self)
        self.start("extracting author's publications")

        logger.debug(
            f"Fining papers by author(s) with {len(authors)} author(s): {authors}"
        )

        # load and clean database
        papers = load_database()

        logger.debug("Cleaning up database author entries")
        papers["authors_clean"] = papers.apply(get_authors, axis=1)
        papers["authors_clean"] = papers.apply(clean, axis=1)

        # filter by author
        keep = papers["authors_clean"].apply(
            isin, args=[cleans(a) for a in authors]
        )
        papers = papers.loc[keep]
        logger.debug(f"Found {len(papers)} papers for authors")

        pd.set_option("display.width", -1)  # to ensure it's not truncated
        pd.set_option("display.max_colwidth", -1)
        logger.debug(
            f"\n\nPapers matching authors:\n{papers.authors.head()}\n\n"
        )

        if papers.empty:
            print(
                f"[{salmon}]Could not find any papers for author(s): {authors}"
            )
            return

        # fill
        self.fill(papers, N, since, to)

        # print
        self.stop()
        ax = " ".join(authors)
        self.print(
            sugg_title=f'Suggestions for author(s): [bold {orange}]"{ax}"\n'
        )

        # save to file
        if savepath:
            self.suggestions.to_csv(savepath)


class query(SimpleQuery):
    def __init__(self, input_string, N=20, since=None, to=None, savepath=None):
        """
            Finds recomendations based on a single input string (with keywords,
            or a paper abstract or whatever) instead of an input .bib file

            Arguments:
                input_stirng: str. String to match against database
                N: int. Number of papers to suggest
                since: int or None. If an int is passed it must be a year,
                    only papers more recent than the given year are kept for recomendation
                to: int or None. If an int is passed it must be a year,
                    only papers older than that are kept for recomendation
                savepath: str, Path. Path pointing to a .csv file where the recomendations
                    will be saved

            Returns:
                suggestions: pd.DataFrame of N recomended papers
        """
        logger.debug("suggest one")
        SimpleQuery.__init__(self)
        self.start("Finding recomended papers")

        # load database and abstracts
        database = load_database()

        # load model
        model = d2v.D2V()

        # find recomendations
        best_IDs = model.predict(input_string, N=N)

        # fill
        papers = database.loc[database["id"].isin(best_IDs)]
        self.fill(papers, N, since, to)

        # print
        self.stop()
        self.print(
            text_title=f"[bold {salmon}]:mag:  [u]search keywords\n",
            text=f"      [b {amber_light}]" + input_string + "\n",
            sugg_title=f"Suggestions:",
        )

        # save to file
        if savepath:
            self.suggestions.to_csv(savepath)


if __name__ == "__main__":
    import refy

    refy.settings.TEST_MODE = False

    refy.set_logging("DEBUG")

    # query("locomotion control mouse steering goal directed")

    # query_author("Gary  Stacey")
    query_author("Carandini M.")
