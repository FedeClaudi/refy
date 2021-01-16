from pyinspect import install_traceback

install_traceback(hide_locals=True)

from refy.suggest import suggest
from refy.query import query_author, query
from refy.settings import (
    DEBUG,
    base_dir,
)


# ----------------------------- logging settings ----------------------------- #

from loguru import logger
import sys


def set_logging(level="INFO"):
    logger.remove()
    logger.add(sys.stdout, level=level)
    logger.add(str(base_dir / "log.log"), level="DEBUG")


if not DEBUG:
    set_logging()
else:
    set_logging(level="DEBUG")
