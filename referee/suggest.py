from loguru import logger
from rich import print
import pandas as pd
import numpy as np

from referee.input import load_user_input
from referee.database import load_abstracts, load_database
from referee.progress import suggest_progress
from referee.settings import use_n_papers
from referee.utils import to_table
from referee.doc2vec import load_model


class suggest:
    def __init__(self, user_papers, N=10):
        """
            Suggest new relevant papers based on the user's
            library.

            Arguments:
                user_papers: str, path. Path to a .bib file with user's papers info
                N: int. Number of papers to suggest
        """
        with suggest_progress as progress:
            self.progress = progress
            self.n_completed = 0
            self.task_id = self.progress.add_task(
                "Suggesting papers..",
                start=True,
                total=5,
                current_task="Loading database papers",
            )

            # load d2v model
            self.d2v = load_model()

            # load metadata
            self.load_data(user_papers)

            # compute similarity matrix
            self.compute_similarity_matrix()

            # get suggestions
            self.get_suggestions(N=N)

    @property
    def n_abstracts(self):
        return len(self.abstracts)

    @property
    def n_papers(self):
        return len(self.papers)

    @property
    def n_user_papers(self):
        return len(self.user_papers)

    @property
    def n_database_papers(self):
        return self.n_papers - self.n_user_papers

    @property
    def user_papers(self):
        return self.papers.loc[self.papers.input]

    @property
    def database_papers(self):
        return self.papers.loc[not self.papers.input]

    def paper_abstract(self, paper_id):
        """
            Returns a paper's abstract given the paper id string
        """
        try:
            self.abstracts[paper_id]
        except KeyError:
            raise ValueError(
                f"Could not find abstract for paper with ID: {paper_id}"
            )

    def _progress(self, task_name):
        """
            Update progress bar showing analysis status
        """
        self.n_completed += 1
        self.progress.update(
            self.task_id, current_task=task_name, completed=self.n_completed
        )

    def load_data(self, user_papers):
        """
            Load papers metadata for user papers
            and database papers

            Arguments:
                user_papers: str, path. Path to a .bib file with user's papers info
        """

        # load database papers
        self._progress("Loading database papers",)
        database_papers = load_database()

        # load abstracts
        abstracts = load_abstracts()

        # Load and augment user's papers
        self._progress("Loading user papers",)
        user_papers = load_user_input(user_papers)
        user_papers["input"] = True

        # add user papers' abstracts to abstracts corpus
        self.abstracts = {
            **abstracts,
            **{p.title: p.abstract for i, p in user_papers.iterrows()},
        }

        # Select only a random sample of the whole database
        if use_n_papers > 0:
            database_papers = database_papers.sample(use_n_papers)
            logger.debug(
                f"Kept only {len(database_papers)} databse papers as requested by user"
            )

        # concatenate user and database papers
        self.papers = pd.concat(
            [user_papers, database_papers], sort=False
        ).copy()

        # remove duplicates
        self.papers = self.papers.drop_duplicates(subset="id", keep="first")

        # keep only papers that have an abstract
        self.papers = self.papers.loc[
            self.papers["id"].isin(self.abstracts.keys())
        ]
        self.papers.reset_index()

        # keep only abstracts for papers we've kept (if use_n_papers > 0)
        self.abstracts = {
            ID: self.abstracts[ID] for ID in self.papers["id"].values
        }

        logger.debug(
            f"Loaded {self.n_papers} papers (of which {self.n_user_papers} are user's) and {self.n_abstracts} abstracts"
        )
        if self.n_abstracts != self.n_papers:
            raise ValueError(
                "Error while loading data. Expected same number of papers and abstracts."
                f"Instead {self.n_papers} papers and {self.n_abstracts} abstracts were found"
            )

    def suggest_for_paper(self, user_paper, paper_idx):
        """
            Finds the best matches for a single paper

            Arguments:
                paper_idx: int. Index of the paper to use
        """
        # Get the pairwsie similarity scores of all papers wrt the current one
        # get non-zero entries in similarity matrix
        indexes = self.similarity[paper_idx].indices

        # sort entries by similarity
        try:
            srtd = indexes[
                np.argsort(self.similarity[paper_idx, indexes.data].data)[::-1]
            ][:200]
        except IndexError:
            srtd = []

        # select N best matches not already in user's library
        selected_titles = [self.papers.title.values[idx] for idx in srtd]
        selected = self.papers.loc[self.papers.title.isin(selected_titles)]

        if not len(selected):
            logger.debug(
                f'Could not find any suggested papers for paper: "{user_paper.title}" '
                f"with abstract:{self.paper_abstract(user_paper.title)}"
            )
            return None

        return selected

    def get_suggestions(self, N=10):
        """
            Finds the papers from the database that are not in the user's
            library but are most similar to the users papers.
            For each user paper, get the N most similar papers, then get
            the papers that came up most frequently across all user papers.
            

            Arguments:
                N: int, number of best papers to keep
        """
        logger.debug(f"Getting suggestions for {self.n_user_papers} papers")

        # progress bar
        self._progress("Finding matches")
        select_task = self.progress.add_task(
            "Selecting best matches...",
            start=True,
            total=self.n_user_papers,
            current_task="working...",
        )

        # find best matches for each paper
        suggestions = []
        for n, (idx, user_paper) in enumerate(self.papers.iterrows()):
            # only use papers from the user's library
            if not user_paper.input:
                continue

            # get best matches for this paper
            suggested = self.suggest_for_paper(user_paper, idx)
            if suggested is not None:
                suggestions.append(suggested)

            self.progress.update(select_task, completed=n)

            # if n == 5:
            #     break

        self.progress.remove_task(select_task)
        self.progress.remove_task(self.task_id)

        logger.debug(f"Found suggestions for {len(suggestions)} papers")

        # collate suggestions
        suggestions = pd.concat(suggestions)

        # remove papers in user database
        suggestions = suggestions.loc[suggestions.input == False]

        # sort by frequency of occurrence
        suggestions["count"] = suggestions["title"].value_counts()
        suggestions = suggestions.sort_values("count").reset_index()

        # print
        print(to_table(suggestions[:20]))
