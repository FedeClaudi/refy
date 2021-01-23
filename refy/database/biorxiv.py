from loguru import logger
import pandas as pd
import sys
import math

sys.path.append("./")

from refy.utils import (
    request,
    to_json,
)
from refy.settings import (
    fields_of_study,
    biorxiv_start_date,
    biorxiv_end_date,
    biorxiv_abstracts_path,
    biorxiv_database_path,
)
from refy.progress import progress
from refy.utils import raise_on_no_connection

"""
    Code to download papers metadata from biorxiv's API:
        https://api.biorxiv.org/
    and integrate it into refy's database
"""


# ---------------------------- make biorxiv dbase ---------------------------- #

base_url = "https://api.biorxiv.org/details/biorxiv/"


@raise_on_no_connection
def make_biorxiv_database():
    """
        Download and clean up papers metadata from biorxiv and save them to file
    """
    logger.debug(
        f'Downloading papers metadata from biorxiv: "{biorxiv_start_date}" -> "{biorxiv_end_date}"'
    )

    # first, get an idea of how many papers there are
    req = request(base_url + f"{biorxiv_start_date}/{biorxiv_end_date}")
    tot = req["messages"][0]["total"]
    logger.debug(f"Downloading metadata for {tot} papers")

    # then iterate to get 100 papers metadata at a time
    metadata = []
    abstracts = {}
    cursor = 0
    with progress:
        tsk = progress.add_task(
            "Downloading metadata from biorxiv.org", total=tot
        )

        while (
            cursor < int(math.ceil(tot / 100.0)) * 100
        ):  # round up to ensure all papers are downloaded
            # download
            data = request(
                base_url + f"{biorxiv_start_date}/{biorxiv_end_date}/{cursor}"
            )["collection"]
            cursor += 100

            # keep only relevant papers/info
            papers = pd.DataFrame(data)
            if papers.empty:
                break

            papers = papers[
                ["doi", "title", "authors", "date", "category", "abstract"]
            ]
            papers = papers.loc[
                papers.category.str.lower().isin(fields_of_study)
            ]

            # fix ID
            papers["id"] = papers["doi"]
            papers = papers.drop_duplicates(subset="id")

            # fix year of publication
            papers["year"] = [
                p.date.split("-")[0] for i, p in papers.iterrows()
            ]
            del papers["date"]

            # separate abstracts
            abstracts.update(
                {paper.id: paper.abstract for i, paper in papers.iterrows()}
            )
            del papers["abstract"]

            metadata.append(papers)

            # update progress
            progress.update(tsk, completed=cursor)

        # collate data and save
        papers = pd.concat(metadata)
        papers = papers.loc[papers["id"].isin(abstracts.keys())]
        papers = papers.drop_duplicates(subset="id")

        logger.debug(
            f"Found metadata for {len(papers)} relevant papers [{len(abstracts)} abstracts]"
        )

        to_json(abstracts, biorxiv_abstracts_path)
        papers.to_feather(biorxiv_database_path)


if __name__ == "__main__":
    make_biorxiv_database()
