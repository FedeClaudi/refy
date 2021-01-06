import os
from pathlib import Path
from loguru import logger


DEBUG = True  # set to True if you wish to see debug logs

# ---------------------------------- TF-IDF ---------------------------------- #
"""
    Fitting TF-IDF on a vast dataset and using a large vocabulary can be very slow
    and memory expensive. Use these settings to reduce the ammount of data used
    in the process.

    Set n_papers = -1 if you want to use the entire database
"""
n_papers = (
    100000  # max number of (randomly selected) papers from the database to use
)
vocabulary_size = (
    50000  # number of words to use to compute similarity across papers
)

# ----------------------------------- paths ---------------------------------- #
# create base path folder
base_dir = Path(os.path.join(os.path.expanduser("~"), ".referee"))
base_dir.mkdir(exist_ok=True)

abstracts_path = base_dir / "abstracts.json"
database_path = base_dir / "database.h5"
if not database_path.exists():
    logger.debug("Database file does not exist")


# ----------------------------- database settings ---------------------------- #
# when creating condensed database, keep only papers in these fields
fields_of_study = (
    "Biology",
    "Neuroscience",
)
keywords = (
    "neuro",
    "neuron",
    "brain",
    "synapse",
    "neurons",
    "neurotransmitter",
    "neuronal",
    "behaviour",
)  # only keep papers that have these keywords in the abstract


low_year = 1990  # only papers more recent than this are kept
