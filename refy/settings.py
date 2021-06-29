import os
from pathlib import Path

DEBUG = False
TEST_MODE = False  # gets set to True when running tests
DOWNLOAD_MODEL_ONLY = False  # set to True to skip downloading datasets
DOWNLOAD_FAST = True  # enable parallel download of multiple files
# ----------------------------------- paths ---------------------------------- #
# create base path folder
base_dir = Path(os.path.join(os.path.expanduser("~"), ".refy"))
base_dir.mkdir(exist_ok=True)

# semantic scholar dbase paths
abstracts_path = base_dir / "abstracts.json"
database_path = base_dir / "database.ftr"

# test dbase paths
test_abstracts_path = base_dir / "test_abstracts.json"
test_database_path = base_dir / "test_database.ftr"

# biorxiv dbase paths
biorxiv_abstracts_path = base_dir / "biorxiv_abstracts.json"
biorxiv_database_path = base_dir / "biorxiv_database.ftr"

# d2v model paths
d2v_model_path = base_dir / "d2v_model.model"

# example library
example_path = base_dir / "example_library.bib"

# urls
remote_url_base = "https://gin.g-node.org/FedeClaudi/refy/raw/master/"

# ----------------------------- database settings ---------------------------- #
# when creating condensed database, keep only papers in these fields
fields_of_study = (
    "biology",
    "neuroscience",
    "medicine",
    "machine learning",
    "deep learning",
    "robotics",
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
    "behavior",
    "cognition",
    "neural network",
    "deep learning",
    "dendrite",
    "dendritic",
    "behaviour",
    "robotics",
    "artificial agent",
    "reinforcement learning",
    "agent",
    "computational",
    "dynamics",
    "RNN",
    "CNN",
    "spiking",
)  # only keep papers that have these keywords in the abstract


low_year = 1990  # only papers more recent than this are kept


# start and end date for queries from biorxiv's server
biorxiv_start_date = "2015-01-01"
biorxiv_end_date = "2021-06-28"
