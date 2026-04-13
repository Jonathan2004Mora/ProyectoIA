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
from typing import Dict, List

from src.evaluator import EvaluadorRAG
from src.generation import responder_con_rag
from src.ingestion import ingestar_corpus
from src.retrieval import recuperar_chunks

EXPERIMENTOS_LOG_PATH = Path("logs/experimentos.json")

# Se incluyen al menos 5 preguntas para cumplir el requerimiento del PP2.
QUERIES_PRUEBA = [
    "Que es Retrieval-Augmented Generation y cual es su objetivo principal?",
    "Como ayuda RAG a reducir alucinaciones en modelos de lenguaje?",
    "Cual es la diferencia entre usar evidencia recuperada y responder solo con memoria parametric?",
    "Que elementos deberia incluir una cita valida en una respuesta academica asistida por IA?",
    "Que limitaciones se mencionan sobre la calidad de recuperacion en sistemas RAG?",
]

CONFIGURACIONES = [
    {"nombre": "Config A", "chunk_size": 300, "top_k": 2},
    {"nombre": "Config B", "chunk_size": 300, "top_k": 5},
    {"nombre": "Config C", "chunk_size": 700, "top_k": 2},
    {"nombre": "Config D", "chunk_size": 700, "top_k": 5},
]


def _guardar_resultado_experimento(entrada: Dict, log_path: Path = EXPERIMENTOS_LOG_PATH) -> None:
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

    data.append(entrada)
    log_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _resumen_configuracion(nombre: str, chunk_size: int, top_k: int, resultados: List[Dict]) -> Dict:
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
    queries: List[str] | None = None,
    chroma_dir: str = "chroma_db",
    corpus_dir: str = "corpus",
    overlap: int = 50,
) -> Dict:
    """Ejecuta el benchmark de configuraciones y retorna resultados completos."""
    evaluador = EvaluadorRAG()
    queries_ejecucion = queries or QUERIES_PRUEBA

    corrida = {
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

        ingestar_corpus(
            corpus_dir=corpus_dir,
            chroma_dir=chroma_dir,
            collection_name=collection_name,
            chunk_size=chunk_size,
            chunk_overlap=overlap,
        )

        resultados_config: List[Dict] = []
        for query in queries_ejecucion:
            chunks = recuperar_chunks(
                query=query,
                k=top_k,
                chroma_dir=chroma_dir,
                collection_name=collection_name,
            )
            respuesta = responder_con_rag(query=query, chunks=chunks)
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

    _guardar_resultado_experimento(corrida)
    return corrida


if __name__ == "__main__":
    resultado = ejecutar_experimentos()
    print("Experimentos completados. Resumen:")
    for fila in resultado["resumen_por_config"]:
        print(fila)
