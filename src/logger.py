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
from typing import Any, Dict, List

LOG_PATH_DEFAULT = Path("logs/consultas.json")


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
        data = json.loads(contenido)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        # Si el archivo se corrompe, evitamos romper el flujo principal.
        return []


def guardar_consulta(
    query: str,
    modo: str,
    chunks_recuperados: List[Dict[str, Any]],
    respuesta: str,
    log_path: Path = LOG_PATH_DEFAULT,
) -> Dict[str, Any]:
    """Guarda una entrada de consulta y retorna la entrada creada."""
    logs_actuales = _leer_logs(log_path)

    entrada = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "modo": modo,
        "chunks_recuperados": chunks_recuperados,
        "respuesta": respuesta,
    }

    logs_actuales.append(entrada)
    log_path.write_text(json.dumps(logs_actuales, ensure_ascii=False, indent=2), encoding="utf-8")

    return entrada
