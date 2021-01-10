import os
from pathlib import Path

DEBUG = True  # set to True if you wish to see debug logs

# ----------------------------------- paths ---------------------------------- #
# create base path folder
base_dir = Path(os.path.join(os.path.expanduser("~"), ".referee"))
base_dir.mkdir(exist_ok=True)

abstracts_path = base_dir / "abstracts.json"
database_path = base_dir / "database.h5"
d2v_model_path = base_dir / "d2v_model.model"
example_path = base_dir / "example_library.bib"

remote_url_base = "https://gin.g-node.org/FedeClaudi/Referee/raw/master/"

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
