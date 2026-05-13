def test_lista_completa_retorna_5_productos(http, base_url):
    res = http.get(f"{base_url}/productos")

    assert res.status_code == 200
    assert len(res.json()) == 5


def test_estructura_del_producto(productos):
    campos_requeridos = {"id", "nombre", "sabores_max", "precio"}
    for producto in productos:
        assert campos_requeridos.issubset(producto.keys())
        assert isinstance(producto["sabores_max"], int)
        assert producto["sabores_max"] > 0
        assert isinstance(producto["precio"], float)
        assert producto["precio"] > 0


def test_detalle_producto_existente(http, base_url, productos):
    producto_id = productos[0]["id"]
    res = http.get(f"{base_url}/productos/{producto_id}")

    assert res.status_code == 200
    data = res.json()
    assert data["id"] == producto_id
    assert data["nombre"] == productos[0]["nombre"]


def test_detalle_producto_inexistente_retorna_404(http, base_url):
    res = http.get(f"{base_url}/productos/9999")

    assert res.status_code == 404


def test_detalle_producto_id_string_retorna_422(http, base_url):
    res = http.get(f"{base_url}/productos/abc")

    assert res.status_code == 422
