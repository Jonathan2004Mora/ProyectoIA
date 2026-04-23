"""Modulo de logging en JSON para trazabilidad de consultas.

Cada consulta se guarda en logs/consultas.json con:
- timestamp
- query
- modo (sin_rag o con_rag)
- chunks_recuperados
- respuesta
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, cast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH_DEFAULT = PROJECT_ROOT / "logs" / "consultas.json"


def _asegurar_archivo_log(log_path: Path) -> None:
    """Crea carpeta y archivo de logs si no existen."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if not log_path.exists():
        log_path.write_text("[]", encoding="utf-8")


def _leer_logs(log_path: Path) -> List[Dict[str, Any]]:
    """Lee el archivo JSON de logs con manejo defensivo de errores."""
    _asegurar_archivo_log(log_path)

    try:
        contenido = log_path.read_text(encoding="utf-8").strip()
        if not contenido:
            return []
        data: object = json.loads(contenido)
        if not isinstance(data, list):
            return []

        data_items = cast(List[object], data)
        logs: List[Dict[str, Any]] = []
        for item in data_items:
            if isinstance(item, dict):
                item_dict = cast(Dict[object, object], item)
                normalizado: Dict[str, Any] = {}
                for key, value in item_dict.items():
                    if isinstance(key, str):
                        normalizado[key] = value
                logs.append(normalizado)
        return logs
    except json.JSONDecodeError:
        # Si el archivo se corrompe, evitamos romper el flujo principal.
        return []


def guardar_consulta(
    query: str,
    modo: str,
    chunks_recuperados: List[Dict[str, Any]],
    respuesta: str,
    evaluacion: Dict[str, Any] | None = None,
    log_path: Path = LOG_PATH_DEFAULT,
) -> Dict[str, Any]:
    """Guarda una entrada de consulta y retorna la entrada creada."""
    logs_actuales = _leer_logs(log_path)

    entrada: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "modo": modo,
        "chunks_recuperados": chunks_recuperados,
        "respuesta": respuesta,
        "evaluacion": evaluacion,
    }

    if evaluacion:
        entrada["veredicto"] = evaluacion.get("veredicto")
        entrada["score_faithfulness"] = evaluacion.get("score_faithfulness")
        entrada["score_relevancia"] = evaluacion.get("score_relevancia")

    logs_actuales.append(entrada)
    log_path.write_text(json.dumps(logs_actuales, ensure_ascii=False, indent=2), encoding="utf-8")

    return entrada


def cargar_consultas(log_path: Path = LOG_PATH_DEFAULT) -> List[Dict[str, Any]]:
    """Retorna el historial completo de consultas del archivo de logs."""
    return _leer_logs(log_path)
