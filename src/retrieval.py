"""Modulo de recuperación (retrieval) para el sistema RAG académico.

Responsabilidad principal:
- Recibir una consulta del usuario.
- Convertirla a embedding con OpenAI.
- Consultar ChromaDB para recuperar los top-k chunks mas relevantes.
- Retornar los resultados en el formato requerido por PP1.
"""

from __future__ import annotations

import os
from typing import Dict, List

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

# Cargamos .env para leer OPENAI_API_KEY.
load_dotenv()

COLLECTION_NAME = "eif420_corpus"
EMBEDDING_MODEL = "text-embedding-3-small"


def _validar_api_key(api_key: str | None) -> str:
    """Valida OPENAI_API_KEY para evitar errores de autenticacion comunes."""
    if not api_key:
        raise ValueError("No se encontro OPENAI_API_KEY. Configura un archivo .env.")

    clave = api_key.strip()
    placeholders = {"tu_api_key_aqui", "your_api_key_here", "api_key", "xxx"}
    if clave.lower() in placeholders or clave.lower().startswith("tu_api_key"):
        raise ValueError(
            "OPENAI_API_KEY contiene un placeholder. Reemplaza el valor en .env "
            "por una clave real de https://platform.openai.com/api-keys"
        )

    return clave


def recuperar_chunks(
    query: str,
    k: int = 3,
    chroma_dir: str = "chroma_db",
    collection_name: str = COLLECTION_NAME,
) -> List[Dict]:
    """Recupera top-k chunks relevantes y retorna lista de dicts.

    Formato de salida por item:
    {
      "text": str,
      "source": str,
      "page": int,
      "score": float
    }
    """
    if not query.strip():
        raise ValueError("La consulta no puede estar vacia.")

    api_key = _validar_api_key(os.getenv("OPENAI_API_KEY"))

    cliente_openai = OpenAI(api_key=api_key)

    # Generamos embedding de la consulta para buscar por similitud vectorial.
    emb_query = cliente_openai.embeddings.create(model=EMBEDDING_MODEL, input=query)
    query_embedding = emb_query.data[0].embedding

    chroma_client = chromadb.PersistentClient(path=chroma_dir)
    collection = chroma_client.get_collection(name=collection_name)

    # distances: menor distancia = mayor similitud.
    resultados = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    documentos = resultados.get("documents", [[]])[0]
    metadatos = resultados.get("metadatas", [[]])[0]
    distancias = resultados.get("distances", [[]])[0]

    salida: List[Dict] = []
    for texto, meta, distancia in zip(documentos, metadatos, distancias):
        # Convertimos distancia en score interpretable: mas alto = mejor.
        score = 1.0 / (1.0 + float(distancia))
        salida.append(
            {
                "text": texto,
                "source": meta.get("source", "desconocido"),
                "page": int(meta.get("page", -1)),
                "score": round(score, 4),
            }
        )

    return salida
