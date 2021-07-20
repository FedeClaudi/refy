from sklearn.feature_extraction.text import TfidfVectorizer
from loguru import logger


def fit_tfidf(preprints_abstracts, user_abstracts):
    """
        Fits tf-idf to all data and estimates cosine similarity
    """
    logger.debug("Fitting TF-IDF model")
    vectorizer = TfidfVectorizer()

    # combine all abstracts
    IDs = list(preprints_abstracts.keys()) + list(user_abstracts.keys())
    abstracts = list(preprints_abstracts.values()) + list(
        user_abstracts.values()
    )

    # fit (includes pre processing)
    vectors = vectorizer.fit_transform(abstracts).toarray()

    return {k: v for k, v in zip(IDs, vectors)}
