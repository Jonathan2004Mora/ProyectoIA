"""Modulo de generacion de respuestas con y sin RAG.

Incluye dos funciones requeridas por PP1:
- responder_sin_rag(query)
- responder_con_rag(query, chunks)
"""

from __future__ import annotations

import os
from typing import Any, List

from dotenv import load_dotenv
from openai import OpenAI

# Carga de variables de entorno para leer OPENAI_API_KEY y OPENAI_MODEL.
load_dotenv()

# Modelo por defecto. Se puede sobrescribir en .env con OPENAI_MODEL.
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# Prompt del sistema exigido por el enunciado para el modo RAG.
SYSTEM_PROMPT_RAG = (
    "Eres un asistente academico. Responde UNICAMENTE basandote en los fragmentos "
    "de documentos proporcionados. Al final de tu respuesta, incluye una seccion "
    "'📚 Fuentes:' listando cada documento y pagina usada. Si la informacion no "
    "esta en los fragmentos, di explicitamente que no tienes evidencia suficiente."
)

# Prompt para baseline sin RAG, util para comparar alucinaciones.
SYSTEM_PROMPT_SIN_RAG = (
    "Eres un asistente academico para estudiantes universitarios. "
    "Responde de forma clara y estructurada."
)


def _crear_cliente() -> OpenAI:
    """Crea cliente OpenAI validando que exista API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("No se encontro OPENAI_API_KEY. Configura un archivo .env.")
    return OpenAI(api_key=api_key)


def responder_sin_rag(query: str, model: str = DEFAULT_MODEL) -> str:
    """Genera respuesta sin contexto externo (baseline)."""
    if not query.strip():
        raise ValueError("La consulta no puede estar vacia.")

    client = _crear_cliente()
    completion = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_SIN_RAG},
            {"role": "user", "content": query},
        ],
    )

    return completion.choices[0].message.content or "No se obtuvo respuesta del modelo."


def responder_con_rag(query: str, chunks: List[dict[str, Any]], model: str = DEFAULT_MODEL) -> str:
    """Genera respuesta inyectando chunks recuperados como evidencia.

    Si no hay chunks, se devuelve un mensaje explicito de evidencia insuficiente,
    alineado con la filosofia de reducir alucinaciones.
    """
    if not query.strip():
        raise ValueError("La consulta no puede estar vacia.")

    if not chunks:
        return (
            "No tengo evidencia suficiente en los fragmentos recuperados para responder "
            "la consulta con confianza.\n\n📚 Fuentes:\n- No se recuperaron fuentes relevantes."
        )

    # Construimos un bloque de contexto con trazabilidad por fuente y pagina.
    contexto_formateado: List[str] = []
    for idx, chunk in enumerate(chunks, start=1):
        fuente = chunk.get("source", "desconocido")
        pagina = chunk.get("page", "?")
        texto = chunk.get("text", "")
        contexto_formateado.append(
            f"[Fragmento {idx}] Fuente: {fuente} | Pagina: {pagina}\n{texto}"
        )

    contexto = "\n\n".join(contexto_formateado)

    prompt_usuario = (
        "Usa exclusivamente la siguiente evidencia para responder la consulta. "
        "No inventes informacion fuera de los fragmentos.\n\n"
        f"EVIDENCIA:\n{contexto}\n\n"
        f"CONSULTA:\n{query}\n\n"
        "Recuerda incluir al final la seccion '📚 Fuentes:' con documento y pagina."
    )

    client = _crear_cliente()
    completion = client.chat.completions.create(
        model=model,
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_RAG},
            {"role": "user", "content": prompt_usuario},
        ],
    )

    return completion.choices[0].message.content or "No se obtuvo respuesta del modelo."
