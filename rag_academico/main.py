"""CLI principal para el proyecto RAG Academico.

Flujo general:
1) Permite ejecutar ingestión de PDFs.
2) Permite elegir modo de ejecucion:
   - Solo RAG
   - Comparacion RAG vs Sin-RAG
3) Muestra chunks recuperados antes de responder.
4) Guarda logs automaticamente en logs/consultas.json.
"""

from __future__ import annotations

<<<<<<< HEAD
from typing import Any
=======
from typing import List
>>>>>>> aef98f5 (PP1: RAG academico base con ingestion, retrieval, generation y demo)

from src.generation import responder_con_rag, responder_sin_rag
from src.ingestion import ingestar_corpus
from src.logger import guardar_consulta
from src.retrieval import recuperar_chunks


<<<<<<< HEAD
Chunk = dict[str, Any]


def mostrar_chunks(chunks: list[Chunk]) -> None:
=======
def mostrar_chunks(chunks: List[dict]) -> None:
>>>>>>> aef98f5 (PP1: RAG academico base con ingestion, retrieval, generation y demo)
    """Imprime chunks recuperados para transparencia del proceso RAG."""
    print("\n=== Chunks recuperados ===")

    if not chunks:
        print("No se recuperaron chunks relevantes.")
        return

    for idx, chunk in enumerate(chunks, start=1):
        print(f"\n[{idx}] Fuente: {chunk['source']} | Pagina: {chunk['page']} | Score: {chunk['score']}")
        print("Texto:")
        print(chunk["text"])


def ejecutar_modo_solo_rag(query: str, k: int) -> None:
    """Ejecuta pipeline RAG completo y registra resultado."""
    chunks = recuperar_chunks(query=query, k=k)
    mostrar_chunks(chunks)

    respuesta = responder_con_rag(query=query, chunks=chunks)
    print("\n=== Respuesta final (RAG) ===")
    print(respuesta)

    guardar_consulta(
        query=query,
        modo="con_rag",
        chunks_recuperados=chunks,
        respuesta=respuesta,
    )


def ejecutar_modo_comparacion(query: str, k: int) -> None:
    """Ejecuta baseline sin RAG y luego respuesta con RAG para comparar."""
    chunks = recuperar_chunks(query=query, k=k)
    mostrar_chunks(chunks)

    respuesta_sin_rag = responder_sin_rag(query=query)
    print("\n=== Respuesta SIN RAG ===")
    print(respuesta_sin_rag)

    guardar_consulta(
        query=query,
        modo="sin_rag",
        chunks_recuperados=[],
        respuesta=respuesta_sin_rag,
    )

    respuesta_con_rag = responder_con_rag(query=query, chunks=chunks)
    print("\n=== Respuesta CON RAG ===")
    print(respuesta_con_rag)

    guardar_consulta(
        query=query,
        modo="con_rag",
        chunks_recuperados=chunks,
        respuesta=respuesta_con_rag,
    )


<<<<<<< HEAD
def ejecutar_consulta_con_reintento(modo: str, query: str, k: int) -> None:
    """Ejecuta una consulta y, si falta la coleccion, intenta auto-ingestion.

    Esto evita que la CLI falle cuando el usuario omite la ingestion inicial.
    """
    try:
        if modo == "1":
            ejecutar_modo_solo_rag(query=query, k=k)
        else:
            ejecutar_modo_comparacion(query=query, k=k)
        return
    except Exception as exc:
        error_texto = str(exc).lower()
        if "does not exist" not in error_texto and "collection" not in error_texto:
            raise

        print("\nNo se encontro la coleccion vectorial. Ejecutando ingestion automatica...")
        resultado = ingestar_corpus()
        print("Ingestion completada:")
        print(resultado)

    if modo == "1":
        ejecutar_modo_solo_rag(query=query, k=k)
    else:
        ejecutar_modo_comparacion(query=query, k=k)


=======
>>>>>>> aef98f5 (PP1: RAG academico base con ingestion, retrieval, generation y demo)
def main() -> None:
    """Punto de entrada de la CLI interactiva."""
    print("RAG Academico - Reducir Alucinaciones con Evidencia y Citas")

    print("\nPaso opcional: ingestion del corpus")
    opcion_ingestion = input("Deseas ejecutar ingestion ahora? (s/n): ").strip().lower()

    if opcion_ingestion == "s":
        try:
            resultado = ingestar_corpus()
            print("Ingestion completada:")
            print(resultado)
        except Exception as exc:
            print(f"Error durante ingestion: {exc}")

    print("\nSelecciona modo de ejecucion:")
    print("1) Solo RAG")
    print("2) Comparacion RAG vs Sin-RAG")

    modo = input("Ingresa 1 o 2: ").strip()
    if modo not in {"1", "2"}:
        print("Modo invalido. Cerrando programa.")
        return

    k_input = input("Top-k de recuperacion (default 3): ").strip()
    k = int(k_input) if k_input.isdigit() and int(k_input) > 0 else 3

    print("\nEscribe tu consulta. Usa 'salir' para terminar.")
    while True:
        query = input("\nConsulta: ").strip()
        if query.lower() in {"salir", "exit", "quit"}:
            print("Sesion finalizada.")
            break

        if not query:
            print("La consulta esta vacia. Intenta de nuevo.")
            continue

        try:
<<<<<<< HEAD
            ejecutar_consulta_con_reintento(modo=modo, query=query, k=k)
=======
            if modo == "1":
                ejecutar_modo_solo_rag(query=query, k=k)
            else:
                ejecutar_modo_comparacion(query=query, k=k)
>>>>>>> aef98f5 (PP1: RAG academico base con ingestion, retrieval, generation y demo)

            print("\nConsulta registrada en logs/consultas.json")
        except Exception as exc:
            print(f"Ocurrio un error durante la consulta: {exc}")


if __name__ == "__main__":
    main()
