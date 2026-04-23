"""Modulo de recuperación (retrieval) para el sistema RAG académico.

Responsabilidad principal:
- Recibir una consulta del usuario.
- Convertirla a embedding con OpenAI.
- Consultar ChromaDB para recuperar los top-k chunks mas relevantes.
- Retornar los resultados en el formato requerido por PP1.
"""

from __future__ import annotations

import os
<<<<<<< HEAD
from pathlib import Path
from typing import Any, List, Mapping
=======
from typing import Dict, List
>>>>>>> aef98f5 (PP1: RAG academico base con ingestion, retrieval, generation y demo)

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

# Cargamos .env para leer OPENAI_API_KEY.
load_dotenv()

COLLECTION_NAME = "eif420_corpus"
EMBEDDING_MODEL = "text-embedding-3-small"
<<<<<<< HEAD
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _resolver_ruta(ruta: str) -> Path:
    """Resuelve rutas relativas respecto a la raiz del proyecto rag_academico."""
    path = Path(ruta)
    return path if path.is_absolute() else PROJECT_ROOT / path
=======


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
>>>>>>> aef98f5 (PP1: RAG academico base con ingestion, retrieval, generation y demo)


def recuperar_chunks(
    query: str,
    k: int = 3,
    chroma_dir: str = "chroma_db",
    collection_name: str = COLLECTION_NAME,
<<<<<<< HEAD
) -> List[dict[str, Any]]:
=======
) -> List[Dict]:
>>>>>>> aef98f5 (PP1: RAG academico base con ingestion, retrieval, generation y demo)
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

<<<<<<< HEAD
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("No se encontro OPENAI_API_KEY. Configura un archivo .env.")
=======
    api_key = _validar_api_key(os.getenv("OPENAI_API_KEY"))
>>>>>>> aef98f5 (PP1: RAG academico base con ingestion, retrieval, generation y demo)

    cliente_openai = OpenAI(api_key=api_key)

    # Generamos embedding de la consulta para buscar por similitud vectorial.
    emb_query = cliente_openai.embeddings.create(model=EMBEDDING_MODEL, input=query)
    query_embedding = emb_query.data[0].embedding

<<<<<<< HEAD
    chroma_path = _resolver_ruta(chroma_dir)
    chroma_client = chromadb.PersistentClient(path=str(chroma_path))
=======
    chroma_client = chromadb.PersistentClient(path=chroma_dir)
>>>>>>> aef98f5 (PP1: RAG academico base con ingestion, retrieval, generation y demo)
    collection = chroma_client.get_collection(name=collection_name)

    # distances: menor distancia = mayor similitud.
    resultados = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

<<<<<<< HEAD
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
=======
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
>>>>>>> aef98f5 (PP1: RAG academico base con ingestion, retrieval, generation y demo)
                "score": round(score, 4),
            }
        )

    return salida
