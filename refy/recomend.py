from datetime import datetime, timedelta
import pandas as pd
from loguru import logger
from pathlib import Path
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from myterial import orange, green

from refy.download import download_arxiv, download_biorxiv
from refy.utils import date_to_string, open_in_browser
from refy.results import Results
from refy.input import load_user_input
from refy.keywords import Keywords, get_keywords_from_text
from refy.infer import fit_tfidf


class Recomender(Results):
    def __init__(
        self,
        user_data_filepath,
        html_path=None,
        N=10,
        show_html=True,
        n_days=2,
    ):
        """
            Get arxiv & biorxiv preprints released in the last n days
            and select the top N matches based on user inputs
            
            Arguments:
                user_data_filepath: str, Path. Path to user's .bib file
                html_path: str, Path. Path to a .HTML to save formatted
                    results to.
                N: int. Number of papers to return
                show_html: bool. If true and a html_path is passed, it opens
                    the html in the default web browser
                n_days: int. Default = 1. Number of days from preprints are to be taken (e.g. 7 means from the last week)
        """
        if not Path(user_data_filepath).exists():
            raise FileExistsError(
                f"bib file does not exist: {user_data_filepath}"
            )
        logger.debug("\n\nStarting biorxiv & arxiv daily search")
        self.n_days = n_days
        self.html_path = html_path
        self.N = N
        self.results = Results()
        self.keywords = None

        # -- SETUPS
        # download preprints
        logger.debug("Downloading data from arxiv & biorxiv")
        self.papers, self.abstracts = self.fetch_preprints()

        # load user data
        logger.debug("Loading user papers")
        self.user_papers = load_user_input(user_data_filepath)
        self.user_abstracts = {
            p["id"]: p.abstract for i, p in self.user_papers.iterrows()
        }

        logger.debug(
            f"Final papers count: {len(self.papers)} preprints and {len(self.user_papers)} user papers"
        )

        # -- ANALYSIS
        self.fit()

        # get keyords
        logger.debug("Getting keywords")
        self.get_keywords(self.user_papers)

        # -- RESULTS
        # print
        today = date_to_string(datetime.today())
        self.results.print(
            text=f"[{orange}]:calendar:  Daily suggestions for: [{green} bold]{today}\n\n"
        )

        # save to html
        self.results.to_html(
            html_path,
            text=f"[{orange}]:calendar:  Daily suggestions for: [{green} bold]{today}\n\n",
        )

        # open html in browser
        if self.html_path is not None and show_html:
            open_in_browser(self.html_path)

    # ------------------------------ data extraction ----------------------------- #
    def fetch_preprints(self):
        """
            Downloads preprints from the online databases
        """
        # get dates
        today = date_to_string(datetime.today())
        start_date = date_to_string(datetime.now() - timedelta(self.n_days))

        # download
        papers = pd.concat(
            [
                download_arxiv(today, start_date),
                download_biorxiv(today, start_date),
            ]
        )

        # cleanup
        papers = papers[
            [
                "id",
                "doi",
                "title",
                "authors",
                "date",
                "category",
                "abstract",
                "source",
                "url",
            ]
        ]

        # fix year of publication
        papers["year"] = [
            p.date.split("-")[0] if isinstance(p.date, str) else "2021"
            for i, p in papers.iterrows()
        ]
        del papers["date"]

        # separate abstracts
        abstracts = {
            paper.id: paper.abstract for i, paper in papers.iterrows()
        }
        del papers["abstract"]

        # make sure everything checks out
        papers = papers.loc[papers["id"].isin(abstracts.keys())]
        papers = papers.drop_duplicates(subset="id")

        return papers, abstracts

    # ------------------------------- data analysis ------------------------------ #
    def fit(self):
        """
            Fits tf-idf to data and estimates pairwise distance between all user
            and preprint papers, then selects best results
        """
        embeddings = fit_tfidf(self.abstracts, self.user_abstracts)

        # compute cosine distances (average across all input user papers)
        logger.debug("Estimating distances")
        distances = {ID: [] for ID in self.abstracts.keys()}
        for uID in self.user_abstracts.keys():
            for ID in self.abstracts.keys():
                distances[ID].append(
                    cosine_similarity(
                        embeddings[uID].reshape(1, -1),
                        embeddings[ID].reshape(1, -1),
                    )
                )
        # distances = {ID: d / len(self.papers) for ID, d in distances.items()}
        distances = {ID: np.median(d) for ID, d in distances.items()}

        # sort and truncate
        self.results.fill(self.papers, N=len(distances), ignore_authors=True)
        scores = self.results.suggestions.set_score(distances.values())
        self.results.suggestions.truncate(self.N)

        logger.debug(f"Recomended papers scores: {scores}")

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
        self.results.keywords = Keywords(keywords)
