"""
tests/ui/test_integracion_ui_api.py  —  TC-INT01 a TC-INT10

Integración UI ↔ API: verifica que cada componente del frontend llame al
endpoint correcto y renderice la respuesta de forma adecuada.

Requisitos para correr:
  - frontend en http://localhost:3000  (nginx sirve frontend/)
  - backend  en http://localhost:8000  (uvicorn)
  - BD sembrada con seed.sql
  - playwright install chromium  (una sola vez)

Correr:
  pytest tests/ui/test_integracion_ui_api.py -v
"""

import json
import time

import pytest
from playwright.sync_api import Page, Route, expect

FRONTEND             = "http://localhost:3000"
API                  = "http://localhost:8000"
PRODUCTO_MAX1_NOMBRE = "Pote 1/4 kg"
TOTAL_SABORES        = 10
SABORES_SIN_TACC     = 8


def ir_a_inicio(page: Page):
    page.goto(FRONTEND)
    page.locator("text=Hacer pedido").wait_for()


def ir_a_productos(page: Page):
    ir_a_inicio(page)
    page.locator("text=Hacer pedido").click()
    page.locator(".card-producto").first.wait_for()


def ir_a_sabores(page: Page, texto_producto: str = PRODUCTO_MAX1_NOMBRE):
    ir_a_productos(page)
    page.locator(".card-producto", has_text=texto_producto).click()
    page.locator(".card-sabor").first.wait_for()


def ir_a_resumen(page: Page, texto_producto: str = PRODUCTO_MAX1_NOMBRE):
    ir_a_sabores(page, texto_producto)
    page.locator(".card-sabor input[type=checkbox]").first.check()
    page.locator("#btn-confirmar-sabores").click()
    page.locator("#screen-resumen").wait_for()


# ── TC-INT01 ──────────────────────────────────────────────────────────────────

def test_int01_productos_se_cargan_desde_api(page: Page):
    """TC-INT01: Al hacer clic en 'Hacer pedido' el frontend dispara GET /productos
    y renderiza exactamente 5 tarjetas con nombre y precio."""
    ir_a_inicio(page)

    with page.expect_request(f"{API}/productos") as req_info:
        page.locator("text=Hacer pedido").click()

    assert req_info.value.method == "GET"

    cards = page.locator(".card-producto")
    expect(cards).to_have_count(5)

    # Cada card expone nombre (.nombre) y precio (.precio con "$")
    for i in range(5):
        expect(cards.nth(i).locator(".nombre")).not_to_be_empty()
        expect(cards.nth(i).locator(".precio")).to_contain_text("$")


# ── TC-INT02 ──────────────────────────────────────────────────────────────────

def test_int02_sabores_se_cargan_desde_api_al_seleccionar_producto(page: Page):
    """TC-INT02: Al seleccionar un producto el frontend dispara GET /sabores
    y renderiza las 10 tarjetas de sabor con los badges Sin TACC correctos."""
    ir_a_productos(page)

    with page.expect_request(f"{API}/sabores") as req_info:
        page.locator(".card-producto", has_text=PRODUCTO_MAX1_NOMBRE).click()

    assert req_info.value.method == "GET"

    # Seed: 10 sabores
    expect(page.locator(".card-sabor")).to_have_count(TOTAL_SABORES)

    # El título de la pantalla muestra el nombre del producto y su sabores_max
    expect(page.locator("#titulo-sabores")).to_contain_text(PRODUCTO_MAX1_NOMBRE)
    expect(page.locator("#titulo-sabores")).to_contain_text("1")

    # Hay tarjetas con badge "TACC" (8 del seed) y tarjetas sin él (2)
    expect(page.locator(".card-sabor .badge").first).to_be_visible()
    expect(page.locator(".card-sabor .badge").first).to_have_text("TACC")


# ── TC-INT03 ──────────────────────────────────────────────────────────────────

def test_int03_filtro_sin_tacc_filtra_en_cliente_sin_nueva_request(page: Page):
    """TC-INT03: El checkbox 'Filtrar sin TACC' filtra la lista en memoria
    (todosLosSabores) sin disparar una nueva request a la API."""
    ir_a_sabores(page)

    # Registrar requests DESPUÉS de que los sabores ya cargaron
    requests_post_carga = []
    page.on(
        "request",
        lambda r: requests_post_carga.append(r.url) if "/sabores" in r.url else None,
    )

    # Activar filtro — debe mostrar solo los 8 sin TACC del seed
    page.locator("#filtro-sin-tacc").check()
    expect(page.locator(".card-sabor")).to_have_count(SABORES_SIN_TACC)

    # Sin TACC activo: ninguna tarjeta debe mostrar "Brownie" ni "Tramontana"
    # (únicos sabores con sin_tacc=false en el seed)
    for nombre in ["Brownie", "Tramontana"]:
        expect(page.locator(".card-sabor", has_text=nombre)).not_to_be_visible()

    # El filtro NO debe haber disparado ninguna request a /sabores
    assert requests_post_carga == [], (
        f"filtrarSabores() no debe llamar a la API — requests inesperadas: {requests_post_carga}"
    )

    # Desactivar restaura los 10 sabores
    page.locator("#filtro-sin-tacc").uncheck()
    expect(page.locator(".card-sabor")).to_have_count(TOTAL_SABORES)


# ── TC-INT04 ──────────────────────────────────────────────────────────────────

def test_int04_sabores_max_deshabilita_checkboxes_en_ui(page: Page):
    """TC-INT04: Con sabores_max=1, al elegir 1 sabor la UI deshabilita
    los demás checkboxes sin llamar al backend."""
    ir_a_sabores(page, PRODUCTO_MAX1_NOMBRE)

    # Antes de seleccionar: el botón Confirmar está deshabilitado
    expect(page.locator("#btn-confirmar-sabores")).to_be_disabled()
    expect(page.locator("#contador-sabores")).to_have_text("0 / 1")

    # Seleccionar el primer sabor (llena el cupo de 1)
    page.locator(".card-sabor input[type=checkbox]").first.check()

    # Contador: "1 / 1"
    expect(page.locator("#contador-sabores")).to_have_text("1 / 1")

    # Botón Confirmar habilitado
    expect(page.locator("#btn-confirmar-sabores")).to_be_enabled()

    # Los checkboxes no seleccionados deben estar disabled (sabores_max alcanzado)
    no_seleccionados = page.locator(".card-sabor input[type=checkbox]:not(:checked)")
    count = no_seleccionados.count()
    assert count == TOTAL_SABORES - 1, f"Deben quedar {TOTAL_SABORES - 1} checkboxes deshabilitados"
    for i in range(count):
        expect(no_seleccionados.nth(i)).to_be_disabled()


# ── TC-INT05 ──────────────────────────────────────────────────────────────────

def test_int05_formulario_pedido_envia_payload_correcto(page: Page):
    """TC-INT05: Al confirmar el pedido el frontend hace POST /pedido con
    producto_id (int) y sabores_elegidos (array con {id, nombre})."""
    ir_a_resumen(page, PRODUCTO_MAX1_NOMBRE)

    with page.expect_request(f"{API}/pedido") as req_info:
        page.locator("#btn-confirmar-pedido").click()

    request = req_info.value
    assert request.method == "POST"
    assert "application/json" in request.headers.get("content-type", "")

    body = json.loads(request.post_data)

    assert isinstance(body["producto_id"], int), (
        f"producto_id debe ser int, recibido: {type(body['producto_id'])}"
    )
    assert isinstance(body["sabores_elegidos"], list)
    assert len(body["sabores_elegidos"]) >= 1

    sabor = body["sabores_elegidos"][0]
    assert "id" in sabor and isinstance(sabor["id"], int)
    assert "nombre" in sabor and isinstance(sabor["nombre"], str)


# ── TC-INT06 ──────────────────────────────────────────────────────────────────

def test_int06_confirmacion_muestra_id_del_backend(page: Page):
    """TC-INT06: La pantalla de confirmación muestra el id del pedido retornado
    por el backend — no un id generado en el frontend."""
    ir_a_resumen(page, PRODUCTO_MAX1_NOMBRE)

    pedido_id_api: dict = {}

    def capturar_respuesta(route: Route):
        response = route.fetch()
        pedido_id_api["id"] = response.json().get("id")
        route.fulfill(response=response)

    page.route(f"{API}/pedido", capturar_respuesta)
    page.locator("#btn-confirmar-pedido").click()

    # Pantalla de confirmación visible
    expect(page.locator(".confirmado")).to_be_visible()
    expect(page.locator(".pedido-id")).to_be_visible()

    texto_pedido = page.locator(".pedido-id").inner_text()
    assert str(pedido_id_api["id"]) in texto_pedido, (
        f"UI muestra '{texto_pedido}' pero el backend devolvió id={pedido_id_api['id']}"
    )

    # El botón "Nuevo pedido" reemplaza al de confirmar (no hay doble submit)
    expect(page.locator("#btn-nuevo-pedido")).to_be_visible()
    expect(page.locator("#btn-confirmar-pedido")).not_to_be_visible()


# ── TC-INT07 ──────────────────────────────────────────────────────────────────

def test_int07_error_422_muestra_alerta_amigable_no_json_crudo(page: Page):
    """TC-INT07: Cuando POST /pedido devuelve 422, la UI muestra un alert con
    el mensaje de error — no el JSON crudo ni un stack trace."""
    ir_a_resumen(page, PRODUCTO_MAX1_NOMBRE)

    page.route(
        f"{API}/pedido",
        lambda route: route.fulfill(
            status=422,
            content_type="application/json",
            body=json.dumps({"detail": "Límite de sabores superado para este producto"}),
        ),
    )

    dialogs: list[str] = []
    page.on("dialog", lambda d: (dialogs.append(d.message), d.accept()))

    page.locator("#btn-confirmar-pedido").click()
    page.wait_for_timeout(800)

    assert len(dialogs) == 1, f"Debe mostrarse 1 alert, se dispararon {len(dialogs)}"

    mensaje = dialogs[0]
    assert "Error" in mensaje or "error" in mensaje.lower(), (
        f"El alert debe indicar un error: '{mensaje}'"
    )
    # No debe exponer el JSON crudo al usuario
    assert "{" not in mensaje, f"El alert no debe mostrar JSON crudo: '{mensaje}'"
    assert "detail" not in mensaje.lower(), (
        f"El alert no debe exponer claves internas del API: '{mensaje}'"
    )


# ── TC-INT08 ──────────────────────────────────────────────────────────────────

def test_int08_chat_envia_query_exacta_a_ia_ask(page: Page):
    """TC-INT08: Al enviar un mensaje en el chat el frontend hace POST /ia/ask
    con body {"query": "<texto exacto del input>"} y Content-Type application/json."""
    ir_a_inicio(page)

    page.locator("text=Consultar").click()
    expect(page.locator("#chat-area")).to_be_visible()

    # Mockear para que el test no dependa de que Ollama responda rápido
    page.route(
        f"{API}/ia/ask",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"answer": "Respuesta de prueba.", "context": []}),
        ),
    )

    texto = "¿tienen opciones veganas?"
    page.fill("#chat-input", texto)

    with page.expect_request(f"{API}/ia/ask") as req_info:
        page.locator("text=Enviar").click()

    request = req_info.value
    assert request.method == "POST"
    assert "application/json" in request.headers.get("content-type", "")

    body = json.loads(request.post_data)
    assert body == {"query": texto}, (
        f"Payload incorrecto — esperado: {{'query': '{texto}'}}, recibido: {body}"
    )


# ── TC-INT09 ──────────────────────────────────────────────────────────────────

def test_int09_chat_muestra_solo_answer_no_expone_context(page: Page):
    """TC-INT09: El chat renderiza únicamente el campo 'answer' de la respuesta.
    El array 'context' (chunks internos del RAG) no debe ser visible al usuario."""
    ir_a_inicio(page)

    page.locator("text=Consultar").click()
    expect(page.locator("#chat-area")).to_be_visible()

    answer_esperado  = "Sí, tenemos sabores 100% veganos en la línea de agua."
    chunk_interno    = "CHUNK_INTERNO_NO_VISIBLE_faq_04"

    page.route(
        f"{API}/ia/ask",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({
                "answer":  answer_esperado,
                "context": [chunk_interno, "otro chunk interno que no debe verse"],
            }),
        ),
    )

    page.fill("#chat-input", "vegano")
    page.locator("text=Enviar").click()

    # El answer debe aparecer como burbuja del asistente
    expect(page.locator(".mensaje.ia")).to_have_text(answer_esperado)

    # El context no debe aparecer en ninguna parte del área de chat
    contenido_chat = page.locator("#chat-mensajes").inner_text()
    assert chunk_interno not in contenido_chat, (
        "El array 'context' (chunks del RAG) no debe exponerse al usuario"
    )


# ── TC-INT10 ──────────────────────────────────────────────────────────────────

def test_int10_loading_visible_mientras_api_responde(page: Page):
    """TC-INT10: Mientras GET /productos no resolvió, la UI muestra el texto
    'Cargando...' en el grid. Al recibir la respuesta, desaparece."""
    ir_a_inicio(page)

    # Interceptar con retardo para poder observar el estado intermedio
    def respuesta_con_retardo(route: Route):
        time.sleep(0.8)   # pausa real para que el DOM con "Cargando..." sea visible
        route.continue_()

    page.route(f"{API}/productos", respuesta_con_retardo)
    page.locator("text=Hacer pedido").click()

    # Durante la espera la UI muestra el indicador de carga
    expect(page.locator(".msg-cargando")).to_be_visible()

    # Cuando resuelve: cards visibles y "Cargando..." desaparece
    expect(page.locator(".card-producto").first).to_be_visible()
    expect(page.locator(".msg-cargando")).not_to_be_visible()
