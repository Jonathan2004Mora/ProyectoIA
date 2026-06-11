"""Utilidades para traducir evidencia recuperada antes de mostrarla en la UI."""

from __future__ import annotations

import os
import re
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

ENGLISH_MARKERS = {
    "the",
    "and",
    "of",
    "to",
    "in",
    "for",
    "with",
    "that",
    "this",
    "is",
    "are",
    "from",
    "by",
    "on",
    "as",
    "an",
    "be",
    "their",
    "language",
    "model",
    "models",
    "retrieval",
    "generation",
    "hallucination",
    "hallucinations",
}

SPANISH_MARKERS = {
    "el",
    "la",
    "los",
    "las",
    "de",
    "del",
    "que",
    "en",
    "para",
    "con",
    "por",
    "una",
    "un",
    "es",
    "son",
    "como",
    "modelo",
    "modelos",
    "lenguaje",
    "alucinacion",
    "alucinaciones",
}


def _crear_cliente() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("No se encontro OPENAI_API_KEY. Configura un archivo .env.")
    return OpenAI(api_key=api_key)


def _parece_ingles(texto: str) -> bool:
    """Heuristica ligera para no traducir chunks que ya estan en espanol."""
    palabras = re.findall(r"[A-Za-zÀ-ÿ]+", texto.lower())
    if len(palabras) < 8:
        return False

    english_score = sum(1 for palabra in palabras if palabra in ENGLISH_MARKERS)
    spanish_score = sum(1 for palabra in palabras if palabra in SPANISH_MARKERS)

    return english_score >= 3 and english_score > spanish_score


def _traducir_a_espanol(texto: str, client: OpenAI, model: str = DEFAULT_MODEL) -> str:
    completion = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "Traduce al espanol el texto academico del usuario. "
                    "No resumas, no agregues explicaciones y conserva terminos tecnicos."
                ),
            },
            {"role": "user", "content": texto},
        ],
    )
    return completion.choices[0].message.content or texto


def preparar_chunks_para_mostrar(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Devuelve una copia de los chunks, traduciendo text si parece estar en ingles."""
    if not chunks:
        return []

    client: OpenAI | None = None
    chunks_preparados: list[dict[str, Any]] = []

    for chunk in chunks:
        texto = str(chunk.get("text", ""))
        chunk_preparado = dict(chunk)
        chunk_preparado["original_text"] = texto
        chunk_preparado["was_translated"] = False

        if _parece_ingles(texto):
            if client is None:
                client = _crear_cliente()
            chunk_preparado["text"] = _traducir_a_espanol(texto, client)
            chunk_preparado["was_translated"] = True
            chunk_preparado["translated_from"] = "en"

        chunks_preparados.append(chunk_preparado)

    return chunks_preparados
