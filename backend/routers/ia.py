# ia.py
# POST /ia/ask — responde preguntas sobre la heladería usando RAG.

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from backend.models import IAQuery
from ia.rag_pipeline import ask_rag

router = APIRouter()


@router.post("/ia/ask")
def ask_ia(query: IAQuery):
    try:
        result = ask_rag(query.query)
        return {"answer": result["answer"], "context": result["context"]}
    except RuntimeError as e:
        # ChromaDB u Ollama no disponibles → el frontend muestra el mensaje en caja
        return JSONResponse(
            status_code=503,
            content={"detail": str(e)},
        )
