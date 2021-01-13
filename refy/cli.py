import typer
import sys
from loguru import logger

sys.path.append("./")
import refy

app = typer.Typer()


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
    savepath: str = typer.Option(
        None, "-save-path", "--s", help="Save suggestions to file"
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
            savepath: str, Path. Path pointing to a .csv file where the recomendations
                will be saved
            debug: bool. If true refy is set in debug mode and more info are printed
    """
    if debug:
        refy.set_logging("DEBUG")

    logger.debug(f"CLI: suggest for: {filepath}")

    refy.suggest(
        filepath, N=N, since=since, to=to, savepath=savepath,
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
    savepath: str = typer.Option(
        None, "-save-path", "--s", help="Save suggestions to file"
    ),
    debug: bool = typer.Option(
        False, "-debug", "--d", help="set debug mode ON/OFF"
    ),
):
    """
        Find relevant papers similar to an input string


        Arguments:
            input_stirng: str. String to match against database
            N: int. Number of papers to suggest
            since: int or None. If an int is passed it must be a year,
                only papers more recent than the given year are kept for recomendation
            to: int or None. If an int is passed it must be a year,
                only papers older than that are kept for recomendation
            savepath: str, Path. Path pointing to a .csv file where the recomendations
                will be saved
            debug: bool. If true refy is set in debug mode and more info are printed
    """
    if debug:
        refy.set_logging("DEBUG")

    refy.suggest_one(
        input_string, N=N, since=since, to=to, savepath=savepath,
    )


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
    epochs: int = typer.Argument(50, help="Number of iterations for training"),
    vecs: int = typer.Argument(500, help="Size of features vector"),
    lr: float = typer.Argument(0.025, help="Learning rate"),
):
    """
        Trains the doc2vec model on the database data and abstracts

        Arguments:
            epochs: int. Numberof epochs for training
            vecs: int. Dimensionality of the feature vectors
            lr: float. The initial learning rate
    """
    logger.debug("CLI: training d2v model")
    refy.doc2vec.train_doc2vec_model(n_epochs=epochs, vec_size=vecs, alpha=lr)


if __name__ == "__main__":
    app()