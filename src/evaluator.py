"""Evaluacion automatica de respuestas RAG contra evidencia recuperada."""

from __future__ import annotations

import os
from typing import Any, Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

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

    SYSTEM_PROMPT = """
Eres un evaluador critico y estricto de sistemas RAG academicos.
Compara cada afirmacion de la respuesta contra los fragmentos de evidencia.
No uses conocimiento externo para completar vacios ni para validar afirmaciones.

RUBRICA DE FAITHFULNESS (0-10):
- 10: Todas las afirmaciones verificables estan respaldadas directamente por la evidencia.
- 8-9: Casi todo esta respaldado; solo hay una imprecision menor.
- 6-7: La idea principal esta respaldada, pero hay detalles sin soporte claro.
- 4-5: Solo una parte importante esta respaldada o se mezcla evidencia con suposiciones.
- 1-3: La mayor parte no esta respaldada o contradice la evidencia.
- 0: No existe evidencia para validar la respuesta o esta completamente inventada.

RUBRICA DE RELEVANCIA (0-10):
- 10: Responde completa, directa y precisamente la pregunta.
- 8-9: Responde bien, con omisiones o contenido extra menor.
- 6-7: Responde parcialmente o incluye bastante informacion innecesaria.
- 4-5: Apenas aborda la pregunta o deja fuera elementos centrales.
- 1-3: Es mayormente irrelevante.
- 0: No responde la pregunta.

REGLAS OBLIGATORIAS:
- No uses 5 como valor por defecto. Selecciona el valor que mejor corresponda a la rubrica.
- Admitir correctamente falta de evidencia puede ser fiel, pero no necesariamente relevante.
- Si hay afirmaciones factuales no respaldadas, tiene_alucinacion debe ser true.
- Si tiene_alucinacion es true, faithfulness no puede superar 4 y el veredicto es ALUCINACION.
- CONFIABLE requiere: sin alucinacion, citas validas, faithfulness >= 8 y relevancia >= 7.
- DUDOSO corresponde a respuestas parcialmente respaldadas, incompletas o con citas debiles.
- Las citas son validas solo si documento y pagina coinciden con la evidencia suministrada.
- problemas_detectados debe mencionar problemas concretos; usa una lista vacia si no hay problemas.

Responde UNICAMENTE con el objeto segun el schema proporcionado.
""".strip()

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
        """Construye un bloque de evidencia con metadata para el prompt."""
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

    @staticmethod
    def _normalizar_evaluacion(
        evaluacion: EvaluacionRAG, chunks: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Aplica reglas deterministas para evitar resultados contradictorios."""
        resultado = evaluacion.model_dump()
        problemas = [p.strip() for p in resultado["problemas_detectados"] if p.strip()]

        if not chunks:
            resultado["citas_validas"] = False
            mensaje = "No se proporciono evidencia para verificar la respuesta."
            if mensaje not in problemas:
                problemas.append(mensaje)

        if resultado["tiene_alucinacion"]:
            resultado["score_faithfulness"] = min(resultado["score_faithfulness"], 4)
            resultado["veredicto"] = "ALUCINACION"
        elif (
            resultado["score_faithfulness"] >= 8
            and resultado["score_relevancia"] >= 7
            and resultado["citas_validas"]
        ):
            resultado["veredicto"] = "CONFIABLE"
        else:
            resultado["veredicto"] = "DUDOSO"

        resultado["problemas_detectados"] = problemas
        return resultado

    def evaluar(self, query: str, respuesta: str, chunks: list[dict[str, Any]]) -> dict[str, Any]:
        """Evalua la respuesta con base en la evidencia recuperada."""
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
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_usuario},
                ],
                response_format=EvaluacionRAG,
            )

            parsed = completion.choices[0].message.parsed
            if parsed is None:
                return self._fallback_evaluacion()

            return self._normalizar_evaluacion(parsed, chunks)
        except Exception:
            return self._fallback_evaluacion()
