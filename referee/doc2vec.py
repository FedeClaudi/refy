from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.parsing.porter import PorterStemmer
from gensim.parsing.preprocessing import remove_stopwords
from gensim.utils import simple_preprocess
from nltk.tokenize import word_tokenize
from loguru import logger
import sys
import re

sys.path.append("./")

from referee.settings import base_dir, d2v_model_path, remote_url_base
from referee.database import load_abstracts
from referee.progress import progress
from referee.utils import (
    raise_on_no_connection,
    retrieve_over_http,
)
import multiprocessing

# for gensim logging
import logging


class D2V:
    def __init__(self):
        """
            Class to load and use Doc2Vec model at inference
        """
        self.model = load_model()

    def _infer(self, input_abstract):
        """ 
            Inference part of the prediction of best matches.
            Convertes an input abstract string into its vector representation

            Arguments:
                input_abstract: str. Input abstract

            Returns:
                inferred_vector: np.ndarray
        """
        # convert input to TaggedDocument
        input_abstract = TaggedDocument(
            words=word_tokenize(input_abstract.lower()), tags=[-1]
        )

        # infer
        return self.model.infer_vector(input_abstract.words)

    def predict(self, input_abstract, N=20):
        """
            Predict the best mach from the input abstract
            from the database abstracts according to the d2v model.

            Arguments:
                input_abstract: str. Input abstract
                N: int. Number of best matches to keep

            Returns:
                matches_id: list. List of indices for the best matches.
                    The indices correspond to the 
        """
        inferred_vector = self._infer(input_abstract)

        # get best match (second prediction)
        matches = self.model.docvecs.most_similar([inferred_vector], topn=N)
        matches_id = [m[0] for m in matches]

        return matches_id


# ----------------------------------- utils ---------------------------------- #
def load_model():
    """
        Loads a previously saved model
    """
    logger.debug("Loading pre-trained doc2vec model")

    return Doc2Vec.load(str(d2v_model_path))


@raise_on_no_connection
def download():
    """
        Downloads a pre-trained d2v model from the remote url
    """
    logger.debug("Downloading trained d2v model from web")

    data = {
        "model": (remote_url_base + "d2v_model.model", d2v_model_path),
        "docvecs": (
            remote_url_base + "d2v_model.model.docvecs.vectors_docs.npy",
            d2v_model_path.parent / "d2v_model.model.docvecs.vectors_docs.npy",
        ),
    }

    # download and extract
    for name, (url, path) in data.items():
        logger.debug(f"Downloading and extracting: {name}")
        retrieve_over_http(url, path)


# ------------------------------- preprocessing ------------------------------ #


class Corpus:
    def __init__(self, training_data):
        """
            Class to pre-process and iterate over training data for d2v
        """
        self.training_data = training_data

    def __iter__(self):
        p = PorterStemmer()
        for n, doc in enumerate(self.training_data):
            doc = re.sub(
                r"http\S+", "", doc, flags=re.MULTILINE
            )  # remove web addresses

            # remove symbols
            for symbol in (r"'", r"\(", r"\)", r"\=", r"\#"):
                doc = re.sub(symbol, "", doc)

            # clean up
            doc = remove_stopwords(doc)
            doc = p.stem_sentence(doc)
            words = simple_preprocess(doc, deacc=True)
            yield TaggedDocument(words=words, tags=[n])


# --------------------------------- training --------------------------------- #


def train_doc2vec_model(n_epochs=50, vec_size=250, alpha=0.025):
    """
        Trains a doc2vec model from gensim for embedding and similarity 
        evaluation of paper abstracts.

        See: https://radimrehurek.com/gensim/models/doc2vec.html

        Arguments:
            model: Doc2Vec. Optional, if None a new model is created (which is very slow).
                Passing a loaded model skips the generate_vocab steps which is slow.
            n_epochs: int. Numberof epochs for training
            vec_size: int. Dimensionality of the feature vectors
            alpha: float. The initial learning rate
    """
    logger.debug("Training doc2vec model")
    logging.basicConfig(
        format="%(asctime)s : %(levelname)s : %(message)s", level=logging.INFO
    )

    # get training data
    training_data = Corpus(list(load_abstracts().values()))
    training_data.save()

    # create model
    logger.debug("Generating vocab")
    model = Doc2Vec(
        vec_size=vec_size,
        alpha=alpha,
        min_alpha=0.00025,
        min_count=2,
        sample=0,
        dm=0,
        hs=0,
        negative=5,
        workers=multiprocessing.cpu_count(),
    )
    model.build_vocab(
        training_data, progress_per=10000,
    )

    # train
    logger.debug("Training")
    with progress:
        model.train(
            training_data, total_examples=model.corpus_count, epochs=n_epochs,
        )

    # save trained
    model.save(str(base_dir / "d2v.model"))
    logger.debug(f"Model Saved at: {base_dir/'d2v.model'}")


if __name__ == "__main__":
    train_doc2vec_model()
