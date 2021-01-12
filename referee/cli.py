import typer
import sys

sys.path.append("./")
import referee

app = typer.Typer()


@app.command()
def suggest(
    filepath: str = typer.Argument(
        ..., help="Path to .bib file with user papers metadata"
    ),
    N: int = typer.Option(
        100, "--N", help="number of recomendations to return"
    ),
    since: int = typer.Option(
        None, "--since", help="Only keep papers published after SINCE"
    ),
    to: int = typer.Option(
        None, "--to", help="Only keep papers published before TO"
    ),
    savepath: str = typer.Option(
        None, "--save-path", "--s", help="Save suggestions to file"
    ),
    debug: bool = typer.Option(
        False, "--debug", "--d", help="set debug mode ON/OFF"
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
            debug: bool. If true referee is set in debug mode and more info are printed
    """
    referee.DEBUG = debug

    referee.suggest(
        filepath, N=N, since=since, to=to, savepath=savepath,
    )


# TODO fix debug messages showing up
# TODO finish this
# TODO add this to tests

if __name__ == "__main__":
    app()
