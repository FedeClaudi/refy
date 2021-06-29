from datetime import datetime, timedelta
from loguru import logger
import math
import pandas as pd
from numpy import dot
from numpy.linalg import norm
from myterial import orange, green
import sys


sys.path.append("./")

from refy.utils import check_internet_connection, request, open_in_browser
from refy.settings import fields_of_study
from refy.input import load_user_input
from refy._query import SimpleQuery

from refy.doc2vec import D2V

base_url = "https://api.biorxiv.org/details/biorxiv/"


def cosine(v1, v2):
    """
        Cosine similarity between two vectors
    """
    return dot(v1, v2) / (norm(v1) * norm(v2))


class Daily(SimpleQuery):
    def __init__(
        self,
        user_data_filepath,
        html_path=None,
        N=10,
        show_html=True,
        n_days=1,
    ):
        """
            Get biorxiv preprints released in the last 24 hours
            and select the top N matches based on user inputs
            
            Arguments:
                user_data_filepath: str, Path. Path to user's .bib fole
                html_path: str, Path. Path to a .html file 
                    where to save the output
                N: int. Number of papers to return
                show_html: bool. If true and a html_path is passed, it opens
                    the html in the default web browser
                n_days: int. Default = 1. Number of days from preprints are to be taken (e.g. 7 means from the last week)
        """
        SimpleQuery.__init__(self, html_path=html_path)
        self.n_days = n_days

        logger.debug("\n\nStarting biorxiv daily search")
        self.start(text="Getting daily suggestions")

        # get model
        self.model = D2V()

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
        logger.debug("Retuning suggestions")
        self.get_suggestions(N)

        # get keyords
        logger.debug("Getting keywords")
        self.get_keywords(self.user_papers)
        self.stop()

        # print
        today = datetime.today().strftime("%Y-%m-%d")
        self.print(
            text=f"[{orange}]:calendar:  Daily suggestions for: [{green} bold]{today}\n\n"
        )

        # save to html
        self.to_html(
            text=f"[{orange}]:calendar:  Daily suggestions for: [{green} bold]{today}\n\n",
        )

        # open html in browser
        if self.html_path is not None and show_html:
            open_in_browser(self.html_path)

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
        yesterday = (datetime.now() - timedelta(self.n_days)).strftime(
            "%Y-%m-%d"
        )

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

    def get_suggestions(self, N):
        """
            Computes the average cosine similarity
            between the input user papers and those from biorxiv, 
            then uses the distance to sort the biorxiv papers
            and select the best 10

            Arguments:
                N: int. number of papers to suggest
        """
        logger.debug("getting suggestions")

        # compute cosine distances
        distances = {ID: 0 for ID in self.papers_vecs.keys()}
        for uID, uvec in self.user_papers_vecs.items():
            for ID, vector in self.papers_vecs.items():
                distances[ID] += cosine(uvec, vector)

        distances = {ID: d / len(self.papers) for ID, d in distances.items()}

        # sort and truncate
        self.fill(self.papers, len(distances), None, None, ignore_authors=True)
        self.suggestions.set_score(distances.values())
        self.suggestions.truncate(N)


if __name__ == "__main__":
    import refy

    refy.set_logging("DEBUG")
    d = Daily(refy.settings.example_path, html_path="test.html")
