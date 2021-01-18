from datetime import datetime, timedelta
from loguru import logger
import math
import pandas as pd
from numpy import dot
from numpy.linalg import norm
from myterial import orange, green

from refy.utils import check_internet_connection, request
from refy.settings import fields_of_study
from refy.input import load_user_input
from refy._query import SimpleQuery
from refy.authors import Authors

from refy.doc2vec import D2V

base_url = "https://api.biorxiv.org/details/biorxiv/"


def cosine(v1, v2):
    """
        Cosine similarity between two vectors
    """
    return dot(v1, v2) / (norm(v1) * norm(v2))


class Daily(SimpleQuery):
    def __init__(self):
        """
            Script that can be run daily to check relevant papers
            published on biorxiv in the last 24 hours.
        """
        SimpleQuery.__init__(self)
        logger.debug("Launching daily biorxiv check")
        self.model = D2V()

    def run(self, user_data_filepath):
        self.start(text="Getting daily suggestions")

        # get data from biorxiv
        logger.debug("Getting data from biorxiv")
        self.fetch()

        # load user data
        logger.debug("Loading user papers")
        self.user_papers = load_user_input(user_data_filepath)

        # embed biorxiv's papers
        logger.debug("Embedding papers")
        self.papers_vecs = {
            ID: self.model._infer(abstract)
            for ID, abstract in self.abstracts.items()
        }

        # embed user data
        self.user_papers_vecs = {
            p["id"]: self.model._infer(p.abstract)
            for i, p in self.user_papers.iterrows()
        }

        # get suggestions
        self.get_suggestions()

        self.stop()

        today = datetime.today().strftime("%Y-%m-%d")
        self.print(
            text=f"[{orange}]:calendar:  Daily suggestions for: [{green} bold]{today}\n\n"
        )

    def clean(self, papers):
        """
            Cleans up a set of papers

            Arguments:
                papers: pd.DataFrame

            Return:
                papers: cleaned up papers
                abstracts: dict of papers abstracts
        """
        # keep only relevant papers/info
        papers = pd.DataFrame(papers)
        if papers.empty:
            raise ValueError("No papers were downloaded from biorxiv")

        papers = papers[
            ["doi", "title", "authors", "date", "category", "abstract"]
        ]
        papers = papers.loc[papers.category.isin(fields_of_study)]

        # fix ID
        papers["id"] = papers["doi"]
        papers = papers.drop_duplicates(subset="id")

        # fix year of publication
        papers["year"] = [p.date.split("-")[0] for i, p in papers.iterrows()]
        del papers["date"]

        # separate abstracts
        abstracts = {
            paper.id: paper.abstract for i, paper in papers.iterrows()
        }
        del papers["abstract"]

        # make sure everything checks out
        papers = papers.loc[papers["id"].isin(abstracts.keys())]
        papers = papers.drop_duplicates(subset="id")
        papers["source"] = "biorxiv"

        return papers, abstracts

    def fetch(self):
        """
            Downloads latest biorxiv's preprints, hot off the press
        """
        if not check_internet_connection():
            raise ConnectionError(
                "Internet connection needed to download data from biorxiv"
            )

        today = datetime.today().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(1)).strftime("%Y-%m-%d")

        req = request(base_url + f"{yesterday}/{today}")
        tot = req["messages"][0]["total"]
        logger.debug(
            f"Downloading metadata for {tot} papers || {yesterday} -> {today}"
        )

        # loop over all papers
        papers, cursor = [], 0
        while cursor < int(math.ceil(tot / 100.0)) * 100:
            # download
            papers.append(
                request(base_url + f"{yesterday}/{today}/{cursor}")[
                    "collection"
                ]
            )
            cursor += 100

        # clean up and get abstracts
        papers = pd.concat([pd.DataFrame(ppr) for ppr in papers])
        self.papers, self.abstracts = self.clean(papers)
        logger.debug(f"Kept {len(self.papers)} biorxiv papers")

    def get_suggestions(self):
        logger.debug("getting suggestions")

        distances = {ID: 0 for ID in self.papers_vecs.keys()}
        for uID, uvec in self.user_papers_vecs.items():
            for ID, vector in self.papers_vecs.items():
                distances[ID] += cosine(uvec, vector)

        distances = {ID: d / len(self.papers) for ID, d in distances.items()}

        # sort and truncate
        self.fill(self.papers, len(distances), None, None)
        self.suggestions.set_score(distances.values())
        self.suggestions.truncate(10)
        self.authors = Authors(self.suggestions.get_authors())


if __name__ == "__main__":
    import refy

    refy.set_logging("DEBUG")
    d = Daily().run(refy.settings.example_path)