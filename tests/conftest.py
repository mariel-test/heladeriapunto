# conftest.py
# Fixtures compartidas por todos los tests de API.
#
# Estrategia de datos:
#   - productos y sabores: scope=session, se cargan una vez por run (vienen del seed)
#   - pedido_creado: scope=function, crea un pedido nuevo en cada test que lo necesite
#   - Los IDs se obtienen dinámicamente desde la API (no hardcodeados) para que
#     los tests sobrevivan si el seed cambia de orden.

import logging
import os

import pytest
import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

logger = logging.getLogger("api_tests")


def _log_response(res: requests.Response, *args, **kwargs):
    """Hook ejecutado después de cada request — loguea método, URL, status y tiempo."""
    ms = res.elapsed.total_seconds() * 1000
    logger.info("%-6s %-50s → %s  (%.0f ms)", res.request.method, res.url, res.status_code, ms)


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def http(base_url):
    """Session de requests con hook de logging automático en cada llamada."""
    session = requests.Session()
    session.hooks["response"].append(_log_response)
    return session


@pytest.fixture(scope="session")
def productos(http, base_url):
    res = http.get(f"{base_url}/productos")
    res.raise_for_status()
    return res.json()


@pytest.fixture(scope="session")
def sabores(http, base_url):
    res = http.get(f"{base_url}/sabores")
    res.raise_for_status()
    return res.json()


@pytest.fixture(scope="session")
def producto_max1(productos):
    """Primer producto con sabores_max == 1 (Pote 1/4 kg en el seed)."""
    return next(p for p in productos if p["sabores_max"] == 1)


@pytest.fixture(scope="session")
def producto_max4(productos):
    """Primer producto con sabores_max == 4 (Pote 1 kg en el seed)."""
    return next(p for p in productos if p["sabores_max"] == 4)


@pytest.fixture
def pedido_creado(http, base_url, producto_max4, sabores):
    """Crea un pedido válido y devuelve el JSON de respuesta."""
    payload = {
        "producto_id": producto_max4["id"],
        "sabores_elegidos": [
            {"id": s["id"], "nombre": s["nombre"]}
            for s in sabores[:2]
        ],
    }
    res = http.post(f"{base_url}/pedido", json=payload)
    res.raise_for_status()
    return res.json()
