import type { CompareResult, DocumentInfo, ExperimentResult, HistoryItem, QueryResult } from "./types";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: init?.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(detail.detail || "No se pudo completar la solicitud");
  }
  return response.json() as Promise<T>;
}

export function listDocuments() {
  return request<{ documents: DocumentInfo[] }>("/api/documents");
}

export function indexCorpus() {
  return request<{ archivos_procesados: number; chunks_indexados: number }>("/api/index", { method: "POST" });
}

export function uploadDocuments(files: FileList) {
  const form = new FormData();
  Array.from(files).forEach((file) => form.append("files", file));
  return request<{ saved: string[]; index: { archivos_procesados: number; chunks_indexados: number } }>(
    "/api/documents",
    { method: "POST", body: form },
  );
}

export function queryRag(query: string, topK: number) {
  return request<QueryResult>("/api/query", {
    method: "POST",
    body: JSON.stringify({ query, top_k: topK }),
  });
}

export function compareRag(query: string, topK: number) {
  return request<CompareResult>("/api/compare", {
    method: "POST",
    body: JSON.stringify({ query, top_k: topK }),
  });
}

export function runExperiments(numQueries: number, forceReindex: boolean) {
  return request<ExperimentResult>("/api/experiments", {
    method: "POST",
    body: JSON.stringify({ num_queries: numQueries, force_reindex: forceReindex }),
  });
}

export function loadHistory() {
  return request<{ items: HistoryItem[] }>("/api/history");
}
