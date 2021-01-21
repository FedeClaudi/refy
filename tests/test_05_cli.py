import refy
from typer.testing import CliRunner
from pathlib import Path
import pytest
from refy.cli import app


@pytest.fixture
def csv_path():
    csvpath = Path("test.csv")
    if csvpath.exists():
        csvpath.unlink()
    return str(csvpath)


@pytest.fixture
def html_path():
    htmlpath = Path("test.html")
    if htmlpath.exists():
        htmlpath.unlink()
    return str(htmlpath)


runner = CliRunner()
ex = refy.settings.example_path


def test_cli_daily(html_path):
    runner.invoke(app, ["daily", ex, "-N", "10", "-o", html_path, "--d"])


def test_cli_query(html_path):
    runner.invoke(
        app,
        [
            "query",
            "locomotion",
            "-N",
            "10",
            "-csv-path",
            html_path,
            "--d",
            "-since",
            2015,
            "-to",
            2020,
        ],
    )


def test_cli_author(html_path):
    runner.invoke(
        app,
        [
            "author",
            "Carandini M.",
            "-N",
            "10",
            "-csv-path",
            html_path,
            "--d",
            "-since",
            2015,
            "-to",
            2020,
        ],
    )


def test_cli_suggest(html_path, csv_path):
    runner.invoke(
        app,
        [
            "suggest",
            ex,
            "-N",
            "10",
            "-html-path",
            html_path,
            "-csv-path",
            csv_path,
            "--d",
            "-since",
            2015,
            "-to",
            2020,
        ],
    )
