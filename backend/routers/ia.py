# ia.py
# POST /ia/ask — stub hasta el paso 7 (rag_pipeline.py).
# Devuelve 503 con mensaje amigable para que el frontend lo muestre en caja.
# La implementación real vive en ia/rag_pipeline.py.

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from backend.models import IAQuery

router = APIRouter()


@router.post("/ia/ask")
def ask_ia(query: IAQuery):
    return JSONResponse(
        status_code=503,
        content={"detail": "Asistente no disponible. Consultá en caja."},
    )
