from referee.database import upack_database, make_database

if __name__ == "__main__":
    fld = r"M:\PAPERS_DBASE"
    upack_database(fld)

    make_database(fld)
