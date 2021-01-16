from refy import utils
from refy import base_dir


def test_isin():
    l1 = [1, 2, 3]
    l2 = [3, 4, 5]
    l3 = [5, 6, 7]

    assert utils.isin(l1, l2), "should be true"
    assert not utils.isin(l1, l3), "shoule be false"


def test_json():
    path = base_dir / "test.json"
    if path.exists():
        path.unlink()

    a = {str(i): i for i in range(20)}

    utils.to_json(a, path)
    assert path.exists()

    b = utils.from_json(path)
    assert a == b, "should be the same"

    path.unlink()


def test_request():
    if not utils.check_internet_connection():
        return

    url = "https://api.biorxiv.org/details/biorxiv/2015-01-01/2015-01-02"
    utils.request(url)
