from loguru import logger
from rich import print
import sys

from myterial import orange, salmon, amber_light

sys.path.append("./")
from refy.database import load_database
from refy import doc2vec as d2v
from refy._query import SimpleQuery


class query_author(SimpleQuery):
    def __init__(self, author, N=20, since=None, to=None, csv_path=None):
        """
            Print all authors in the database from a list of authors

            Arguments:
                authors: str with author name
                N: int. Number of papers to suggest
                since: int or None. If an int is passed it must be a year,
                    only papers more recent than the given year are kept for recomendation
                to: int or None. If an int is passed it must be a year,
                    only papers older than that are kept for recomendation
                csv_path: str, Path. Path pointing to a .csv file where the recomendations
                    will be saved
        """

        def clean(string):
            for punc in ".,;)(":
                string = string.replace(punc, "")
            return string

        SimpleQuery.__init__(self, csv_path=csv_path)
        self.start("extracting author's publications")

        logger.debug(f"Fining papers by from author: '{author}'")

        # load and clean database
        papers = load_database()
        papers["clean_authors"] = papers.authors.apply(clean)

        # select papers
        for auth in author.split(" "):
            papers = papers.loc[
                papers.clean_authors.str.contains(
                    " " + clean(auth) + " ", case=False
                )
            ]

        logger.debug(
            f"Found {len(papers)} papers for author's cleaned name: {author}"
        )

        if papers.empty:
            print(
                f"\n[{salmon}]Could not find any papers for author: {author}"
            )
            self.stop()
            return

        # fill
        self.fill(papers, N, since, to)

        # print
        self.stop()
        self.print(
            sugg_title=f'Suggestions for author(s): [bold {orange}]"{author}"\n'
        )

        # save to file
        self.to_csv()


class query(SimpleQuery):
    def __init__(self, input_string, N=20, since=None, to=None, csv_path=None):
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
                csv_path: str, Path. Path pointing to a .csv file where the recomendations
                    will be saved

            Returns:
                suggestions: pd.DataFrame of N recomended papers
        """
        logger.debug("suggest one")
        SimpleQuery.__init__(self, csv_path=csv_path)
        self.start("Finding recomended papers")

        # load database and abstracts
        database = load_database()

        # load model
        model = d2v.D2V()

        # find recomendations
        best_IDs = model.predict(input_string, N=N)

        # fill
        papers = database.loc[database["id"].isin(best_IDs)]
        if papers.empty:
            print(
                f'\n[bold {salmon}]Could not find any suggested paper with query: "{input_string}"'
            )
            return

        self.fill(papers, N, since, to)

        # print
        self.stop()
        self.print(
            text_title=f"[bold {salmon}]:mag:  [u]search keywords\n",
            text=f"      [b {amber_light}]" + input_string + "\n",
            sugg_title=f"Suggestions:",
        )

        # save to file
        self.to_csv()


if __name__ == "__main__":
    import refy

    refy.settings.TEST_MODE = False

    refy.set_logging("DEBUG")

    # query("locomotion control mouse steering goal directed")
    # query(
    #     "neuron gene expression", N=20, since=2015, to=2018,
    # )

    query_author("Branco Tiago")
    # query_author("Gary Stacey")
    # query_author("Gary  Stacey")
    # query_author("Carandini M.")

    # query_author("carandini")
