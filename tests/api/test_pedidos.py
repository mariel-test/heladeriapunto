def _sabores_payload(sabores, cantidad):
    return [{"id": s["id"], "nombre": s["nombre"]} for s in sabores[:cantidad]]


# ── Happy path + reglas de negocio ────────────────────────────────────────────

def test_crear_pedido_valido_retorna_201(http, base_url, producto_max4, sabores):
    payload = {
        "producto_id": producto_max4["id"],
        "sabores_elegidos": _sabores_payload(sabores, 4),
    }
    res = http.post(f"{base_url}/pedido", json=payload)

    assert res.status_code == 201
    data = res.json()
    assert "id" in data
    assert "total" in data
    assert "estado" in data


def test_total_lo_calcula_el_backend(http, base_url, producto_max4, sabores):
    payload = {
        "producto_id": producto_max4["id"],
        "sabores_elegidos": _sabores_payload(sabores, 2),
    }
    res = http.post(f"{base_url}/pedido", json=payload)

    assert res.status_code == 201
    assert res.json()["total"] == producto_max4["precio"]


def test_estado_inicial_es_pendiente(http, base_url, producto_max4, sabores):
    payload = {
        "producto_id": producto_max4["id"],
        "sabores_elegidos": _sabores_payload(sabores, 1),
    }
    res = http.post(f"{base_url}/pedido", json=payload)

    assert res.status_code == 201
    assert res.json()["estado"] == "pendiente"


def test_pedido_con_sabores_max_1(http, base_url, producto_max1, sabores):
    payload = {
        "producto_id": producto_max1["id"],
        "sabores_elegidos": _sabores_payload(sabores, 1),
    }
    res = http.post(f"{base_url}/pedido", json=payload)

    assert res.status_code == 201
    assert res.json()["total"] == producto_max1["precio"]


# ── GET /pedido/{id} ──────────────────────────────────────────────────────────

def test_obtener_pedido_existente(http, base_url, pedido_creado):
    res = http.get(f"{base_url}/pedido/{pedido_creado['id']}")

    assert res.status_code == 200
    data = res.json()
    assert data["id"] == pedido_creado["id"]
    assert isinstance(data["sabores_elegidos"], list)
    assert all("id" in s and "nombre" in s for s in data["sabores_elegidos"])


def test_obtener_pedido_inexistente_retorna_404(http, base_url):
    res = http.get(f"{base_url}/pedido/9999")

    assert res.status_code == 404


# ── Negativos ─────────────────────────────────────────────────────────────────

def test_producto_inexistente_retorna_404(http, base_url, sabores):
    payload = {
        "producto_id": 9999,
        "sabores_elegidos": _sabores_payload(sabores, 1),
    }
    res = http.post(f"{base_url}/pedido", json=payload)

    assert res.status_code == 404


def test_superar_sabores_max_retorna_422(http, base_url, producto_max1, sabores):
    payload = {
        "producto_id": producto_max1["id"],
        "sabores_elegidos": _sabores_payload(sabores, 2),
    }
    res = http.post(f"{base_url}/pedido", json=payload)

    assert res.status_code == 422
    assert str(producto_max1["sabores_max"]) in res.json()["detail"]


def test_sabor_inexistente_retorna_422(http, base_url, producto_max4):
    payload = {
        "producto_id": producto_max4["id"],
        "sabores_elegidos": [{"id": 9999, "nombre": "Sabor fantasma"}],
    }
    res = http.post(f"{base_url}/pedido", json=payload)

    assert res.status_code == 422
    assert "9999" in str(res.json()["detail"])


def test_sabores_vacios_retorna_422(http, base_url, producto_max4):
    payload = {
        "producto_id": producto_max4["id"],
        "sabores_elegidos": [],
    }
    res = http.post(f"{base_url}/pedido", json=payload)

    assert res.status_code == 422


def test_sin_producto_id_retorna_422(http, base_url, sabores):
    payload = {"sabores_elegidos": _sabores_payload(sabores, 1)}
    res = http.post(f"{base_url}/pedido", json=payload)

    assert res.status_code == 422


def test_body_invalido_retorna_422(http, base_url):
    res = http.post(
        f"{base_url}/pedido",
        data="esto no es json",
        headers={"Content-Type": "application/json"},
    )

    assert res.status_code == 422
