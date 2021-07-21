from sklearn.feature_extraction.text import TfidfVectorizer
from loguru import logger
from nltk import word_tokenize
from nltk.stem import WordNetLemmatizer
import nltk
from nltk.corpus import stopwords

nltk.download("punkt")
nltk.download("wordnet")


# Interface lemma tokenizer from nltk with sklearn
class LemmaTokenizer:
    ignore_tokens = [",", ".", ";", ":", '"', "``", "''", "`"]

    def __init__(self):
        # Download stopwords list
        nltk.download("punkt")
        self.stop_words = set(stopwords.words("english"))

        self.wnl = WordNetLemmatizer()

    def __call__(self, doc):
        return [
            self.wnl.lemmatize(t)
            for t in word_tokenize(doc)
            if t not in self.ignore_tokens
        ]


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

    # Lemmatize the stop words
    tokenizer = LemmaTokenizer()
    token_stop = tokenizer(" ".join(tokenizer.stop_words))

    # create TF-IDF model
    model = TfidfVectorizer(
        strip_accents="ascii", stop_words=token_stop, tokenizer=tokenizer
    )

    # fit (includes pre processing)
    model.fit(abstracts)
    vectors = model.transform(abstracts).toarray()

    return {k: v for k, v in zip(IDs, vectors)}
