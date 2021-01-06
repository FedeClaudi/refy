from loguru import logger
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import numpy as np

from .input import load_user_input, augment_data
from ._dbase import load_abstracts, load_database
from .progress import suggest_progress, step_suggest_progress
from .settings import n_papers, vocabulary_size
from .utils import cosine_similarities


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
                total=6,
                current_task="Loading database papers",
            )

            # load metadata
            papers = self.load(user_papers)

            # compute similarity matrix
            similarity = self.compute_similarity_matrix(papers)

            # get suggestions
            self.get_suggestions(papers, similarity, N=N)

    def load(self, user_papers):
        """
            Load papers metadata for user papers
            and database papers

            Arguments:
                user_papers: str, path. Path to a .bib file with user's papers info
        """
        # load database papers
        self.n_completed = step_suggest_progress(
            self.progress,
            self.task_id,
            "Loading database papers",
            self.n_completed,
        )
        database_papers = load_database()
        database_papers["input"] = False

        # Load and augment user's papers
        self.n_completed = step_suggest_progress(
            self.progress,
            self.task_id,
            "Loading user papers",
            self.n_completed,
        )
        user_papers = load_user_input(user_papers)
        user_papers = augment_data(user_papers, database_papers)
        user_papers["input"] = True

        # Select only a random sample of the whole database
        if n_papers > 0:
            database_papers = database_papers.sample(n_papers)
            logger.debug(
                f"Kept only {len(database_papers)} databse papers as requested by user"
            )

        # concatenate
        papers = pd.concat([user_papers, database_papers], sort=False)
        return papers

    def compute_similarity_matrix(self, papers):
        """
            Given a dataframe with papers metadata, load the 
            abstract of each paper and use Frequency-Inverse Document Frequency (TF-IDF) embedding
            (https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
            with cosine similarity to create a similarity matrix

            Arguments:
                papers: DataFrame with papers metadata (both user's and database)
        """
        # Load each paper's abstract to create embedding
        logger.debug(f"Loading abstracts for {len(papers)} papers")

        self.n_completed = step_suggest_progress(
            self.progress,
            self.task_id,
            "Loading papers abstracts",
            self.n_completed,
        )
        abstracts = load_abstracts(papers["id"], progress=self.progress)

        # Construct the required TF-IDF matrix by fitting and transforming the data
        self.n_completed = step_suggest_progress(
            self.progress, self.task_id, "Fitting tfidf", self.n_completed
        )
        logger.debug(
            f"Fitting TfidfVectorizer model with {vocabulary_size} words"
        )

        # Define a TF-IDF Vectorizer Object. Remove all english stop words such as 'the', 'a'
        tfidf = TfidfVectorizer(
            stop_words="english",
            strip_accents="ascii",
            max_features=vocabulary_size,
        )
        tfidf_matrix = tfidf.fit_transform(abstracts)
        logger.debug(f"tfidf matrix with shape: {tfidf_matrix.shape}")

        # compute cosine similarity
        self.n_completed = step_suggest_progress(
            self.progress,
            self.task_id,
            "Computing similarity matrix",
            self.n_completed,
        )
        similarity = cosine_similarities(tfidf_matrix.T)
        logger.debug(
            f"Created similarity matrix with shape: {similarity.shape}"
        )

        return similarity

    def suggest_for_paper(self, papers, paper_idx, similarity):
        """
            Finds the best matches for a single paper

            Arguments:
                papers: DataFrame with papers metadata (both user's and database)
                paper_idx: int. Index of the paper to use
                similarity: sparse matrix with cosine similarity of all papers
        """
        # Get the pairwsie similarity scores of all papers wrt the current one
        # get non-zero entries in similarity matrix
        indexes = similarity[paper_idx].indices
        values = [similarity[paper_idx, idx] for idx in indexes]

        # sort entries by similarity
        srtd = indexes[np.argsort(values)[::-1]]

        # select N best matches not already in user's library
        selected_titles = [
            self.lookup[idx] for idx in srtd if not self.lookup_input[idx]
        ]

        selected = papers.loc[papers.title.isin(selected_titles)]

        if not len(selected):
            logger.debug(
                f"Could not find any suggested papers for paper: {papers.title.values[paper_idx]}"
            )

        return selected

    def get_suggestions(self, papers, similarity, N=10):
        """
            Finds the papers from the database that are not in the user's
            library but are most similar to the users papers.
            For each user paper, get the N most similar papers, then get
            the papers that came up most frequently across all user papers.
            

            Arguments:
                N: int, number of best papers to keep
                papers: DataFrame with papers metadata (both user's and database)
                similarity: sparse matrix with cosine similarity of all papers
        """
        logger.debug("Getting suggestions")

        # get lookups for idx -> title and idx -> is input
        papers = papers.reset_index()
        self.lookup = {i: t for i, t in zip(papers.index, papers.title)}
        self.lookup_input = {
            i: inp for i, inp in zip(papers.index, papers.input)
        }

        # progress bar
        self.n_completed = step_suggest_progress(
            self.progress, self.task_id, "Finding matches", self.n_completed,
        )

        select_task = self.progress.add_task(
            "Selecting best matches...",
            start=True,
            total=len(papers.loc[papers.input]),
            current_task="working...",
        )

        # find best matches for each paper
        suggestions = []
        for n, (paper_idx, user_paper) in enumerate(papers.iterrows()):
            # only use papers from the user's library
            if not user_paper.input:
                continue

            # get best matches for this paper
            suggestions.append(
                self.suggest_for_paper(papers, paper_idx, similarity)
            )
            self.progress.update(select_task, completed=n)

        #  a = 1
