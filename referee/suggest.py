from loguru import logger
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import pandas as pd

from .input import load_user_input, augment_data
from ._dbase import load_abstracts, load_database
from .progress import suggest_progress, step_suggest_progress


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
        logger.debug(f"Loaded {len(database_papers)} DATABASE papers")

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
        logger.debug(f"Loaded {len(user_papers)} USER papers")

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

        # create embedding
        # Define a TF-IDF Vectorizer Object. Remove all english stop words such as 'the', 'a'
        tfidf = TfidfVectorizer(stop_words="english")

        # Construct the required TF-IDF matrix by fitting and transforming the data
        self.n_completed = step_suggest_progress(
            self.progress, self.task_id, "Fitting tfidf", self.n_completed
        )
        logger.debug("Fitting TfidfVectorizer model")
        tfidf_matrix = tfidf.fit_transform(abstracts)

        # compute cosine similarity
        self.n_completed = step_suggest_progress(
            self.progress,
            self.task_id,
            "Computing similarity matrix",
            self.n_completed,
        )
        similarity = linear_kernel(tfidf_matrix, tfidf_matrix)
        logger.debug(
            f"Created similarity matrix with shape: {similarity.shape}"
        )

        return similarity

    def get_suggestions(papers, similarity, N=10):
        """
            Finds the papers from the database that are not in the user's
            library but are most similar to the users papers.
            For each user paper, get the N most similar papers, then get
            the papers that came up most frequently across all user papers.
        """
        logger.debug("Getting suggestions")

        # Construct a reverse map of indices and paper titles
        indices = pd.Series(
            papers.index, index=papers["title"]
        ).drop_duplicates()

        suggestions = []
        for user_paper in papers.loc[papers.input].title:
            idx = indices[user_paper]

            # Get the pairwsie similarity scores of all papers wrt the current one
            sim_scores = list(enumerate(similarity[idx]))

            # Sort the papers based on the similarity scores
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

            # Get the scores of the 10 most similar papers
            sim_scores = sim_scores[0:N]

            # Get the paper indices
            best_indices = [i[0] for i in sim_scores]

            suggestions.append(papers["title"].iloc[best_indices])

        # a = 1
