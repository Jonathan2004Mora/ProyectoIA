"""API HTTP para la interfaz React del RAG academico."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.evaluator import EvaluadorRAG
from src.experimenter import ejecutar_experimentos
from src.generation import responder_con_rag, responder_sin_rag
from src.ingestion import ingestar_corpus
from src.logger import cargar_consultas, guardar_consulta
from src.retrieval import recuperar_chunks

PROJECT_ROOT = Path(__file__).resolve().parent
CORPUS_DIR = PROJECT_ROOT / "corpus"

app = FastAPI(title="RAG Academico API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


class ExperimentRequest(BaseModel):
    num_queries: int = Field(default=5, ge=1, le=5)
    force_reindex: bool = False


def _document_path(filename: str) -> Path:
    path = (CORPUS_DIR / filename).resolve()
    corpus_root = CORPUS_DIR.resolve()
    if corpus_root not in path.parents or path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return path


def _document_summary(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "name": path.name,
        "size_kb": round(stat.st_size / 1024, 1),
        "modified": pd.Timestamp(stat.st_mtime, unit="s").strftime("%Y-%m-%d %H:%M"),
        "url": f"/api/documents/{path.name}/file",
    }


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/documents")
def list_documents() -> dict[str, Any]:
    CORPUS_DIR.mkdir(exist_ok=True)
    documents = [_document_summary(path) for path in sorted(CORPUS_DIR.glob("*.pdf"))]
    return {"documents": documents}


@app.get("/api/documents/{filename}/file")
def get_document(filename: str) -> FileResponse:
    path = _document_path(filename)
    return FileResponse(path, media_type="application/pdf", filename=path.name)


@app.post("/api/documents")
async def upload_documents(files: list[UploadFile] = File(...)) -> dict[str, Any]:
    CORPUS_DIR.mkdir(exist_ok=True)
    saved: list[str] = []
    for file in files:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")
        destination = CORPUS_DIR / Path(file.filename).name
        destination.write_bytes(await file.read())
        saved.append(destination.name)

    stats = ingestar_corpus(chunk_size=500, chunk_overlap=50)
    return {"saved": saved, "index": stats}


@app.post("/api/index")
def index_corpus() -> dict[str, Any]:
    return ingestar_corpus(chunk_size=500, chunk_overlap=50)


@app.post("/api/query")
def query_rag(payload: QueryRequest) -> dict[str, Any]:
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="La consulta no puede estar vacia")

    chunks = recuperar_chunks(query=query, k=payload.top_k)
    answer = responder_con_rag(query=query, chunks=chunks)
    evaluation = EvaluadorRAG().evaluar(query=query, respuesta=answer, chunks=chunks)
    guardar_consulta(
        query=query,
        modo="con_rag",
        chunks_recuperados=chunks,
        respuesta=answer,
        evaluacion=evaluation,
    )
    return {"query": query, "chunks": chunks, "answer": answer, "evaluation": evaluation}


@app.post("/api/compare")
def compare(payload: QueryRequest) -> dict[str, Any]:
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="La consulta no puede estar vacia")

    chunks = recuperar_chunks(query=query, k=payload.top_k)
    baseline = responder_sin_rag(query=query)
    rag = responder_con_rag(query=query, chunks=chunks)
    evaluator = EvaluadorRAG()
    baseline_eval = evaluator.evaluar(query=query, respuesta=baseline, chunks=[])
    rag_eval = evaluator.evaluar(query=query, respuesta=rag, chunks=chunks)
    guardar_consulta(query, "sin_rag", [], baseline, evaluacion=baseline_eval)
    guardar_consulta(query, "con_rag", chunks, rag, evaluacion=rag_eval)
    return {
        "query": query,
        "chunks": chunks,
        "baseline": {"answer": baseline, "evaluation": baseline_eval},
        "rag": {"answer": rag, "evaluation": rag_eval},
    }


@app.post("/api/experiments")
def experiments(payload: ExperimentRequest) -> dict[str, Any]:
    queries_demo = [
        "Que es Retrieval-Augmented Generation y cual es su objetivo principal?",
        "Como ayuda RAG a reducir alucinaciones en modelos de lenguaje?",
        "Cual es la diferencia entre usar evidencia recuperada y responder solo con memoria parametric?",
        "Que elementos deberia incluir una cita valida en una respuesta academica asistida por IA?",
        "Que limitaciones se mencionan sobre la calidad de recuperacion en sistemas RAG?",
    ]
    return ejecutar_experimentos(
        queries=queries_demo[: payload.num_queries],
        force_reindex=payload.force_reindex,
    )


@app.get("/api/history")
def history() -> dict[str, Any]:
    return {"items": cargar_consultas()}
