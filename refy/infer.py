from sklearn.feature_extraction.text import TfidfVectorizer
from loguru import logger


def fit_tfidf(preprints_abstracts, user_abstracts):
    """
        Fits tf-idf to all data and estimates cosine similarity
    """
    logger.debug("Fitting TF-IDF model")

    # combine all abstracts
    IDs = list(preprints_abstracts.keys()) + list(user_abstracts.keys())
    abstracts = list(preprints_abstracts.values()) + list(
        user_abstracts.values()
    )

    # create TF-IDF model
    model = TfidfVectorizer(strip_accents="ascii", stop_words="english")

    # fit (includes pre processing)
    model.fit(abstracts)
    vectors = model.transform(abstracts).toarray()

    return {k: v for k, v in zip(IDs, vectors)}
