from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.parsing.porter import PorterStemmer
from gensim.parsing.preprocessing import remove_stopwords
from gensim.utils import simple_preprocess
from nltk.tokenize import word_tokenize
from loguru import logger
import sys
import re

sys.path.append("./")

from referee.settings import base_dir
from referee.database import load_abstracts
from referee.progress import progress

# for gensim logging
import logging

handler = logging.basicConfig(
    format="%(asctime)s : %(levelname)s : %(message)s", level=logging.INFO
)


# ----------------------------------- utils ---------------------------------- #
def load_model(untrained=False):
    """
        Loads a previously saved model
    """
    logger.debug("Loading pre-trained doc2vec model")

    return Doc2Vec.load(
        str(
            base_dir
            / ("d2v.model" if not untrained else "untrained_d2v.model")
        )
    )


def preprocess(data):
    """
        Preprocess a corpus of text for using with a doc2vec
        model.

        Arguments:
            data: list of strings
        
        Returns:
            training_data: list of TaggedDocument objects
    """
    training_data = []
    with progress:
        preprocess_task = progress.add_task(
            "Preprocessing", total=len(data), start=True
        )

        for i, _d in enumerate(data):
            training_data.append(
                TaggedDocument(words=word_tokenize(_d.lower()), tags=[i])
            )
            progress.update(preprocess_task, completed=i)

    progress.remove_task(preprocess_task)
    return training_data


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

    def tolist(self):
        """
            Return the entire dataset as a list
        """
        return [x for x in self]


# --------------------------------- training --------------------------------- #


def train_doc2vec_model(n_epochs=3, vec_size=50, alpha=0.025):
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

    # get training data
    training_data = Corpus(list(load_abstracts().values()))

    # create model
    logger.debug("Generating vocab")
    model = Doc2Vec(
        vec_size=vec_size,
        alpha=alpha,
        min_alpha=0.00025,
        min_count=100,
        sample=1e-05,
        dm=1,
        workers=6,
    )
    model.build_vocab(
        training_data, progress_per=10000,
    )

    # save with vocab
    model.save(str(base_dir / "untrained_d2v.model"))

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
