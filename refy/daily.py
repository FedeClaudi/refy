from datetime import datetime, timedelta
from loguru import logger
import math
import pandas as pd
from numpy import dot
from numpy.linalg import norm
from myterial import orange, green
from pathlib import Path
import sys
from crontab import CronTab


sys.path.append("./")

from refy.utils import check_internet_connection, request
from refy.settings import fields_of_study, base_dir
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
    def __init__(self, user_data_filepath, html_path=None, N=10):
        """
            Get biorxiv preprints released in the last 24 hours
            and select the top N matches based on user inputs
            
            Arguments:
                user_data_filepath: str, Path. Path to user's .bib fole
                html_path: str, Path. Path to a .html file 
                    where to save the output
                N: int. Number of papers to return
        """
        logger.debug("\n\nStarting biorxiv daily search")
        self.start(text="Getting daily suggestions")

        SimpleQuery.__init__(self, html_path=html_path)
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


def setup(user, python_path, bibfile, N, outputpath):
    """
        Sets up crontab schedule to run Daily every day

        Arguments:
            user: str. user name
            python_path: str. path to python installation to use
            N: int. Number of suggestions to return
            outputpath: str. Path to .HTML to save the results to
    """
    if not Path(python_path).exists():
        raise FileNotFoundError(
            f"Could not find .bib file to use for daily searches: {python_path}"
        )

    # get refy installation path
    refy_folder = Path(__file__).parent
    assert (refy_folder / "cli.py").exists(), "could not find refy's cli file"
    logger.debug(f"Refy package folder: {refy_folder}")

    # get out file
    out_file = base_dir / "daily.txt"
    if out_file.exists():
        out_file.unlink()

    # create crontab command
    command = f"{python_path} {refy_folder}/cli.py daily {bibfile} -N {N} -o {outputpath} --d"
    command += f" >> {out_file}"  # output file for crontab

    # setup cronotab job
    logger.debug(f"Setting up crontab for user: {user}")
    cron = CronTab(user=user)

    logger.debug(f"setting up crontab jobs with command:\n     {command}")
    job = cron.new(command=command, comment="refy_daily")
    job.setall("* 10 * * *")  # run at 10 AM every day
    cron.write()

    jobs = "\n".join([str(c) for c in cron])
    logger.debug(f"Crontab jobs:\n{jobs}")


def stop(user):
    """
        Removes crontab job for refy
    """
    cron = CronTab(user=user)
    cron.remove_all(comment="refy_daily")
    cron.write()

    # log jobs
    jobs = "\n".join([str(c) for c in cron])
    logger.debug(f"Crontab jobs:\n{jobs}")


if __name__ == "__main__":
    import refy

    refy.set_logging("DEBUG")
    d = Daily(refy.settings.example_path, html_path="test.html")

    # setup(
    #     "federico claudi",
    #     "/Users/federicoclaudi/miniconda3/envs/ref/bin/python",
    #     "test.bib",
    # )
    # stop("federico claudi")

    """
        example:

        sudo refy setup-daily "federico claudi" "/Users/federicoclaudi/miniconda3/envs/ref/bin/python" "/Users/federicoclaudi/Documents/Github/referee/test.bib" -N 20 -o /Users/federicoclaudi/Desktop/refy.html

        to stop:

        sudo refy stop-daily "federico claudi"

    """
