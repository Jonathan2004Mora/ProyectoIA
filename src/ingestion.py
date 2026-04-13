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
) -> Tuple[List[str], List[Dict], List[str]]:
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
    metadatos: List[Dict] = []
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


def _crear_embeddings(textos: List[str], cliente_openai: OpenAI) -> List[List[float]]:
    """Crea embeddings en lotes para mejorar rendimiento y estabilidad.

    Chroma permite almacenar embeddings precalculados, lo cual nos da control
    sobre el modelo de embeddings y consistencia con retrieval.
    """
    if not textos:
        return []

    embeddings: List[List[float]] = []
    batch_size = 64

    for i in range(0, len(textos), batch_size):
        batch = textos[i : i + batch_size]
        respuesta = cliente_openai.embeddings.create(model=EMBEDDING_MODEL, input=batch)
        embeddings.extend([item.embedding for item in respuesta.data])

    return embeddings


def ingestar_corpus(
    corpus_dir: str = "corpus",
    chroma_dir: str = "chroma_db",
    collection_name: str = COLLECTION_NAME,
) -> Dict[str, int]:
    """Ingresa todos los PDFs en ChromaDB y retorna estadisticas del proceso."""
    api_key = _validar_api_key(os.getenv("OPENAI_API_KEY"))

    cliente_openai = OpenAI(api_key=api_key)

    carpeta_corpus = Path(corpus_dir)
    if not carpeta_corpus.exists():
        raise FileNotFoundError(f"No existe la carpeta de corpus: {corpus_dir}")

    pdfs = sorted(carpeta_corpus.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError("No se encontraron PDFs en la carpeta corpus/.")

    todos_los_documentos: List[str] = []
    todos_los_metadatos: List[Dict] = []
    todos_los_ids: List[str] = []

    for pdf_path in pdfs:
        paginas = _extraer_paginas_pdf(pdf_path)
        documentos, metadatos, ids = _crear_chunks(pdf_path.name, paginas)

        todos_los_documentos.extend(documentos)
        todos_los_metadatos.extend(metadatos)
        todos_los_ids.extend(ids)

    if not todos_los_documentos:
        raise ValueError("No se pudo extraer texto util de los PDFs del corpus.")

    # Creamos los embeddings una sola vez antes de enviar a Chroma.
    embeddings = _crear_embeddings(todos_los_documentos, cliente_openai)

    # PersistentClient guarda la base vectorial en disco para reutilizarla.
    chroma_client = chromadb.PersistentClient(path=chroma_dir)
    collection = chroma_client.get_or_create_collection(name=collection_name)

    # upsert actualiza o inserta segun el id, evitando duplicaciones al re-ejecutar.
    collection.upsert(
        ids=todos_los_ids,
        documents=todos_los_documentos,
        metadatas=todos_los_metadatos,
        embeddings=embeddings,
    )

    return {
        "archivos_procesados": len(pdfs),
        "chunks_indexados": len(todos_los_documentos),
    }


if __name__ == "__main__":
    # Punto de entrada rapido para pruebas de ingestión desde terminal.
    resultado = ingestar_corpus()
    print("Ingestion completada:")
    print(resultado)
