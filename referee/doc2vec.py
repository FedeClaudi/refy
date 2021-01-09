from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from nltk.tokenize import word_tokenize
from loguru import logger

from .settings import base_dir
from .database import load_abstracts
from .progress import progress
from .utils import to_json, from_json

# ----------------------------------- utils ---------------------------------- #


def load_model():
    """
        Loads a previously saved model
    """
    logger.debug("Loading pre-trained doc2vec model")
    return Doc2Vec.load(str(base_dir / "d2v.model"))


def save_training_data(training_data):
    """
        Saves a training data body for future use.
    """
    logger.debug("Saving d2v training data")
    to_json(training_data, base_dir / "d2v_training_data.json")


def load_training_data():
    """
        Loads previously saved training data, TaggedDocument
        representation of each abstract in the database.
        Loading training data is much faster then generating
        them from scratch with make_training_data
    """
    logger.debug("Loading d2v training data")
    data = from_json(base_dir / "d2v_training_data.json")
    return [TaggedDocument(d[0], d[1]) for d in data]


# --------------------------------- training --------------------------------- #


def _preprocess(data):
    """
        Preprocess a corpus of text for training/using a doc2vec
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
                TaggedDocument(words=word_tokenize(_d.lower()), tags=[str(i)])
            )
            progress.update(preprocess_task, completed=i)

    progress.remove_task(preprocess_task)
    return training_data


def make_training_data():
    """
        Prepares training data for mod2vec for training
        the model on the whole corpus of abstracts

        Returns:
            training_data: list of TaggedDocument objects
    """
    # get database abstracts
    data = list(load_abstracts().values())[:1000]  # ! for debugging

    # pre-process data
    logger.debug("Pre-processing data")
    if len(data) > 10000:
        logger.info(
            f"Creating training set with {len(data)} items, pre-processing may be very slow"
        )

    try:
        training_data = _preprocess(data)
    except LookupError:
        res = "import nltk; nltk.download('punkt')"
        raise ValueError(
            f'Failed to tokenize training data, please download resource with "{res}"'
        )
    save_training_data(training_data)
    return training_data


def train_doc2vec_model(
    training_data=None, n_epochs=1000, vec_size=20, alpha=0.025
):
    """
        Trains a doc2vec model from gensim for embedding and similarity 
        evaluation of paper abstracts.

        See: https://radimrehurek.com/gensim/models/doc2vec.html

        Arguments:
            training_data: List of TaggedDocument objects. Optional. If not passed
                the entire corpus of abstracts is used
            n_epochs: int. Numberof epochs for training
            vec_size: int. Dimensionality of the feature vectors
            alpha: float. The initial learning rate
    """
    logger.debug("Training doc2vec model")

    # get training data
    training_data = training_data or make_training_data()

    # create model
    logger.debug("Training")
    model = Doc2Vec(
        vec_size=vec_size, alpha=alpha, min_alpha=0.00025, min_count=1, dm=1
    )

    model.build_vocab(training_data)

    # train
    with progress:
        task = progress.add_task(
            "Training doc2vec", total=n_epochs, start=True, completed=0,
        )

        for epoch in range(n_epochs):
            model.train(
                training_data,
                total_examples=model.corpus_count,
                epochs=model.iter,
            )

            # decrease the learning rate
            model.alpha -= 0.0002

            # fix the learning rate, no decay
            model.min_alpha = model.alpha

            # update progress
            progress.update(task, completed=epoch)

    model.save(str(base_dir / "d2v.model"))
    logger.debug(f"Model Saved at: {base_dir/'d2v.model'}")
