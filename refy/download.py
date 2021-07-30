from loguru import logger
import xmltodict
import pandas as pd
import math
from time import sleep

from refy.web_utils import request, raise_on_no_connection
from refy.utils import string_to_date
from refy.settings import biorxiv_categories, arxiv_categories

biorxiv_base_url = "https://api.biorxiv.org/details/biorxiv/"
arxiv_base_url = "http://export.arxiv.org/api/query?search_query="


def download_biorxiv(today, start_date):
    """
        Downloads latest biorxiv's preprints, hot off the press
    """
    req = request(biorxiv_base_url + f"{start_date}/{today}", to_json=True)
    tot = req["messages"][0]["total"]
    logger.debug(
        f"Downloading metadata for {tot} papers from bioarxiv || {start_date} -> {today}"
    )

    # loop over all papers
    papers, cursor = [], 0
    while cursor < int(math.ceil(tot / 100.0)) * 100:
        # download
        papers.append(
            request(
                biorxiv_base_url + f"{start_date}/{today}/{cursor}",
                to_json=True,
            )["collection"]
        )
        cursor += 100
        logger.debug(f"     downloaded {cursor/tot * 100:.0f}%")

    # clean up
    papers = pd.concat([pd.DataFrame(ppr) for ppr in papers])
    papers["source"] = "biorxiv"
    papers = papers.loc[papers.category.isin(biorxiv_categories)]
    papers["id"] = papers["doi"]

    logger.debug(f"kept {len(papers)} preprints from biorxiv")
    return papers


@raise_on_no_connection
def download_arxiv(today, start_date):
    """
            get papers from arxiv
        """
    logger.debug(f"downloading papers from arxiv. || {start_date} -> {today}")
    today, start_date = string_to_date(today), string_to_date(start_date)

    N_results = 500  # per request
    url_end = f"&max_results={N_results}&start=START&sortBy=submittedDate&sortOrder=descending"
    query = "".join([f"cat:{cat}+OR+" for cat in arxiv_categories])[:-4]

    count = 0
    papers, dates = [], []
    while True:
        logger.debug(
            f"     sending biorxiv request with start index: {count} (requesting {N_results} papers)"
            + f' | collected {len(papers)} papers so far | min date: {min(dates) if dates else "nan"}'
        )
        # download arxiv papers
        url = arxiv_base_url + query + url_end.replace("START", str(count))
        logger.debug(f"         request url:\n{url}")
        data_str = request(url)

        # parse
        dict_data = xmltodict.parse(data_str)
        try:
            downloaded = dict_data["feed"]["entry"]
        except KeyError:
            # raise ValueError('Failed to retrieve data from arxiv, likely an API limitation issue, wait a bit.')
            logger.debug(
                " !!! Failed to retrieve data from arxiv, likely an API limitation issue, wait a bit. !!!"
            )
            logger.debug(dict_data["feed"])
            break
        else:
            logger.debug(
                f"     downloaded {len(downloaded)} papers - filtering"
            )

        for paper in downloaded:
            if isinstance(paper, str):
                raise ValueError(
                    f"Querying Arxiv API returned a string: {paper}"
                )
            if isinstance(paper["category"], list):
                paper["category"] = paper["category"][0]["@term"]
            else:
                paper["category"] = paper["category"]["@term"]

        # store results
        _dates = [
            string_to_date(paper["published"].split("T")[0])
            for paper in downloaded
        ]
        papers.extend(downloaded)
        dates.extend(_dates)

        if min(dates) < start_date:
            break
        else:
            sleep(20)  # to avoid exceeding API restrictions
            count += len(papers)

    # keep only papers in the right date range
    papers = [
        paper for date, paper in zip(dates, papers) if date >= start_date
    ]

    # organize in a dataframe and return
    _papers = dict(
        id=[], title=[], published=[], authors=[], abstract=[], url=[]
    )
    for paper in papers:
        _papers["id"].append(paper["id"])
        _papers["title"].append(paper["title"])
        _papers["published"].append(paper["published"].split("T")[0])
        _papers["abstract"].append(paper["summary"])
        _papers["url"].append(paper["link"][0]["@href"])

        if isinstance(paper["author"], list):
            _papers["authors"].append(
                [auth["name"] for auth in paper["author"]]
            )
        else:
            _papers["authors"].append(paper["author"])  # single author

    papers = pd.DataFrame(_papers)
    papers["source"] = "arxiv"

    logger.debug(f"Downloaded {len(papers)} preprints from arxiv")
    return papers
