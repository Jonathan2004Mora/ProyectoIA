export type DocumentInfo = {
  name: string;
  size_kb: number;
  modified: string;
  url: string;
};

export type Chunk = {
  text: string;
  original_text?: string;
  source: string;
  page: number;
  score: number;
  was_translated?: boolean;
  translated_from?: string;
};

export type Evaluation = {
  score_faithfulness: number;
  score_relevancia: number;
  tiene_alucinacion: boolean;
  citas_validas: boolean;
  problemas_detectados: string[];
  veredicto: "CONFIABLE" | "DUDOSO" | "ALUCINACION";
};

export type QueryResult = {
  query: string;
  chunks: Chunk[];
  answer: string;
  evaluation: Evaluation;
};

export type CompareResult = {
  query: string;
  chunks: Chunk[];
  baseline: { answer: string; evaluation: Evaluation };
  rag: { answer: string; evaluation: Evaluation };
};

export type HistoryItem = {
  timestamp: string;
  query: string;
  modo: string;
  respuesta: string;
  chunks_recuperados: Chunk[];
  evaluacion?: Evaluation;
  veredicto?: string;
  score_faithfulness?: number;
  score_relevancia?: number;
};

export type ExperimentSummary = {
  config: string;
  chunk_size: number;
  top_k: number;
  promedio_faithfulness: number;
  promedio_relevancia: number;
  porcentaje_alucinaciones: number;
  veredicto_mas_frecuente: string;
};

export type ExperimentResult = {
  resumen_por_config?: ExperimentSummary[];
  resultados_detallados?: unknown[];
};
