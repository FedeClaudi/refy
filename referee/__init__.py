from pyinspect import install_traceback

install_traceback(hide_locals=True)

from referee.suggest import suggest
from referee.settings import (
    DEBUG,
    base_dir,
    database_path,
    d2v_model_path,
    example_path,
    remote_url_base,
    biorxiv_abstracts_path,
)
from referee import doc2vec
from referee.utils import retrieve_over_http

import referee.database_preprocessing as preprocessing
import referee.database_biorxiv as biorxiv


# logging settings
from loguru import logger
import sys

if not DEBUG:
    # show only log messages from warning up
    logger.remove()
    handler_id = logger.add(sys.stderr, level="INFO")
    handler_id = logger.add(sys.stdout, level="INFO")

# add another logger saving to file
logger.add(str(base_dir / "log.log"), level="DEBUG")


# ------------------------------- download data ------------------------------ #

# download database
if not database_path.exists():
    preprocessing.download()

# download d2v model
if not d2v_model_path.exists():
    doc2vec.download()

# download example library
if not example_path.exists():
    retrieve_over_http(remote_url_base + "example_library.bib", example_path)

# download biorxiv
# if not biorxiv_abstracts_path.exists():
#     biorxiv.download()
