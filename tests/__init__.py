from refy import settings
import refy

# set test mode to load a small portion of the database
settings.TEST_MODE = True
settings.DEBUG = True
refy.set_logging("DEBUG")


DB = refy.database.load_database()
