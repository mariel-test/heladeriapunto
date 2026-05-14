"""
tests/ia/test_rag_pipeline.py — TC-IA01 a TC-IA09

Tests unitarios del pipeline RAG. ChromaDB y Ollama son mockeados
para que los tests sean deterministas y no dependan de infraestructura.

Correr:
  pytest tests/ia/test_rag_pipeline.py -v
"""

import pytest
import requests as req_lib
from unittest.mock import MagicMock, patch

from ia.rag_pipeline import ask_rag, TOP_K
from chromadb.errors import ChromaError


# ── Helpers ───────────────────────────────────────────────────────────────────

CHUNKS = [
    "Tenemos sabores veganos: frutilla, limón, maracuyá y menta.",
    "Todos los sabores de agua son aptos para veganos y celíacos.",
    "Consultá en caja por más información sobre ingredientes.",
]
ANSWER = "Sí, tenemos sabores 100% veganos."


def _mock_collection(chunks=None):
    col = MagicMock()
    col.query.return_value = {
        "documents": [CHUNKS if chunks is None else chunks],
        "metadatas": [[]],
        "distances": [[0.1, 0.2, 0.3]],
    }
    return col


def _mock_ollama_ok(answer=ANSWER):
    resp = MagicMock()
    resp.json.return_value = {"response": answer}
    resp.raise_for_status = MagicMock()
    return resp


# ── TC-IA01 ───────────────────────────────────────────────────────────────────

@patch("ia.rag_pipeline.requests.post")
@patch("ia.rag_pipeline._get_chroma_collection")
def test_ia01_ask_rag_retorna_answer_y_context(mock_col, mock_post):
    """TC-IA01: ask_rag exitoso devuelve dict con 'answer' (str) y 'context' (list)."""
    mock_col.return_value = _mock_collection()
    mock_post.return_value = _mock_ollama_ok()

    result = ask_rag("¿tienen opciones veganas?")

    assert isinstance(result, dict)
    assert isinstance(result["answer"], str) and len(result["answer"]) > 0
    assert isinstance(result["context"], list)


# ── TC-IA02 ───────────────────────────────────────────────────────────────────

@patch("ia.rag_pipeline.requests.post")
@patch("ia.rag_pipeline._get_chroma_collection")
def test_ia02_context_tiene_exactamente_top_k_chunks(mock_col, mock_post):
    """TC-IA02: el campo 'context' tiene exactamente TOP_K=3 elementos."""
    mock_col.return_value = _mock_collection()
    mock_post.return_value = _mock_ollama_ok()

    result = ask_rag("¿tienen opciones veganas?")

    assert len(result["context"]) == TOP_K


# ── TC-IA03 ───────────────────────────────────────────────────────────────────

@patch("ia.rag_pipeline.requests.post")
@patch("ia.rag_pipeline._get_chroma_collection")
def test_ia03_prompt_incluye_instruccion_anti_alucinacion(mock_col, mock_post):
    """TC-IA03: el prompt enviado a Ollama contiene la instrucción anti-alucinación."""
    mock_col.return_value = _mock_collection()
    mock_post.return_value = _mock_ollama_ok()

    ask_rag("¿tienen opciones veganas?")

    payload = mock_post.call_args.kwargs["json"]
    prompt = payload["prompt"]
    assert "Consultá en caja" in prompt
    assert "No tengo información" in prompt


# ── TC-IA04 ───────────────────────────────────────────────────────────────────

@patch("ia.rag_pipeline.requests.post")
@patch("ia.rag_pipeline._get_chroma_collection")
def test_ia04_sin_chunks_retorna_fallback_sin_llamar_ollama(mock_col, mock_post):
    """TC-IA04: sin chunks de ChromaDB, devuelve fallback y no llama a Ollama."""
    mock_col.return_value = _mock_collection(chunks=[])

    result = ask_rag("¿hacen delivery?")

    assert result["answer"] == "No tengo información sobre eso. Consultá en caja."
    assert result["context"] == []
    mock_post.assert_not_called()


# ── TC-IA05 ───────────────────────────────────────────────────────────────────

@patch("ia.rag_pipeline.chromadb.HttpClient")
def test_ia05_chromadb_no_disponible_lanza_runtime_error(mock_client):
    """TC-IA05: si heartbeat() lanza ChromaError, ask_rag propaga RuntimeError con 'ChromaDB'."""
    mock_client.return_value.heartbeat.side_effect = ChromaError("connection refused")

    with pytest.raises(RuntimeError) as exc:
        ask_rag("¿tienen opciones veganas?")

    assert "ChromaDB" in str(exc.value)


# ── TC-IA06 ───────────────────────────────────────────────────────────────────

@patch("ia.rag_pipeline.requests.post")
@patch("ia.rag_pipeline._get_chroma_collection")
def test_ia06_ollama_conexion_fallida_lanza_runtime_error(mock_col, mock_post):
    """TC-IA06: si requests.post lanza ConnectionError, ask_rag propaga RuntimeError con 'Ollama'."""
    mock_col.return_value = _mock_collection()
    mock_post.side_effect = req_lib.exceptions.ConnectionError("connection refused")

    with pytest.raises(RuntimeError) as exc:
        ask_rag("¿tienen opciones veganas?")

    assert "Ollama" in str(exc.value)


# ── TC-IA07 ───────────────────────────────────────────────────────────────────

@patch("ia.rag_pipeline.requests.post")
@patch("ia.rag_pipeline._get_chroma_collection")
def test_ia07_ollama_timeout_lanza_runtime_error(mock_col, mock_post):
    """TC-IA07: si requests.post lanza Timeout, ask_rag propaga RuntimeError con 'timeout'."""
    mock_col.return_value = _mock_collection()
    mock_post.side_effect = req_lib.exceptions.Timeout()

    with pytest.raises(RuntimeError) as exc:
        ask_rag("¿tienen opciones veganas?")

    assert "timeout" in str(exc.value).lower()


# ── TC-IA08 ───────────────────────────────────────────────────────────────────

@patch("backend.routers.ia.ask_rag")
def test_ia08_router_retorna_200_con_answer_y_context(mock_ask_rag):
    """TC-IA08: POST /ia/ask con ask_rag mockeado devuelve 200 con answer y context."""
    from fastapi.testclient import TestClient
    from backend.main import app

    mock_ask_rag.return_value = {"answer": ANSWER, "context": CHUNKS}

    client = TestClient(app)
    res = client.post("/ia/ask", json={"query": "¿tienen veganos?"})

    assert res.status_code == 200
    data = res.json()
    assert data["answer"] == ANSWER
    assert isinstance(data["context"], list)


# ── TC-IA09 ───────────────────────────────────────────────────────────────────

@patch("backend.routers.ia.ask_rag")
def test_ia09_router_retorna_503_cuando_ia_down(mock_ask_rag):
    """TC-IA09: cuando ask_rag lanza RuntimeError, el router devuelve 503 con 'detail'."""
    from fastapi.testclient import TestClient
    from backend.main import app

    mock_ask_rag.side_effect = RuntimeError("ChromaDB no disponible")

    client = TestClient(app)
    res = client.post("/ia/ask", json={"query": "¿tienen veganos?"})

    assert res.status_code == 503
    data = res.json()
    assert "detail" in data
    assert "ChromaDB" in data["detail"]
