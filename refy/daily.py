from datetime import datetime, timedelta
from loguru import logger
import math
import pandas as pd
from numpy import dot
from numpy.linalg import norm
from myterial import orange, green
import sys
import urllib
import xmltodict


sys.path.append("./")

from refy.utils import check_internet_connection, request, open_in_browser
from refy.settings import fields_of_study, arxiv_categories
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

        logger.debug("\n\nStarting biorxiv & arxiv daily search")
        self.start(text="Getting daily suggestions")

        # get model
        self.model = D2V()

        # get data from biorxiv
        logger.debug("Getting data from biorxiv & arxiv")
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
        papers["server"] = papers["source"]
        papers = pd.DataFrame(papers)
        if papers.empty:
            raise ValueError("No papers were downloaded from biorxiv")

        papers = papers[
            [
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

        # fix ID
        papers["id"] = papers["doi"]
        papers = papers.drop_duplicates(subset="id")

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

    def _download_biorxiv(self, today, start_date):
        """
            Downloads latest biorxiv's preprints, hot off the press
        """
        req = request(base_url + f"{start_date}/{today}")
        tot = req["messages"][0]["total"]
        logger.debug(
            f"Downloading metadata for {tot} papers from bioarxiv || {start_date} -> {today}"
        )

        # loop over all papers
        papers, cursor = [], 0
        while cursor < int(math.ceil(tot / 100.0)) * 100:
            # download
            papers.append(
                request(base_url + f"{start_date}/{today}/{cursor}")[
                    "collection"
                ]
            )
            cursor += 100

        # clean up
        papers = pd.concat([pd.DataFrame(ppr) for ppr in papers])
        papers = papers.loc[papers.category.isin(fields_of_study)]
        papers["source"] = "biorxiv"
        return papers

    def _download_arxiv(self, today, start_date):
        """
            get papers from arxiv
        """
        N_results = 50
        base_url = "http://export.arxiv.org/api/query?search_query="
        url_end = f"&max_results={N_results}&sortBy=submittedDate&sortOrder=descending"
        logger.debug("downloading papers from arxiv.")
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

        # iterate over categories
        papers = []
        for ncat, cat in enumerate(arxiv_categories):
            count = 0  # for pagination

            logger.debug(f" category {cat} ({ncat+1}/{len(arxiv_categories)})")
            # download as many papers as needed to get papers in the right range
            while True:
                url = base_url + f"cat:{cat}" + url_end + f"&start={count}"
                data = urllib.request.urlopen(url)
                data_str = data.read().decode("utf-8")

                # parse
                dict_data = xmltodict.parse(data_str)
                downloaded = dict_data["feed"]["entry"]
                for paper in downloaded:
                    paper["category"] = cat
                papers.extend(downloaded)

                # check if we are out of the date range or get more papers
                last = datetime.strptime(
                    downloaded[0]["published"].split("T")[0], "%Y-%m-%d"
                ).date()
                if last < start_date:
                    break
                count += N_results

        # keep only papers in the right date range
        dates = [
            datetime.strptime(
                paper["published"].split("T")[0], "%Y-%m-%d"
            ).date()
            for paper in papers
        ]
        papers = [
            paper for date, paper in zip(dates, papers) if date >= start_date
        ]

        # organize in a dataframe and return
        _papers = dict(
            doi=[], title=[], published=[], authors=[], abstract=[], url=[]
        )
        for paper in papers:
            _papers["doi"].append(paper["id"])
            _papers["title"].append(paper["title"])
            _papers["published"].append(paper["published"].split("T")[0])
            if isinstance(paper["author"], list):
                _papers["authors"].append(
                    [auth["name"] for auth in paper["author"]]
                )
            else:
                _papers["authors"].append(paper["author"])  # single author
            _papers["abstract"].append(paper["summary"])
            _papers["url"].append(paper["link"][0]["@href"])

        papers = pd.DataFrame(_papers)
        papers["source"] = "arxiv"
        return papers

    def fetch(self):
        """
            Downloads latest biorxiv's and arxiv's preprints
        """
        if not check_internet_connection():
            raise ConnectionError(
                "Internet connection needed to download data from biorxiv"
            )

        # get start and end dates
        today = datetime.today().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(self.n_days)).strftime(
            "%Y-%m-%d"
        )

        # get papers from biorxiv and arxiv
        arxiv_papers = self._download_arxiv(today, start_date)
        biorxiv_papers = self._download_biorxiv(today, start_date)
        papers = pd.concat([biorxiv_papers, arxiv_papers])

        self.papers, self.abstracts = self.clean(papers)
        logger.debug(
            f"Kept {len(self.papers)}/{len(papers)} biorxiv/arxiv papers"
        )

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
