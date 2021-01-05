import os
from pathlib import Path

# ----------------------------------- paths ---------------------------------- #
# create base path folder
base_dir = Path(os.path.join(os.path.expanduser("~"), ".referee"))
base_dir.mkdir(exist_ok=True)


# ----------------------------- database settings ---------------------------- #
# when creating condensed database, keep only papers in these fields
fields_of_study = (
    'Biology',
    'Neuroscience',
)
keywords = (
    'neuro',
    'neuron',
    'brain',
    'synapse',
    'neurons',
    'neurotransmitter',
    'neuronal'
) # only keep papers that have these keywords in the abstract


low_year = 1990  # only papers more recent than this are kept