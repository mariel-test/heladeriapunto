def test_lista_completa_retorna_10_sabores(http, base_url):
    res = http.get(f"{base_url}/sabores")

    assert res.status_code == 200
    assert len(res.json()) == 10


def test_estructura_del_sabor(http, base_url, sabores):
    campos_requeridos = {"id", "nombre", "categoria", "sin_tacc", "vegano", "alergenos"}
    for sabor in sabores:
        assert campos_requeridos.issubset(sabor.keys())
        assert isinstance(sabor["sin_tacc"], bool)
        assert isinstance(sabor["vegano"], bool)
        assert isinstance(sabor["alergenos"], list)


def test_filtro_categoria_crema(http, base_url):
    res = http.get(f"{base_url}/sabores", params={"categoria": "crema"})

    assert res.status_code == 200
    data = res.json()
    assert len(data) == 6
    assert all(s["categoria"] == "crema" for s in data)


def test_filtro_categoria_agua(http, base_url):
    res = http.get(f"{base_url}/sabores", params={"categoria": "agua"})

    assert res.status_code == 200
    data = res.json()
    assert len(data) == 4
    assert all(s["categoria"] == "agua" for s in data)


def test_filtro_sin_tacc_true(http, base_url):
    res = http.get(f"{base_url}/sabores", params={"sin_tacc": "true"})

    assert res.status_code == 200
    data = res.json()
    assert len(data) == 8
    assert all(s["sin_tacc"] is True for s in data)


def test_filtro_sin_tacc_false(http, base_url):
    res = http.get(f"{base_url}/sabores", params={"sin_tacc": "false"})

    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert all(s["sin_tacc"] is False for s in data)


def test_filtro_combinado_categoria_agua_sin_tacc_true(http, base_url):
    res = http.get(
        f"{base_url}/sabores",
        params={"categoria": "agua", "sin_tacc": "true"},
    )

    assert res.status_code == 200
    data = res.json()
    assert len(data) == 4
    assert all(s["categoria"] == "agua" and s["sin_tacc"] is True for s in data)


def test_categoria_inexistente_retorna_lista_vacia(http, base_url):
    res = http.get(f"{base_url}/sabores", params={"categoria": "medialuna"})

    assert res.status_code == 200
    assert res.json() == []
