import os
from pathlib import Path

DEBUG = True  # set to True if you wish to see debug logs

# ---------------------------------- TF-IDF ---------------------------------- #
"""
    Fitting TF-IDF on a vast dataset and using a large vocabulary can be very slow
    and memory expensive. Use these settings to reduce the ammount of data used
    in the process.

    The larger the `use_n_papers` the more papers are used for the comparison
    The large the `vocabulary_size` the more words are used to compare paper's absracts

    Set n_papers = -1 if you want to use the entire database
"""
use_n_papers = (
    20000  # max number of (randomly selected) papers from the database to use
)
vocabulary_size = (
    250  # number of words to use to compute similarity across papers
)

# ----------------------------------- paths ---------------------------------- #
# create base path folder
base_dir = Path(os.path.join(os.path.expanduser("~"), ".referee"))
base_dir.mkdir(exist_ok=True)

abstracts_path = base_dir / "abstracts.json"
database_path = base_dir / "database.h5"

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
