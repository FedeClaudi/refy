from loguru import logger
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import pandas as pd

from .input import load_user_input, augment_data
from ._dbase import load_abstracts, load_database


"""
    - parse + augment user's papers
    - construct similarity score for user's papers
    - select N best fits to present to the user
    - output them in a nice way
"""


def compute_similarity_matrix(papers):
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

    abstracts = load_abstracts(papers["ids"])

    # create embedding
    # Define a TF-IDF Vectorizer Object. Remove all english stop words such as 'the', 'a'
    tfidf = TfidfVectorizer(stop_words="english")

    # Construct the required TF-IDF matrix by fitting and transforming the data
    logger.debug("Fitting TfidfVectorizer model")
    tfidf_matrix = tfidf.fit_transform(abstracts)

    # compute cosine similarity
    similarity = linear_kernel(tfidf_matrix, tfidf_matrix)
    logger.debug(f"Created similarity matrix with shape: {similarity.shape}")

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
    indices = pd.Series(papers.index, index=papers["title"]).drop_duplicates()

    suggestions = []
    for user_paper in papers.loc[papers.input].title:
        idx = indices[user_paper]

        # Get the pairwsie similarity scores of all papers with that paper
        sim_scores = list(enumerate(similarity[idx]))

        # Sort the papers based on the similarity scores
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

        # Get the scores of the 10 most similar papers
        sim_scores = sim_scores[0:N]

        # Get the paper indices
        best_indices = [i[0] for i in sim_scores]

        suggestions.append(papers["title"].iloc[best_indices])


def suggest(user_papers):
    """
        Suggest new relevant papers based on the user's
        library.

        Arguments:
            user_papers: str, path. Path to a .bib file with user's papers info
    """
    # Load and augment user's papers
    user_papers = load_user_input(user_papers)
    user_papers = augment_data(user_papers)
    user_papers["input"] = True
    logger.debug(f"Loaded {len(user_papers)} USER papers")

    # load database papers
    database_papers = load_database()
    database_papers["input"] = False
    logger.debug(f"Loaded {len(database_papers)} DATABASE papers")

    # concatenate
    papers = pd.concat([user_papers, database_papers])

    # compute similarity matrix
    similarity = compute_similarity_matrix(papers)

    # select most similar new papers
    get_suggestions(papers, similarity)
