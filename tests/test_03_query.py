import refy


def test_by_author():
    refy.query_author("Gary  Stacey")

    refy.query_author("Gary  Stacey", to=1990, since=2020)

    # refy.query_author("this author doesnt exist probably right")


def test_query():
    refy.query("neuron gene expression", N=20)

    # refy.query(
    #     "neuron gene expression", N=20, since=2015, to=2018,
    # )

    # refy.query(
    #     " i dont think youll find many recomendations with this my dear 1231231"
    # )


# def test_query_save():
#     f = refy.base_dir / "query.csv"
#     if f.exists:
#         f.unlink()

#     refy.query("neuron gene expression", N=20, savepath=f)

#     assert f.exists, "should have saved"
#     f.unlink()
