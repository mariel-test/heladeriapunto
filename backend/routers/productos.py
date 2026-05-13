# productos.py
# GET /productos  — lista completa
# GET /productos/{id} — detalle, 404 si no existe

from fastapi import APIRouter, HTTPException
from backend.database import get_cursor
from backend.models import ProductoOut

router = APIRouter()


@router.get("/productos", response_model=list[ProductoOut])
def get_productos():
    with get_cursor() as cur:
        cur.execute("SELECT * FROM productos ORDER BY id")
        return cur.fetchall()


@router.get("/productos/{producto_id}", response_model=ProductoOut)
def get_producto(producto_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM productos WHERE id = %s", (producto_id,))
        row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return row
