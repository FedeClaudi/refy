from refy import query, query_author, base_dir


def test_by_author():
    query_author("Gary  Stacey")

    query_author("this author doesnt exist probably right")


def test_query():
    query("neuron gene expression", N=20)

    query(
        "neuron gene expression", N=20, since=2015, to=2018,
    )

    query(
        " i dont think youll find many recomendations with this my dear 1231231"
    )


def test_query_save():
    f = base_dir / "query.csv"
    if f.exists:
        f.unlink()

    query("neuron gene expression", N=20, savepath=f)

    assert f.exists, "should have saved"

    f.unlink()
