# conftest.py — fixtures compartidas para tests de integración UI↔API.
# El fixture `page` lo provee pytest-playwright automáticamente.
# Aquí solo agregamos helpers de navegación y datos del seed.

import pytest

FRONTEND = "http://localhost:3000"
API      = "http://localhost:8000"

# Datos del seed (seed.sql) — no hardcodeamos IDs, sí nombres y reglas
PRODUCTO_MAX1_NOMBRE = "Pote 1/4 kg"     # sabores_max=1
PRODUCTO_MAX4_NOMBRE = "Combo familiar"  # sabores_max=4
TOTAL_SABORES        = 10
SABORES_SIN_TACC     = 8                 # sin_tacc=true en el seed


def ir_a_inicio(page):
    """Navega a la pantalla de inicio y espera que el botón principal sea visible."""
    page.goto(FRONTEND)
    page.locator("text=Hacer pedido").wait_for()


def ir_a_productos(page):
    """Navega hasta la grilla de productos y espera que los cards carguen."""
    ir_a_inicio(page)
    page.locator("text=Hacer pedido").click()
    # Espera el primer card — señal de que GET /productos respondió y renderizó
    page.locator(".card-producto").first.wait_for()


def ir_a_sabores(page, texto_producto=PRODUCTO_MAX1_NOMBRE):
    """Navega hasta la grilla de sabores eligiendo el producto indicado."""
    ir_a_productos(page)
    page.locator(".card-producto", has_text=texto_producto).click()
    # Espera el primer card — señal de que GET /sabores respondió y renderizó
    page.locator(".card-sabor").first.wait_for()


def ir_a_resumen(page, texto_producto=PRODUCTO_MAX1_NOMBRE):
    """Navega hasta la pantalla de resumen con 1 sabor seleccionado."""
    ir_a_sabores(page, texto_producto)
    page.locator(".card-sabor input[type=checkbox]").first.check()
    page.locator("#btn-confirmar-sabores").click()
    page.locator("#screen-resumen").wait_for()
