from pyinspect import install_traceback

install_traceback(hide_locals=True)

from refy.suggest import suggest
from refy.daily import Daily
from refy.query import query_author, query
from refy.settings import (
    DEBUG,
    base_dir,
)


# ----------------------------- logging settings ----------------------------- #

from loguru import logger
import sys
from pathlib import Path


def set_logging(level="INFO", path=None):
    logger.remove()
    logger.add(sys.stdout, level=level)

    path = path or str(base_dir / "log.log")
    if Path(path).exists():
        Path(path).unlink()

    logger.add(path, level="DEBUG")


if not DEBUG:
    set_logging()
else:
    set_logging(level="DEBUG")
