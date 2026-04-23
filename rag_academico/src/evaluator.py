"""Modulo de evaluacion automatica para respuestas RAG.

Este evaluador usa exclusivamente OpenAI y Structured Outputs para obtener
una evaluacion consistente de faithfulness, relevancia y alucinaciones.
"""

from __future__ import annotations

import os
from typing import Any, Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

# Cargamos variables de entorno para obtener OPENAI_API_KEY y modelo opcional.
load_dotenv()


class EvaluacionRAG(BaseModel):
    """Schema estructurado para evaluar calidad de respuestas RAG."""

    score_faithfulness: int = Field(..., ge=0, le=10)
    score_relevancia: int = Field(..., ge=0, le=10)
    tiene_alucinacion: bool
    citas_validas: bool
    problemas_detectados: list[str]
    veredicto: Literal["CONFIABLE", "DUDOSO", "ALUCINACION"]


class EvaluadorRAG:
    """Evaluador critico que califica una respuesta frente a su evidencia."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("OPENAI_EVAL_MODEL", "gpt-4o-mini")
        self.client = self._crear_cliente()

    @staticmethod
    def _crear_cliente() -> OpenAI:
        """Inicializa cliente OpenAI validando API key."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("No se encontro OPENAI_API_KEY. Configura un archivo .env.")
        return OpenAI(api_key=api_key)

    @staticmethod
    def _fallback_evaluacion() -> dict[str, Any]:
        """Resultado por defecto cuando falla parseo o invocacion del evaluador."""
        return {
            "score_faithfulness": 0,
            "score_relevancia": 0,
            "tiene_alucinacion": True,
            "citas_validas": False,
            "problemas_detectados": ["Error al parsear la evaluacion del LLM"],
            "veredicto": "ALUCINACION",
        }

    @staticmethod
    def _formatear_chunks(chunks: list[dict[str, Any]]) -> str:
        """Construye bloque de evidencia con metadata para el prompt."""
        if not chunks:
            return "No se recuperaron chunks para esta respuesta."

        bloques: list[str] = []
        for idx, chunk in enumerate(chunks, start=1):
            source = chunk.get("source", "desconocido")
            page = chunk.get("page", "?")
            score = chunk.get("score", "?")
            text = chunk.get("text", "")
            bloques.append(
                f"[Chunk {idx}] archivo={source} | pagina={page} | score={score}\n{text}"
            )

        return "\n\n".join(bloques)

    def evaluar(self, query: str, respuesta: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        """Evalua la respuesta con base en evidencia recuperada.

        Usa Structured Outputs mediante parse() para mapear directamente al
        modelo Pydantic EvaluacionRAG.
        """
        system_prompt = (
            "Eres un evaluador critico y estricto de sistemas RAG academicos. \n"
            "Analiza si la respuesta esta bien soportada por los fragmentos de evidencia.\n\n"
            "Evalua:\n"
            "- Faithfulness: ¿La respuesta solo usa informacion presente en los chunks o inventa contenido?\n"
            "- Relevancia: ¿La respuesta responde directamente y de forma util a la pregunta?\n"
            "- Alucinaciones: ¿Existe informacion no respaldada por los chunks?\n"
            "- Citas: ¿Las referencias a fuentes son precisas y validas?\n\n"
            "Responde UNICAMENTE con el objeto segun el schema proporcionado. Se objetivo y riguroso."
        )

        evidencia = self._formatear_chunks(chunks)
        prompt_usuario = (
            f"Pregunta:\n{query}\n\n"
            f"Respuesta generada:\n{respuesta}\n\n"
            f"Fragmentos de evidencia:\n{evidencia}"
        )

        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                temperature=0,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt_usuario},
                ],
                response_format=EvaluacionRAG,
            )

            parsed = completion.choices[0].message.parsed
            if parsed is None:
                return self._fallback_evaluacion()

            return parsed.model_dump()
        except Exception:
            # Se retorna fallback para que la app y los experimentos nunca fallen.
            return self._fallback_evaluacion()
