from loguru import logger
from rich import print
import sys

from myterial import orange, salmon, amber_light

sys.path.append("./")
from refy.database import load_database
from refy import doc2vec as d2v
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
        SimpleQuery.__init__(self)
        self.start("extracting author's publications")

        logger.debug(
            f"Fining papers by author(s) with {len(authors)} author(s): {authors}"
        )

        # load and clean database
        papers = load_database()
        # papers['stripped_authors'] = papers.authors.str.replace(r'[^\w\s]', ' ', regex=True)

        # select papers with authors
        for author in authors:
            author.replace("  ", " ")
            for name in author.split(" "):
                if len(author.replace(".", "")) == 1:
                    # ignore initials
                    continue

                # select papers
                papers = papers.loc[
                    papers.authors.str.contains(name, case=False, regex=False)
                ]

        logger.debug(f"Found {len(papers)} papers for authors")

        if papers.empty:
            print(
                f"[{salmon}]Could not find any papers for author(s): {authors}"
            )
            self.stop()
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
        if papers.empty:
            print(
                f'[bold {salmon}]Could not find any suggested paper with query: "{input_string}"'
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
        if savepath:
            self.suggestions.to_csv(savepath)


if __name__ == "__main__":
    import refy

    refy.settings.TEST_MODE = False

    refy.set_logging("DEBUG")

    # query("locomotion control mouse steering goal directed")
    query(
        "neuron gene expression", N=20, since=2015, to=2018,
    )

    # query_author("Gary Stacey")
    # query_author("Gary  Stacey")
    # query_author("Carandini M.")
