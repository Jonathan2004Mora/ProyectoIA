"""Modulo de recuperación (retrieval) para el sistema RAG académico.

Responsabilidad principal:
- Recibir una consulta del usuario.
- Convertirla a embedding con OpenAI.
- Consultar ChromaDB para recuperar los top-k chunks mas relevantes.
- Retornar los resultados en el formato requerido por PP1.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List, Mapping

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

# Cargamos .env para leer OPENAI_API_KEY.
load_dotenv()

COLLECTION_NAME = "eif420_corpus"
EMBEDDING_MODEL = "text-embedding-3-small"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _resolver_ruta(ruta: str) -> Path:
    """Resuelve rutas relativas respecto a la raiz del proyecto rag_academico."""
    path = Path(ruta)
    return path if path.is_absolute() else PROJECT_ROOT / path


def recuperar_chunks(
    query: str,
    k: int = 3,
    chroma_dir: str = "chroma_db",
    collection_name: str = COLLECTION_NAME,
) -> List[dict[str, Any]]:
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

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("No se encontro OPENAI_API_KEY. Configura un archivo .env.")

    cliente_openai = OpenAI(api_key=api_key)

    # Generamos embedding de la consulta para buscar por similitud vectorial.
    emb_query = cliente_openai.embeddings.create(model=EMBEDDING_MODEL, input=query)
    query_embedding = emb_query.data[0].embedding

    chroma_path = _resolver_ruta(chroma_dir)
    chroma_client = chromadb.PersistentClient(path=str(chroma_path))
    collection = chroma_client.get_collection(name=collection_name)

    # distances: menor distancia = mayor similitud.
    resultados = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    documentos_raw = resultados.get("documents") or [[]]
    metadatos_raw = resultados.get("metadatas") or [[]]
    distancias_raw = resultados.get("distances") or [[]]

    documentos = documentos_raw[0] if documentos_raw else []
    metadatos = metadatos_raw[0] if metadatos_raw else []
    distancias = distancias_raw[0] if distancias_raw else []

    salida: List[dict[str, Any]] = []
    for texto, meta, distancia in zip(documentos, metadatos, distancias):
        meta_map: Mapping[str, Any] = dict(meta)

        # Convertimos distancia en score interpretable: mas alto = mejor.
        score = 1.0 / (1.0 + float(distancia))

        source_raw = meta_map.get("source", "desconocido")
        source = str(source_raw)

        page_raw = meta_map.get("page", -1)
        if isinstance(page_raw, bool):
            page = -1
        elif isinstance(page_raw, (int, float)):
            page = int(page_raw)
        elif isinstance(page_raw, str) and page_raw.strip().isdigit():
            page = int(page_raw.strip())
        else:
            page = -1

        salida.append(
            {
                "text": texto,
                "source": source,
                "page": page,
                "score": round(score, 4),
            }
        )

    return salida
