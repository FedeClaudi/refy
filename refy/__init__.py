from pyinspect import install_traceback

install_traceback(hide_locals=True)


from refy.recomend import Recomender

from loguru import logger
import sys


def set_logging(level="INFO", path=None):
    logger.remove()
    logger.add(sys.stdout, level=level)


set_logging()
