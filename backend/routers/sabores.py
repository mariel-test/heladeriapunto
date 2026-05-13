# sabores.py
# GET /sabores — lista completa con filtros opcionales por categoria y sin_tacc.
# Construimos el WHERE dinámicamente para no duplicar queries.

from fastapi import APIRouter, Query
from typing import Optional
from backend.database import get_cursor
from backend.models import SaborOut

router = APIRouter()


@router.get("/sabores", response_model=list[SaborOut])
def get_sabores(
    categoria: Optional[str] = Query(None, description="crema | agua"),
    sin_tacc: Optional[bool] = Query(None),
):
    conditions: list[str] = []
    params: list = []

    if categoria is not None:
        conditions.append("categoria = %s")
        params.append(categoria)

    if sin_tacc is not None:
        conditions.append("sin_tacc = %s")
        params.append(sin_tacc)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    with get_cursor() as cur:
        cur.execute(f"SELECT * FROM sabores {where} ORDER BY id", params)
        return cur.fetchall()
