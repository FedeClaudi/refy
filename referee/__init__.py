from pyinspect import install_traceback

install_traceback()

from referee.suggest import suggest
from referee.settings import DEBUG, base_dir, database_path
from referee._dbase import download_database

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


# download database
if not database_path.exists():
    download_database()
