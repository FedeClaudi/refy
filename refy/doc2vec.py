from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.parsing.preprocessing import (
    remove_stopwords,
    stem,
    preprocess_string,
    strip_multiple_whitespaces,
    strip_punctuation,
)
import logging
from loguru import logger
import sys
import multiprocessing

sys.path.append("./")

from refy.settings import base_dir, d2v_model_path
from refy.database import load_abstracts
from refy.progress import progress


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
        # clean up input
        words = _preprocess_string(input_abstract)

        # infer
        return self.model.infer_vector(words, epochs=100)

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

        # get N best matches
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


# --------------------------------- training --------------------------------- #
def _preprocess_string(string):
    """
        Cleans up (e.g. strips punctuation) and tokenizes an input string
        to preprare for d2v processing
    """
    string = string.lower()
    filters = (
        remove_stopwords,
        stem,
        strip_multiple_whitespaces,
        strip_punctuation,
    )
    return preprocess_string(string, filters)


class Corpus:
    def __init__(self):
        """
            Class to pre-process and iterate over training data for d2v
        """
        self.training_data = load_abstracts()

    def __iter__(self):
        for ID, doc in self.training_data.items():
            yield TaggedDocument(words=_preprocess_string(doc), tags=[ID])


def train_doc2vec_model(n_epochs=50, vec_size=500, alpha=0.025):
    """
        Trains a doc2vec model from gensim for embedding and similarity 
        evaluation of paper abstracts.

        See: https://radimrehurek.com/gensim/models/doc2vec.html

        Arguments:
            n_epochs: int. Numberof epochs for training
            vec_size: int. Dimensionality of the feature vectors
            alpha: float. The initial learning rate
    """
    logger.debug("Training doc2vec model")
    logging.basicConfig(
        format="%(asctime)s : %(levelname)s : %(message)s", level=logging.INFO
    )

    # get training data
    training_data = Corpus()

    # create model
    logger.debug("Generating vocab")
    model = Doc2Vec(
        vec_size=vec_size,
        alpha=alpha,
        sample=0,
        dm=1,
        hs=0,
        workers=multiprocessing.cpu_count(),
    )
    model.build_vocab(
        training_data, progress_per=25000,
    )

    # train
    logger.debug("Training")
    with progress:
        model.train(
            training_data, total_examples=model.corpus_count, epochs=n_epochs,
        )

    # save trained
    model.save(str(base_dir / "d2v_model.model"))
    logger.debug(f"Model Saved at: {base_dir/'d2v_model.model'}")


if __name__ == "__main__":
    train_doc2vec_model()
