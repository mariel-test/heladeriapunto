# pedidos.py
# POST /pedido — crea un pedido validando todas las reglas de negocio
# GET  /pedido/{id} — detalle del pedido
#
# Reglas de negocio validadas acá (no en el frontend):
#   1. El producto debe existir
#   2. Los sabores deben existir en la BD
#   3. La cantidad no puede superar sabores_max del producto
#   4. El total lo calcula el backend usando el precio del producto

import json
from fastapi import APIRouter, HTTPException
from backend.database import get_cursor
from backend.models import PedidoIn, PedidoOut

router = APIRouter()


@router.post("/pedido", response_model=PedidoOut, status_code=201)
def crear_pedido(pedido: PedidoIn):
    with get_cursor() as cur:

        cur.execute(
            "SELECT id, sabores_max, precio FROM productos WHERE id = %s",
            (pedido.producto_id,),
        )
        producto = cur.fetchone()
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        if len(pedido.sabores_elegidos) > producto["sabores_max"]:
            raise HTTPException(
                status_code=422,
                detail=f"Este producto permite máximo {producto['sabores_max']} sabor(es), "
                       f"recibido: {len(pedido.sabores_elegidos)}",
            )

        ids_elegidos = [s.id for s in pedido.sabores_elegidos]
        cur.execute(
            "SELECT id FROM sabores WHERE id = ANY(%s)",
            (ids_elegidos,),
        )
        ids_encontrados = {row["id"] for row in cur.fetchall()}
        ids_invalidos = sorted(set(ids_elegidos) - ids_encontrados)
        if ids_invalidos:
            raise HTTPException(
                status_code=422,
                detail=f"Sabores no encontrados: {ids_invalidos}",
            )

        sabores_json = json.dumps([s.model_dump() for s in pedido.sabores_elegidos])
        total = float(producto["precio"])

        cur.execute(
            """
            INSERT INTO pedidos (producto_id, sabores_elegidos, total, estado)
            VALUES (%s, %s::jsonb, %s, 'pendiente')
            RETURNING *
            """,
            (pedido.producto_id, sabores_json, total),
        )
        return cur.fetchone()


@router.get("/pedido/{pedido_id}", response_model=PedidoOut)
def get_pedido(pedido_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM pedidos WHERE id = %s", (pedido_id,))
        row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    return row
