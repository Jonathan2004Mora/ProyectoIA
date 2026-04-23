"""Modulo de ingestión para el sistema RAG académico.

Responsabilidad principal:
1) Leer todos los PDFs de la carpeta corpus/.
2) Extraer texto por pagina.
3) Dividir el texto en fragmentos (chunks) controlados.
4) Crear embeddings con OpenAI.
5) Guardar chunks + metadatos + embeddings en ChromaDB persistente.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Tuple

import chromadb
import numpy as np
from chromadb.api.types import Embedding, Metadata
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from pypdf import PdfReader

# Cargamos variables de entorno desde .env para acceder a OPENAI_API_KEY.
load_dotenv()

# Constantes de diseño del proyecto.
COLLECTION_NAME = "eif420_corpus"
EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _resolver_ruta(ruta: str) -> Path:
    """Resuelve rutas relativas respecto a la raiz del proyecto rag_academico."""
    path = Path(ruta)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _validar_api_key(api_key: str | None) -> str:
    """Valida OPENAI_API_KEY y retorna la clave limpia.

    Este chequeo evita errores de autenticacion comunes cuando en .env
    se deja un valor de ejemplo como "tu_api_key_aqui".
    """
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


def _extraer_paginas_pdf(pdf_path: Path) -> List[Tuple[int, str]]:
    """Extrae texto pagina por pagina desde un PDF.

    Retorna una lista de tuplas: (numero_pagina, texto_pagina).
    Si una pagina no tiene texto extraible, se omite para evitar ruido.
    """
    reader = PdfReader(str(pdf_path))
    paginas: List[Tuple[int, str]] = []

    for page_idx, page in enumerate(reader.pages, start=1):
        # extract_text puede retornar None en PDFs escaneados o dañados.
        texto = page.extract_text() or ""
        texto_limpio = texto.strip()
        if texto_limpio:
            paginas.append((page_idx, texto_limpio))

    return paginas


def _crear_chunks(
    nombre_archivo: str,
    paginas: List[Tuple[int, str]],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> Tuple[List[str], List[Metadata], List[str]]:
    """Genera chunks a partir del texto por paginas y prepara metadatos/ids.

    Metadatos requeridos por el enunciado:
    - source: nombre del archivo
    - page: numero de pagina
    - chunk: numero de chunk dentro de la pagina
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    documentos: List[str] = []
    metadatos: List[Metadata] = []
    ids: List[str] = []

    for numero_pagina, texto_pagina in paginas:
        chunks_pagina = splitter.split_text(texto_pagina)
        for numero_chunk, chunk in enumerate(chunks_pagina):
            # Se utiliza un id determinista para poder hacer upsert sin duplicar.
            chunk_id = f"{nombre_archivo}-p{numero_pagina}-c{numero_chunk}"

            documentos.append(chunk)
            metadatos.append(
                {
                    "source": nombre_archivo,
                    "page": numero_pagina,
                    "chunk": numero_chunk,
                }
            )
            ids.append(chunk_id)

    return documentos, metadatos, ids


def _crear_embeddings(textos: List[str], cliente_openai: OpenAI) -> List[Embedding]:
    """Crea embeddings en lotes para mejorar rendimiento y estabilidad.

    Chroma permite almacenar embeddings precalculados, lo cual nos da control
    sobre el modelo de embeddings y consistencia con retrieval.
    """
    if not textos:
        return []

    embeddings: List[Embedding] = []
    batch_size = 64

    for i in range(0, len(textos), batch_size):
        batch = textos[i : i + batch_size]
        respuesta = cliente_openai.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        for item in respuesta.data:
            # Chroma tipa Embedding como ndarray[int32 | float32].
            vector: Embedding = np.asarray(item.embedding, dtype=np.float32)
            embeddings.append(vector)

    return embeddings


def ingestar_corpus(
    corpus_dir: str = "corpus",
    chroma_dir: str = "chroma_db",
    collection_name: str = COLLECTION_NAME,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> Dict[str, int]:
    """Ingresa todos los PDFs en ChromaDB y retorna estadisticas del proceso.

    Args:
        corpus_dir: Carpeta donde se encuentran los PDFs.
        chroma_dir: Carpeta de persistencia de ChromaDB.
        collection_name: Nombre de la coleccion vectorial.
        chunk_size: Tamano maximo de cada fragmento de texto.
        chunk_overlap: Solapamiento entre fragmentos consecutivos.
    """
    api_key = _validar_api_key(os.getenv("OPENAI_API_KEY"))

    if chunk_size <= 0:
        raise ValueError("chunk_size debe ser un entero positivo.")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap no puede ser negativo.")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap debe ser menor que chunk_size.")

    cliente_openai = OpenAI(api_key=api_key)

    carpeta_corpus = _resolver_ruta(corpus_dir)
    if not carpeta_corpus.exists():
        raise FileNotFoundError(f"No existe la carpeta de corpus: {carpeta_corpus}")

    pdfs = sorted(carpeta_corpus.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError("No se encontraron PDFs en la carpeta corpus/.)")

    todos_los_documentos: List[str] = []
    todos_los_metadatos: List[Metadata] = []
    todos_los_ids: List[str] = []

    for pdf_path in pdfs:
        paginas = _extraer_paginas_pdf(pdf_path)
        documentos, metadatos, ids = _crear_chunks(
            pdf_path.name,
            paginas,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        todos_los_documentos.extend(documentos)
        todos_los_metadatos.extend(metadatos)
        todos_los_ids.extend(ids)

    if not todos_los_documentos:
        raise ValueError("No se pudo extraer texto util de los PDFs del corpus.")

    # Creamos los embeddings una sola vez antes de enviar a Chroma.
    embeddings = _crear_embeddings(todos_los_documentos, cliente_openai)

    # PersistentClient guarda la base vectorial en disco para reutilizarla.
    chroma_path = _resolver_ruta(chroma_dir)
    chroma_client = chromadb.PersistentClient(path=str(chroma_path))
    collection = chroma_client.get_or_create_collection(name=collection_name)

    # upsert actualiza o inserta segun el id, evitando duplicaciones al re-ejecutar.
    collection.upsert(
        ids=todos_los_ids,
        documents=todos_los_documentos,
        embeddings=embeddings,
        metadatas=todos_los_metadatos,
    )

    return {
        "total_pdfs": len(pdfs),
        "total_paginas": len(todos_los_metadatos),
        "total_chunks": len(todos_los_documentos),
    }


if __name__ == "__main__":
    # Este bloque permite ejecutar el modulo directamente para testeo.
    # Ejemplo: python -m src.ingestion
    try:
        stats = ingestar_corpus()
        print("✅ Ingestión completada con éxito.")
        print(f"   - PDFs procesados: {stats['total_pdfs']}")
        print(f"   - Chunks creados: {stats['total_chunks']}")
    except (ValueError, FileNotFoundError) as e:
        print(f"❌ Error durante la ingestión: {e}")
