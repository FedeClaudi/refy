from sklearn.feature_extraction.text import TfidfVectorizer
from loguru import logger

from .settings import vocabulary_size


def get_tfidf_matrix(abstracts):
    """
        Given a list of abstracts it returns a sparse matrix
        with the tf-idf vectors. Uses settings specified in settings.py

        Create a Frequency-Inverse Document Frequency (TF-IDF) embedding
        (https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
        to represent each papers' abstract as a vector
        
        Arguments:
            abstracts: list of str. Papers abstracts

        Returns:
            tfidf_matrix: sparse matrix with tf-idf vectors.
                shape: n abstracts x vocab. size
    """
    logger.debug(f"Fitting tf-idf with {vocabulary_size} words")
    tfidf = TfidfVectorizer(
        stop_words="english", max_features=vocabulary_size,
    )
    tfidf_matrix = tfidf.fit_transform(abstracts)
    logger.debug(f"Created tf-idf matrix with shape: {tfidf_matrix.shape}")

    return tfidf_matrix
