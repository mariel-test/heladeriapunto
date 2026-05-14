"""
ingest.py — Carga el FAQ de la heladería en ChromaDB.

Ejecutar una sola vez (o cada vez que cambie el FAQ):
    python -m ia.ingest

Usa el modelo de embeddings por defecto de ChromaDB (all-MiniLM-L6-v2),
que corre localmente sin necesidad de Ollama ni API keys.
"""

import json
from pathlib import Path

import chromadb

CHROMA_HOST = "localhost"
CHROMA_PORT = 8001
COLLECTION_NAME = "heladeria_faq"
FAQ_PATH = Path(__file__).parent / "knowledge_base" / "heladeria_faq.json"


def main() -> None:
    # Conexión al servidor ChromaDB levantado con `chroma run --host ... --port 8001`
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)

    # get_or_create evita duplicar la colección si el script se corre más de una vez
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        # Sin metadata de distancia explícita: ChromaDB usa coseno por defecto,
        # que es lo más adecuado para comparar texto semántico
    )

    with open(FAQ_PATH, encoding="utf-8") as f:
        faq = json.load(f)

    # Verificamos qué IDs ya están en la colección para no duplicar documentos
    existing = set(collection.get(ids=[item["id"] for item in faq])["ids"])
    nuevos = [item for item in faq if item["id"] not in existing]

    if not nuevos:
        print(f"No hay documentos nuevos. La colección '{COLLECTION_NAME}' ya tiene {len(faq)} entradas.")
        return

    collection.add(
        ids=[item["id"] for item in nuevos],
        # El documento que se embeddea y sobre el que se hace la búsqueda semántica
        # es la combinación pregunta + respuesta para maximizar cobertura
        documents=[f"{item['pregunta']} {item['respuesta']}" for item in nuevos],
        metadatas=[
            {
                "id": item["id"],
                "categoria": item["categoria"],
                "pregunta": item["pregunta"],
            }
            for item in nuevos
        ],
    )

    print(f"Indexados {len(nuevos)} documentos nuevos en la colección '{COLLECTION_NAME}'.")
    print(f"Total en colección: {collection.count()}")


if __name__ == "__main__":
    main()
