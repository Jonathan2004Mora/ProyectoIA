"""Modulo de experimentacion para comparar configuraciones RAG.

Este script ejecuta consultas de prueba sobre 4 configuraciones de chunk_size
y top_k, evalua cada salida con EvaluadorRAG y guarda resultados agregados.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, TypedDict, cast

import chromadb

from src.evaluator import EvaluadorRAG
from src.generation import responder_con_rag
from src.ingestion import ingestar_corpus
from src.retrieval import recuperar_chunks

EXPERIMENTOS_LOG_PATH = Path("logs/experimentos.json")


class ConfiguracionExperimento(TypedDict):
    """Define una configuracion valida de chunking + retrieval."""

    nombre: str
    chunk_size: int
    top_k: int


class ResultadoConsulta(TypedDict):
    """Resultado individual por pregunta dentro de una configuracion."""

    query: str
    respuesta: str
    chunks: list[dict[str, Any]]
    evaluacion: dict[str, Any]


class ResultadoPorConfig(TypedDict):
    """Agrupa resultados por configuracion."""

    config: str
    chunk_size: int
    top_k: int
    resultados: list[ResultadoConsulta]


class CorridaExperimentos(TypedDict):
    """Estructura principal persistida en logs/experimentos.json."""

    timestamp: str
    queries: list[str]
    resultados_por_config: list[ResultadoPorConfig]
    resumen_por_config: list[dict[str, Any]]

# Se incluyen al menos 5 preguntas para cumplir el requerimiento del PP2.
QUERIES_PRUEBA = [
    "Que es Retrieval-Augmented Generation y cual es su objetivo principal?",
    "Como ayuda RAG a reducir alucinaciones en modelos de lenguaje?",
    "Cual es la diferencia entre usar evidencia recuperada y responder solo con memoria parametric?",
    "Que elementos deberia incluir una cita valida en una respuesta academica asistida por IA?",
    "Que limitaciones se mencionan sobre la calidad de recuperacion en sistemas RAG?",
]

CONFIGURACIONES: list[ConfiguracionExperimento] = [
    {"nombre": "Config A", "chunk_size": 300, "top_k": 2},
    {"nombre": "Config B", "chunk_size": 300, "top_k": 5},
    {"nombre": "Config C", "chunk_size": 700, "top_k": 2},
    {"nombre": "Config D", "chunk_size": 700, "top_k": 5},
]


def _coleccion_tiene_datos(chroma_dir: str, collection_name: str) -> bool:
    """Verifica si una coleccion ya esta indexada para evitar reingestar siempre.

    Este chequeo reduce drasticamente tiempo/costo en corridas repetidas de
    experimentos, porque la ingestión (embeddings + upsert) suele ser lo mas caro.
    """
    try:
        chroma_client = chromadb.PersistentClient(path=chroma_dir)
        collection = chroma_client.get_collection(name=collection_name)
        return collection.count() > 0
    except Exception:
        return False


def _guardar_resultado_experimento(
    entrada: dict[str, Any], log_path: Path = EXPERIMENTOS_LOG_PATH
) -> None:
    """Persistencia acumulada de ejecuciones de experimentos en JSON."""
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if log_path.exists():
        try:
            data = json.loads(log_path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                data = []
        except json.JSONDecodeError:
            data = []
    else:
        data = []

    data_list: list[dict[str, Any]] = cast(list[dict[str, Any]], data)
    data_list.append(entrada)
    log_path.write_text(json.dumps(data_list, ensure_ascii=False, indent=2), encoding="utf-8")


def _resumen_configuracion(
    nombre: str,
    chunk_size: int,
    top_k: int,
    resultados: list[ResultadoConsulta],
) -> dict[str, Any]:
    """Calcula metricas agregadas por configuracion para analisis comparativo."""
    scores_faith = [r["evaluacion"]["score_faithfulness"] for r in resultados]
    scores_relev = [r["evaluacion"]["score_relevancia"] for r in resultados]
    alucinaciones = [r["evaluacion"]["tiene_alucinacion"] for r in resultados]
    veredictos = [r["evaluacion"]["veredicto"] for r in resultados]

    veredicto_mas_frecuente = Counter(veredictos).most_common(1)[0][0] if veredictos else "ALUCINACION"

    return {
        "config": nombre,
        "chunk_size": chunk_size,
        "top_k": top_k,
        "promedio_faithfulness": round(mean(scores_faith), 2) if scores_faith else 0.0,
        "promedio_relevancia": round(mean(scores_relev), 2) if scores_relev else 0.0,
        "porcentaje_alucinaciones": round((sum(alucinaciones) / len(alucinaciones)) * 100, 2)
        if alucinaciones
        else 100.0,
        "veredicto_mas_frecuente": veredicto_mas_frecuente,
    }


def ejecutar_experimentos(
    queries: list[str] | None = None,
    chroma_dir: str = "chroma_db",
    corpus_dir: str = "corpus",
    overlap: int = 50,
    force_reindex: bool = False,
    generation_model: str = "gpt-4o-mini",
) -> dict[str, Any]:
    """Ejecuta el benchmark de configuraciones y retorna resultados completos."""
    evaluador = EvaluadorRAG()
    queries_ejecucion = queries or QUERIES_PRUEBA

    corrida: CorridaExperimentos = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "queries": queries_ejecucion,
        "resultados_por_config": [],
        "resumen_por_config": [],
    }

    for config in CONFIGURACIONES:
        nombre = config["nombre"]
        chunk_size = config["chunk_size"]
        top_k = config["top_k"]

        # Usamos colecciones separadas por configuracion para no mezclar embeddings.
        collection_name = f"eif420_{nombre.lower().replace(' ', '_')}_cs{chunk_size}_k{top_k}"

        # Solo reindexamos si no existe la coleccion o si se fuerza manualmente.
        if force_reindex or not _coleccion_tiene_datos(chroma_dir, collection_name):
            ingestar_corpus(
                corpus_dir=corpus_dir,
                chroma_dir=chroma_dir,
                collection_name=collection_name,
                chunk_size=chunk_size,
                chunk_overlap=overlap,
            )

        resultados_config: list[ResultadoConsulta] = []
        for query in queries_ejecucion:
            chunks = recuperar_chunks(
                query=query,
                k=top_k,
                chroma_dir=chroma_dir,
                collection_name=collection_name,
            )
            respuesta = responder_con_rag(query=query, chunks=chunks, model=generation_model)
            evaluacion = evaluador.evaluar(query=query, respuesta=respuesta, chunks=chunks)

            resultados_config.append(
                {
                    "query": query,
                    "respuesta": respuesta,
                    "chunks": chunks,
                    "evaluacion": evaluacion,
                }
            )

        corrida["resultados_por_config"].append(
            {
                "config": nombre,
                "chunk_size": chunk_size,
                "top_k": top_k,
                "resultados": resultados_config,
            }
        )

        corrida["resumen_por_config"].append(
            _resumen_configuracion(nombre, chunk_size, top_k, resultados_config)
        )

    _guardar_resultado_experimento(cast(dict[str, Any], corrida))
    return cast(dict[str, Any], corrida)


if __name__ == "__main__":
    resultado = ejecutar_experimentos()
    print("Experimentos completados. Resumen:")
    for fila in resultado["resumen_por_config"]:
        print(fila)
