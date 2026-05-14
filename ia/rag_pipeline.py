"""
rag_pipeline.py — Retrieval-Augmented Generation sobre el FAQ de la heladería.

Flujo: query → ChromaDB (recuperar chunks relevantes) → Ollama (generar respuesta)

Sin LangChain: todas las llamadas son directas a chromadb y requests.
"""

import requests
import chromadb
from chromadb.errors import ChromaError

CHROMA_HOST = "localhost"
CHROMA_PORT = 8001
COLLECTION_NAME = "heladeria_faq"

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"

# Cuántos chunks del FAQ se le pasan al LLM como contexto.
# 3 es suficiente para respuestas precisas sin inflar el prompt.
TOP_K = 3

# Instrucción de sistema que previene alucinaciones.
# Está en español porque el modelo responde en el idioma del prompt.
SYSTEM_PROMPT = (
    "Sos el asistente virtual de Frío & Punto, una heladería artesanal en Córdoba, Argentina. "
    "Respondé SOLO con información del contexto provisto. "
    "Si la pregunta no tiene respuesta en el contexto, "
    "decí exactamente: 'No tengo información sobre eso. Consultá en caja.' "
    "No inventes información."
)


def _get_chroma_collection():
    """Conecta a ChromaDB y devuelve la colección del FAQ."""
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        # heartbeat() lanza excepción si el servidor no responde
        client.heartbeat()
        return client.get_collection(name=COLLECTION_NAME)
    except ChromaError as e:
        raise RuntimeError(
            f"No se puede conectar a ChromaDB en {CHROMA_HOST}:{CHROMA_PORT}. "
            f"Verificá que el servidor esté corriendo. Detalle: {e}"
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"Error inesperado al conectar con ChromaDB: {e}"
        ) from e


def _query_ollama(prompt: str) -> str:
    """Llama a Ollama con el prompt completo y devuelve el texto generado."""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        # stream: false para recibir la respuesta completa en un solo JSON
        "stream": False,
    }
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["response"].strip()
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"No se puede conectar a Ollama en {OLLAMA_BASE_URL}. "
            f"Verificá que Ollama esté corriendo y el modelo '{OLLAMA_MODEL}' descargado. Detalle: {e}"
        ) from e
    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"Ollama tardó demasiado en responder (timeout 60s). "
            f"El modelo '{OLLAMA_MODEL}' puede estar cargando por primera vez."
        )
    except (requests.exceptions.HTTPError, KeyError) as e:
        raise RuntimeError(f"Error en la respuesta de Ollama: {e}") from e


def ask_rag(query: str) -> dict:
    """
    Punto de entrada principal. Recibe una pregunta en lenguaje natural
    y devuelve la respuesta generada por el LLM junto con los chunks usados.

    Returns:
        {"answer": str, "context": list[str]}

    Raises:
        RuntimeError si ChromaDB u Ollama no están disponibles.
    """
    collection = _get_chroma_collection()

    results = collection.query(
        query_texts=[query],
        n_results=TOP_K,
        # Incluimos el documento original para mostrarlo como contexto en la respuesta
        include=["documents", "metadatas", "distances"],
    )

    # results["documents"] es una lista de listas (una por query); tomamos la primera
    chunks: list[str] = results["documents"][0]

    if not chunks:
        return {
            "answer": "No tengo información sobre eso. Consultá en caja.",
            "context": [],
        }

    context_block = "\n\n".join(
        f"[{i+1}] {chunk}" for i, chunk in enumerate(chunks)
    )

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Contexto:\n{context_block}\n\n"
        f"Pregunta: {query}\n\n"
        f"Respuesta:"
    )

    answer = _query_ollama(prompt)

    return {
        "answer": answer,
        "context": chunks,
    }
