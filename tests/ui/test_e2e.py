"""
tests/ui/test_e2e.py  —  TC-E2E01 a TC-E2E06

Flujos End-to-End completos: usuario → UI (localhost:3000) → API (localhost:8000) → BD.
Sin mocks excepto TC-E2E06, que simula el servicio IA caído.

Requisitos:
  - frontend en http://localhost:3000  (nginx sirve frontend/)
  - backend  en http://localhost:8000  (uvicorn)
  - BD sembrada con seed.sql
  - ChromaDB en http://localhost:8001  con FAQ indexado (python -m ia.ingest)
  - Ollama   en http://localhost:11434 con modelo llama3.2

Correr:
  pytest tests/ui/test_e2e.py -v
"""

import json
import requests
from playwright.sync_api import Page, Route, expect

FRONTEND         = "http://localhost:3000"
API              = "http://localhost:8000"
PRODUCTO_MAX1    = "Pote 1/4 kg"      # sabores_max=1  (seed)
PRODUCTO_MAX4    = "Combo familiar"   # sabores_max=4  (seed)
TOTAL_SABORES    = 10
SABORES_SIN_TACC = 8                  # sin_tacc=true en el seed


# ── TC-E2E02 ──────────────────────────────────────────────────────────────────

def test_e2e02_pantalla_inicial_muestra_elementos_clave(page: Page):
    """TC-E2E02: Al cargar localhost:3000 se muestran el logo, el botón
    'Hacer pedido' y el botón 'Consultar'. El chat permanece oculto."""
    page.goto(FRONTEND)

    expect(page.locator(".logo")).to_contain_text("Frío & Punto")
    expect(page.locator(".btn-primario", has_text="Hacer pedido")).to_be_visible()
    expect(page.locator(".btn-secundario", has_text="Consultar")).to_be_visible()

    # Solo la pantalla de inicio activa
    expect(page.locator("#screen-inicio")).to_be_visible()
    expect(page.locator("#screen-productos")).not_to_be_visible()

    # El chat empieza oculto
    expect(page.locator("#chat-area")).not_to_be_visible()


# ── TC-E2E01 ──────────────────────────────────────────────────────────────────

def test_e2e01_flujo_completo_pedido(page: Page):
    """TC-E2E01: Flujo completo inicio → producto → sabores → resumen → confirmación.
    Verifica navegación entre pantallas, reglas de negocio y persistencia del pedido."""
    page.goto(FRONTEND)

    # ── Inicio ──────────────────────────────────────────────
    expect(page.locator(".logo")).to_be_visible()
    page.locator("text=Hacer pedido").click()

    # ── Pantalla productos ───────────────────────────────────
    expect(page.locator("#screen-productos")).to_be_visible()
    expect(page.locator("h2", has_text="¿Qué tamaño?")).to_be_visible()
    page.locator(".card-producto", has_text=PRODUCTO_MAX1).wait_for()
    expect(page.locator(".card-producto")).to_have_count(5)

    page.locator(".card-producto", has_text=PRODUCTO_MAX1).click()

    # ── Pantalla sabores ─────────────────────────────────────
    expect(page.locator("#screen-sabores")).to_be_visible()
    expect(page.locator("#titulo-sabores")).to_contain_text(PRODUCTO_MAX1)
    expect(page.locator("#titulo-sabores")).to_contain_text("1")
    page.locator(".card-sabor").first.wait_for()
    expect(page.locator(".card-sabor")).to_have_count(TOTAL_SABORES)

    # El botón Confirmar empieza deshabilitado (0 sabores elegidos)
    expect(page.locator("#btn-confirmar-sabores")).to_be_disabled()
    expect(page.locator("#contador-sabores")).to_have_text("0 / 1")

    # Elegir un sabor → se habilita Confirmar
    primer_sabor = page.locator(".card-sabor").first.locator(".sabor-nombre").inner_text()
    page.locator(".card-sabor input[type=checkbox]").first.check()
    expect(page.locator("#contador-sabores")).to_have_text("1 / 1")
    expect(page.locator("#btn-confirmar-sabores")).to_be_enabled()

    page.locator("#btn-confirmar-sabores").click()

    # ── Pantalla resumen ─────────────────────────────────────
    expect(page.locator("#screen-resumen")).to_be_visible()
    expect(page.locator(".resumen-producto-nombre")).to_contain_text(PRODUCTO_MAX1)
    expect(page.locator(".resumen-precio")).to_contain_text("$")
    expect(page.locator(".resumen-sabores li")).to_have_count(1)
    expect(page.locator(".resumen-sabores li").first).to_contain_text(primer_sabor)

    page.locator("#btn-confirmar-pedido").click()

    # ── Confirmación ─────────────────────────────────────────
    expect(page.locator(".confirmado")).to_have_text("✓ Pedido confirmado")
    expect(page.locator(".pedido-id")).to_be_visible()

    pedido_texto = page.locator(".pedido-id").inner_text()
    numero = pedido_texto.replace("Pedido #", "").strip()
    assert numero.isdigit(), f"El id del pedido debe ser numérico: '{numero}'"

    # BUG-004 fix: verificar que el pedido exista en la BD (no solo en la UI)
    resp = requests.get(f"{API}/pedido/{numero}")
    assert resp.status_code == 200, (
        f"Pedido #{numero} mostrado en UI pero no encontrado en BD (status {resp.status_code})"
    )
    db_data = resp.json()
    assert db_data["id"] == int(numero)
    assert db_data["estado"] == "pendiente"

    # El botón "Confirmar" se oculta; aparece "Nuevo pedido"
    expect(page.locator("#btn-confirmar-pedido")).not_to_be_visible()
    expect(page.locator("#btn-nuevo-pedido")).to_be_visible()

    # ── Nuevo pedido vuelve al inicio ────────────────────────
    page.locator("#btn-nuevo-pedido").click()
    expect(page.locator("#screen-inicio")).to_be_visible()
    expect(page.locator("#screen-resumen")).not_to_be_visible()


# ── TC-E2E04 ──────────────────────────────────────────────────────────────────

def test_e2e04_validacion_sabores_maximo_bloquea_en_ui(page: Page):
    """TC-E2E04: Con sabores_max=1, al elegir el primer sabor la UI deshabilita
    los demás checkboxes — la validación ocurre en cliente sin llamar al backend."""
    page.goto(FRONTEND)
    page.locator("text=Hacer pedido").click()
    page.locator(".card-producto", has_text=PRODUCTO_MAX1).wait_for()
    page.locator(".card-producto", has_text=PRODUCTO_MAX1).click()
    page.locator(".card-sabor").first.wait_for()

    # Estado inicial: ningún sabor seleccionado
    expect(page.locator("#btn-confirmar-sabores")).to_be_disabled()

    # Seleccionar el primer sabor
    page.locator(".card-sabor input[type=checkbox]").first.check()
    expect(page.locator("#contador-sabores")).to_have_text("1 / 1")

    # Todos los checkboxes no marcados deben estar disabled
    no_marcados = page.locator(".card-sabor input[type=checkbox]:not(:checked)")
    assert no_marcados.count() == TOTAL_SABORES - 1
    for i in range(no_marcados.count()):
        expect(no_marcados.nth(i)).to_be_disabled()

    # Desmarcar libera los demás checkboxes
    # Nota: .click() en lugar de .uncheck() porque renderSabores() reconstruye el
    # DOM completo tras cada toggle — el nodo original queda detached y uncheck() falla.
    page.locator(".card-sabor input[type=checkbox]").first.click()
    expect(page.locator("#contador-sabores")).to_have_text("0 / 1")
    expect(page.locator("#btn-confirmar-sabores")).to_be_disabled()
    for i in range(page.locator(".card-sabor input[type=checkbox]").count()):
        expect(page.locator(".card-sabor input[type=checkbox]").nth(i)).to_be_enabled()


# ── TC-E2E05 ──────────────────────────────────────────────────────────────────

def test_e2e05_filtro_tacc_en_flujo_de_sabores(page: Page):
    """TC-E2E05: Durante la selección de sabores, 'Filtrar con TACC' muestra solo
    los 8 sabores aptos (sin_tacc=true) y oculta Brownie y Tramontana."""
    page.goto(FRONTEND)
    page.locator("text=Hacer pedido").click()
    page.locator(".card-producto", has_text=PRODUCTO_MAX4).wait_for()
    page.locator(".card-producto", has_text=PRODUCTO_MAX4).click()
    page.locator(".card-sabor").first.wait_for()

    # Verificar que el label del filtro dice "Filtrar con TACC" (fix BUG-002)
    expect(page.locator(".filtro-tacc")).to_contain_text("Filtrar con TACC")

    # Sin filtro: 10 sabores
    expect(page.locator(".card-sabor")).to_have_count(TOTAL_SABORES)

    # Activar filtro
    page.locator("#filtro-sin-tacc").check()
    expect(page.locator(".card-sabor")).to_have_count(SABORES_SIN_TACC)

    # Brownie con chips y Tramontana (sin_tacc=false) no deben ser visibles
    expect(page.locator(".card-sabor", has_text="Brownie")).not_to_be_visible()
    expect(page.locator(".card-sabor", has_text="Tramontana")).not_to_be_visible()

    # Desactivar filtro restaura los 10 sabores
    page.locator("#filtro-sin-tacc").uncheck()
    expect(page.locator(".card-sabor")).to_have_count(TOTAL_SABORES)
    expect(page.locator(".card-sabor", has_text="Brownie")).to_be_visible()


# ── TC-E2E03 ──────────────────────────────────────────────────────────────────

def test_e2e03_chat_ia_responde_pregunta_real(page: Page):
    """TC-E2E03: Flujo completo del chat — UI → POST /ia/ask → ChromaDB → Ollama.
    La respuesta debe ser coherente con el FAQ indexado (no 503, no vacía)."""
    page.goto(FRONTEND)

    page.locator("text=Consultar").click()
    expect(page.locator("#chat-area")).to_be_visible()

    page.fill("#chat-input", "¿tienen opciones veganas?")
    page.locator("text=Enviar").click()

    # Mensaje del usuario reflejado en el chat
    expect(page.locator(".mensaje.usuario")).to_have_text("¿tienen opciones veganas?")

    # Respuesta del asistente — Ollama puede tardar hasta 45s en la primera inferencia
    expect(page.locator(".mensaje.ia")).to_be_visible(timeout=45_000)
    respuesta = page.locator(".mensaje.ia").inner_text()

    assert len(respuesta) > 10, "La respuesta no puede estar vacía"
    assert "503" not in respuesta, "No debe exponerse el código HTTP al usuario"
    # El FAQ tiene respuesta sobre veganos; si no hay contexto retorna el fallback
    assert "vegano" in respuesta.lower() or "No tengo información" in respuesta, (
        f"Respuesta inesperada del asistente: '{respuesta}'"
    )


# ── TC-E2E06 ──────────────────────────────────────────────────────────────────

def test_e2e06_ia_indisponible_muestra_fallback_amigable(page: Page):
    """TC-E2E06: Con el servicio IA caído (503), la UI muestra el mensaje amigable
    'Asistente no disponible. Consultá en caja.' — sin exponer errores técnicos."""
    page.goto(FRONTEND)

    # Simular IA caída antes de que el usuario consulte
    page.route(
        f"{API}/ia/ask",
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body=json.dumps({"detail": "Asistente no disponible. Consultá en caja."}),
        ),
    )

    page.locator("text=Consultar").click()
    expect(page.locator("#chat-area")).to_be_visible()

    page.fill("#chat-input", "¿tienen delivery?")
    page.locator("text=Enviar").click()

    # La UI debe mostrar el mensaje de fallback, no el JSON crudo
    expect(page.locator(".mensaje.ia")).to_be_visible()
    expect(page.locator(".mensaje.ia")).to_have_text(
        "Asistente no disponible. Consultá en caja."
    )

    # No debe filtrarse información técnica al usuario
    contenido = page.locator("#chat-mensajes").inner_text()
    assert "503" not in contenido
    assert "detail" not in contenido
    assert "traceback" not in contenido.lower()
