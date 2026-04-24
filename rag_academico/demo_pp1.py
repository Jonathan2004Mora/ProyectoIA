"""Demo automatica para PP1.

Este script ejecuta consultas de prueba basadas en el corpus en modo comparacion:
- Respuesta SIN RAG
- Respuesta CON RAG

Los resultados se guardan en logs/consultas.json como evidencia academica.
"""

from __future__ import annotations

from src.generation import responder_con_rag, responder_sin_rag
from src.ingestion import ingestar_corpus
from src.logger import guardar_consulta
from src.retrieval import recuperar_chunks


CONSULTAS_DEMO = [
    "Que es el perceptron y cual fue su principal limitacion historica?",
    "Como se relacionan los sesgos de los datos de entrenamiento con las alucinaciones de IA?",
    "Que papel cumple la autoatencion en los modelos transformadores?",
    "Por que en educacion no se recomienda prohibir ChatGPT, sino capacitar su uso etico?",
    "Cual es la diferencia entre alucinaciones humanas y alucinaciones de inteligencia artificial?",
]


def ejecutar_demo() -> None:
    """Ejecuta demo completa y registra resultados de forma automatica."""
    print("Iniciando demo PP1...")

    # Primero intentamos asegurar que el corpus este indexado.
    # Si ya estaba indexado, upsert simplemente actualiza o reutiliza ids.
    try:
        resultado_ingestion = ingestar_corpus()
        print("Ingestion previa completada:", resultado_ingestion)
    except Exception as exc:
        print(f"Aviso: no se pudo ejecutar ingestion automatica: {exc}")
        print("Se intentara continuar usando una base ya existente.")

    for idx, query in enumerate(CONSULTAS_DEMO, start=1):
        print(f"\n--- Consulta demo {idx} ---")
        print("Pregunta:", query)

        chunks = recuperar_chunks(query=query, k=3)

        respuesta_sin_rag = responder_sin_rag(query)
        guardar_consulta(
            query=query,
            modo="sin_rag",
            chunks_recuperados=[],
            respuesta=respuesta_sin_rag,
        )

        respuesta_con_rag = responder_con_rag(query, chunks)
        guardar_consulta(
            query=query,
            modo="con_rag",
            chunks_recuperados=chunks,
            respuesta=respuesta_con_rag,
        )

        print("Respuesta SIN RAG registrada.")
        print("Respuesta CON RAG registrada.")

    print("\nDemo completada. Revisa logs/consultas.json para evidencia.")


if __name__ == "__main__":
    ejecutar_demo()
