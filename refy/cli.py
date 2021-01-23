import typer
import sys
from loguru import logger

sys.path.append("./")
import refy

app = typer.Typer()


@app.command()
def daily(
    filepath: str = typer.Argument(
        ..., help="Path to .bib file with user papers metadata"
    ),
    N: int = typer.Option(10, "-N", help="number of recomendations to return"),
    html_path: str = typer.Option(
        None, "-o", help="Path to .html file where to save suggestions"
    ),
    debug: bool = typer.Option(
        False, "-debug", "--d", help="set debug mode ON/OFF"
    ),
):
    """
        Run suggestions on latest biorxvis preprints, daily.
    """

    # set specific log file
    logpath = refy.base_dir / "daily.log"
    lvl = "DEBUG" if debug else "INFO"
    try:
        refy.set_logging(level=lvl, path=logpath)
    except:
        refy.set_logging(level=lvl)

    # run daily search
    try:
        refy.Daily(filepath, html_path=html_path, N=N)
    except Exception as e:
        logger.warning(f"Failed to run daily search, error: {e}")


@app.command()
def setup_daily(
    user: str = typer.Argument(..., help="Computer user name"),
    python_path: str = typer.Argument(
        ..., help="Path of python executable (which python)"
    ),
    filepath: str = typer.Argument(
        ..., help="Path to .bib file with user papers metadata"
    ),
    N: int = typer.Option(10, "-N", help="number of recomendations to return"),
    html_path: str = typer.Option(
        None, "-o", help="Path to .html file where to save suggestions"
    ),
):
    """
        Sets up a scheduled daily task to recomend papers
    """
    # set specific log file
    logpath = refy.base_dir / "daily.log"
    if logpath.exists():
        logpath.unlink()

    refy.set_logging(level="INFO", path=str(logpath))

    # setup daily
    try:
        refy.daily.setup(user, python_path, filepath, N, html_path)
    except OSError:
        raise ValueError(
            "In order to set up refy daily you need to use this command as administrator."
            ' On Linux and Mac OS try putting "sudo" before the command'
        )


@app.command()
def stop_daily(user: str = typer.Argument(..., help="Computer user name"),):
    """
        removes any schedule daily task from refy
    """
    refy.daily.stop(user)


@app.command()
def suggest(
    filepath: str = typer.Argument(
        ..., help="Path to .bib file with user papers metadata"
    ),
    N: int = typer.Option(25, "-N", help="number of recomendations to return"),
    since: int = typer.Option(
        None, "-since", help="Only keep papers published after SINCE"
    ),
    to: int = typer.Option(
        None, "-to", help="Only keep papers published before TO"
    ),
    csv_path: str = typer.Option(
        None, "-csv-path", help="Save suggestions to .CSV file"
    ),
    html_path: str = typer.Option(
        None, "-html-path", help="Save suggestions to .HTML file"
    ),
    debug: bool = typer.Option(
        False, "-debug", "--d", help="set debug mode ON/OFF"
    ),
):
    """
        Suggest new relevant papers based on your library

        Arguments:
            user_papers: str, path. Path to a .bib file with user's papers info
            N: int. Number of papers to suggest
            since: int or None. If an int is passed it must be a year,
                only papers more recent than the given year are kept for recomendation
            to: int or None. If an int is passed it must be a year,
                only papers older than that are kept for recomendation
            csv_path: str, Path. Path pointing to a .csv file where the recomendations
                will be saved
            html_path: str, Path. Path to save formatted suggestions as HTML content
            debug: bool. If true refy is set in debug mode and more info are printed
    """
    if debug:
        refy.set_logging("DEBUG")

    logger.debug(f"CLI: suggest for: {filepath}")

    refy.suggest(
        filepath,
        N=N,
        since=since,
        to=to,
        csv_path=csv_path,
        html_path=html_path,
    )


@app.command()
def query(
    input_string: str = typer.Argument(..., help="Imput string for query"),
    N: int = typer.Option(10, "-N", help="number of recomendations to return"),
    since: int = typer.Option(
        None, "-since", help="Only keep papers published after SINCE"
    ),
    to: int = typer.Option(
        None, "-to", help="Only keep papers published before TO"
    ),
    csv_path: str = typer.Option(
        None, "-csv-path", help="Save suggestions to file"
    ),
    debug: bool = typer.Option(
        False, "-debug", "--d", help="set debug mode ON/OFF"
    ),
):
    """
        Find relevant papers similar to an input string


        Arguments:
            input_string: str. String to match against database
            N: int. Number of papers to suggest
            since: int or None. If an int is passed it must be a year,
                only papers more recent than the given year are kept for recomendation
            to: int or None. If an int is passed it must be a year,
                only papers older than that are kept for recomendation
            csv_path: str, Path. Path pointing to a .csv file where the recomendations
                will be saved
            debug: bool. If true refy is set in debug mode and more info are printed
    """
    if debug:
        refy.set_logging("DEBUG")

    refy.query(
        input_string, N=N, since=since, to=to, csv_path=csv_path,
    )


@app.command()
def author(
    author: str = typer.Argument(..., help="Author name"),
    N: int = typer.Option(10, "-N", help="number of recomendations to return"),
    since: int = typer.Option(
        None, "-since", help="Only keep papers published after SINCE"
    ),
    to: int = typer.Option(
        None, "-to", help="Only keep papers published before TO"
    ),
    csv_path: str = typer.Option(
        None, "-csv-path", help="Save suggestions to file"
    ),
    debug: bool = typer.Option(
        False, "-debug", "--d", help="set debug mode ON/OFF"
    ),
):
    """
        Find relevant papers similar to an input string


        Arguments:
            author: str. Author name for search
            N: int. Number of papers to suggest
            since: int or None. If an int is passed it must be a year,
                only papers more recent than the given year are kept for recomendation
            to: int or None. If an int is passed it must be a year,
                only papers older than that are kept for recomendation
            csv_path: str, Path. Path pointing to a .csv file where the recomendations
                will be saved
            debug: bool. If true refy is set in debug mode and more info are printed
    """
    if debug:
        refy.set_logging("DEBUG")

    refy.query_author(
        author, N=N, since=since, to=to, csv_path=csv_path,
    )


@app.command()
def example():
    """
        Run refy on an example .bib file.
    """
    refy.suggest(refy.settings.example_path, N=10)


@app.command()
def update_database(
    folder: str = typer.Argument(
        ..., help="Path to folder with semantic scholar raw data"
    ),
):
    """
        Updates all database files with current settings.

        Arguments:
            folder: str. Path to folder with 
                semantic scholar raw data
    """
    logger.debug("CLI: updating database")
    logger.debug("Unpacking sem. schol. database")
    refy.database.semantic_scholar.upack_database(folder)

    logger.debug("Making sem. schol. database")
    refy.database.semantic_scholar.make_database(folder)

    logger.debug("Making biorxiv database")
    refy.database.biorxiv.make_biorxiv_database()


@app.command()
def train(
    epochs: int = typer.Option(
        50, "--epochs", help="Number of iterations for training"
    ),
    vecs: int = typer.Option(500, "--vecs", help="Size of features vector"),
    lr: float = typer.Option(0.025, "--lr", help="Learning rate"),
):
    """
        Trains the doc2vec model on the database data and abstracts

        Arguments:
            epochs: int. Numberof epochs for training
            vecs: int. Dimensionality of the feature vectors
            lr: float. The initial learning rate
    """
    refy.set_logging("DEBUG")

    logger.debug("CLI: training d2v model")
    refy.doc2vec.train_doc2vec_model(n_epochs=epochs, vec_size=vecs, alpha=lr)


if __name__ == "__main__":
    app()
