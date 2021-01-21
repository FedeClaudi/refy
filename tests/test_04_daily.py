from refy import Daily
import refy
from pathlib import Path


def test_daily():
    htmlpath = Path("test.html")
    if htmlpath.exists():
        htmlpath.unlink()

    Daily(refy.settings.example_path, html_path=htmlpath)

    assert htmlpath.exists(), "did not save to HTML!"
