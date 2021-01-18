from refy import Daily
import refy


def test_daily():
    Daily().run(refy.settings.example_path)
