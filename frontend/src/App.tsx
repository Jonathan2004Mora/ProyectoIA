import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  BookOpen,
  CheckCircle2,
  FileText,
  FlaskConical,
  History,
  Loader2,
  RefreshCw,
  Scale,
  Search,
  Upload,
} from "lucide-react";

import {
  compareRag,
  indexCorpus,
  listDocuments,
  loadHistory,
  queryRag,
  runExperiments,
  uploadDocuments,
} from "./api";
import { Badge } from "./components/ui/badge";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { Textarea } from "./components/ui/textarea";
import type {
  Chunk,
  CompareResult,
  DocumentInfo,
  Evaluation,
  ExperimentResult,
  ExperimentSummary,
  HistoryItem,
  QueryResult,
} from "./types";

type View = "consulta" | "comparacion" | "experimentos" | "historial" | "corpus";

const navItems: Array<{ id: View; label: string; icon: typeof Search }> = [
  { id: "consulta", label: "Consulta RAG", icon: Search },
  { id: "comparacion", label: "Comparacion", icon: Scale },
  { id: "experimentos", label: "Experimentos", icon: FlaskConical },
  { id: "historial", label: "Historial", icon: History },
  { id: "corpus", label: "Corpus", icon: BookOpen },
];

const examples = [
  "Como ayuda RAG a reducir alucinaciones en modelos de lenguaje?",
  "Que limitaciones se mencionan sobre la calidad de recuperacion?",
  "Que diferencia hay entre usar evidencia recuperada y memoria parametrica?",
];

function verdictVariant(verdict?: string) {
  if (verdict === "CONFIABLE") return "success";
  if (verdict === "DUDOSO") return "warning";
  return "danger";
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-border bg-secondary/45 px-3 py-2">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-semibold">{value}</p>
    </div>
  );
}

function EvaluationPanel({ evaluation }: { evaluation: Evaluation }) {
  return (
    <div className="space-y-3">
      <Badge variant={verdictVariant(evaluation.veredicto)}>{evaluation.veredicto}</Badge>
      <div className="grid gap-2 sm:grid-cols-2">
        <Metric label="Faithfulness" value={`${evaluation.score_faithfulness}/10`} />
        <Metric label="Relevancia" value={`${evaluation.score_relevancia}/10`} />
        <Metric label="Citas validas" value={evaluation.citas_validas ? "Si" : "No"} />
        <Metric label="Alucinacion" value={evaluation.tiene_alucinacion ? "Detectada" : "No detectada"} />
      </div>
      {evaluation.problemas_detectados?.length > 0 && (
        <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          {evaluation.problemas_detectados.join(" | ")}
        </div>
      )}
    </div>
  );
}

function EvidenceList({ chunks }: { chunks: Chunk[] }) {
  if (!chunks.length) {
    return (
      <div className="rounded-lg border border-dashed border-border p-6 text-sm text-muted-foreground">
        No hay evidencia recuperada todavia. Ejecuta una consulta para inspeccionar los fragmentos.
      </div>
    );
  }
  return (
    <div className="space-y-3">
      {chunks.map((chunk, index) => (
        <article key={`${chunk.source}-${chunk.page}-${index}`} className="rounded-lg border border-border bg-white p-4">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <Badge variant="outline">#{index + 1}</Badge>
            <span className="text-sm font-medium">{chunk.source}</span>
            <span className="text-xs text-muted-foreground">p. {chunk.page}</span>
            <span className="ml-auto rounded-md bg-secondary px-2 py-1 text-xs text-muted-foreground">
              score {chunk.score}
            </span>
          </div>
          <p className="line-clamp-6 whitespace-pre-wrap text-sm leading-6 text-slate-700">{chunk.text}</p>
        </article>
      ))}
    </div>
  );
}

function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="rounded-lg border border-dashed border-border bg-white/60 p-8 text-center">
      <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-md bg-secondary">
        <FileText className="h-5 w-5 text-muted-foreground" />
      </div>
      <p className="font-medium">{title}</p>
      <p className="mx-auto mt-1 max-w-md text-sm text-muted-foreground">{detail}</p>
    </div>
  );
}

function Sidebar({
  active,
  setActive,
  documents,
  onRefresh,
  busy,
}: {
  active: View;
  setActive: (view: View) => void;
  documents: DocumentInfo[];
  onRefresh: () => void;
  busy: boolean;
}) {
  return (
    <aside className="border-r border-border bg-white/75 px-4 py-5 backdrop-blur">
      <div className="mb-7 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-border bg-slate-950 text-sm font-semibold text-white">
          R
        </div>
        <div>
          <p className="text-sm font-semibold">RAG Academico</p>
          <p className="text-xs text-muted-foreground">Workbench de evidencia</p>
        </div>
      </div>

      <nav className="space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const selected = item.id === active;
          return (
            <button
              key={item.id}
              onClick={() => setActive(item.id)}
              className={`flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm transition ${
                selected ? "bg-slate-950 text-white" : "text-slate-600 hover:bg-secondary hover:text-slate-950"
              }`}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="mt-8 rounded-lg border border-border bg-card p-4">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium">Corpus activo</p>
          <Button variant="ghost" size="icon" onClick={onRefresh} disabled={busy} title="Actualizar corpus">
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          </Button>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">{documents.length} documentos PDF indexables</p>
        <div className="mt-3 space-y-2">
          {documents.slice(0, 4).map((doc) => (
            <div key={doc.name} className="rounded-md border border-border bg-white px-3 py-2">
              <p className="truncate text-xs font-medium">{doc.name}</p>
              <p className="text-xs text-muted-foreground">{doc.size_kb} KB</p>
            </div>
          ))}
          {!documents.length && <p className="text-xs text-muted-foreground">Sube PDFs para empezar.</p>}
        </div>
      </div>
    </aside>
  );
}

function QueryView() {
  const [query, setQuery] = useState(examples[0]);
  const [topK, setTopK] = useState(3);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function run() {
    setLoading(true);
    setError("");
    try {
      setResult(await queryRag(query, topK));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al consultar");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="space-y-5">
      <div>
        <p className="text-sm font-medium text-primary">Consulta con trazabilidad</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-normal">Pregunta al corpus con evidencia verificable</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
          Recupera fragmentos de PDFs, genera una respuesta condicionada por evidencia y evalua riesgo de alucinacion.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Pregunta academica</CardTitle>
          <CardDescription>El modelo responde solo con fragmentos recuperados del corpus.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea value={query} onChange={(event) => setQuery(event.target.value)} />
          <div className="flex flex-wrap items-center gap-3">
            <label className="text-sm text-muted-foreground">top_k</label>
            <Input
              className="w-24"
              type="number"
              min={1}
              max={10}
              value={topK}
              onChange={(event) => setTopK(Number(event.target.value))}
            />
            <Button onClick={run} disabled={loading || !query.trim()}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
              Ejecutar consulta
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {examples.map((example) => (
              <button key={example} onClick={() => setQuery(example)} className="rounded-md border px-2.5 py-1 text-xs text-muted-foreground hover:bg-secondary">
                {example}
              </button>
            ))}
          </div>
          {error && <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}
        </CardContent>
      </Card>

      {result ? (
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1.05fr)_minmax(360px,0.95fr)]">
          <Card>
            <CardHeader>
              <CardTitle>Respuesta generada</CardTitle>
              <CardDescription>Salida RAG con fuentes al final de la respuesta.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="whitespace-pre-wrap rounded-lg border border-border bg-white p-5 text-sm leading-7">
                {result.answer}
              </div>
            </CardContent>
          </Card>
          <div className="space-y-5">
            <Card>
              <CardHeader>
                <CardTitle>Evaluacion</CardTitle>
              </CardHeader>
              <CardContent>
                <EvaluationPanel evaluation={result.evaluation} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Evidencia recuperada</CardTitle>
              </CardHeader>
              <CardContent>
                <EvidenceList chunks={result.chunks} />
              </CardContent>
            </Card>
          </div>
        </div>
      ) : (
        <EmptyState title="Aun no hay respuesta" detail="Ejecuta una consulta para ver la respuesta, sus fuentes y la evaluacion automatica." />
      )}
    </section>
  );
}

function CompareView() {
  const [query, setQuery] = useState(examples[2]);
  const [topK, setTopK] = useState(3);
  const [result, setResult] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(false);

  async function run() {
    setLoading(true);
    try {
      setResult(await compareRag(query, topK));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="space-y-5">
      <div>
        <p className="text-sm font-medium text-primary">Contraste controlado</p>
        <h1 className="mt-1 text-2xl font-semibold">RAG contra memoria parametrica</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
          Compara una respuesta libre del LLM contra una respuesta respaldada por documentos.
        </p>
      </div>
      <Card>
        <CardContent className="space-y-4 p-5">
          <Textarea value={query} onChange={(event) => setQuery(event.target.value)} />
          <div className="flex flex-wrap items-center gap-3">
            <Input className="w-24" type="number" min={1} max={10} value={topK} onChange={(event) => setTopK(Number(event.target.value))} />
            <Button onClick={run} disabled={loading || !query.trim()}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Scale className="h-4 w-4" />}
              Comparar
            </Button>
          </div>
        </CardContent>
      </Card>

      {result ? (
        <div className="grid gap-5 xl:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>LLM solo</CardTitle>
              <CardDescription>Sin evidencia externa recuperada.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="whitespace-pre-wrap rounded-lg border border-border bg-white p-4 text-sm leading-7">{result.baseline.answer}</div>
              <EvaluationPanel evaluation={result.baseline.evaluation} />
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>RAG con evidencia</CardTitle>
              <CardDescription>Respuesta condicionada por chunks del corpus.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="whitespace-pre-wrap rounded-lg border border-border bg-white p-4 text-sm leading-7">{result.rag.answer}</div>
              <EvaluationPanel evaluation={result.rag.evaluation} />
            </CardContent>
          </Card>
        </div>
      ) : (
        <EmptyState title="Comparacion pendiente" detail="Ejecuta una pregunta para ver diferencias en faithfulness, relevancia y alucinaciones." />
      )}
    </section>
  );
}

function ExperimentsView() {
  const [numQueries, setNumQueries] = useState(5);
  const [forceReindex, setForceReindex] = useState(false);
  const [result, setResult] = useState<ExperimentResult | null>(null);
  const [loading, setLoading] = useState(false);

  async function run() {
    setLoading(true);
    try {
      setResult(await runExperiments(numQueries, forceReindex));
    } finally {
      setLoading(false);
    }
  }

  const summary = result?.resumen_por_config ?? [];
  const best = useMemo(
    () => summary.reduce<ExperimentSummary | null>((current, item) => (!current || item.promedio_faithfulness > current.promedio_faithfulness ? item : current), null),
    [summary],
  );

  return (
    <section className="space-y-5">
      <div>
        <p className="text-sm font-medium text-primary">Benchmark</p>
        <h1 className="mt-1 text-2xl font-semibold">Evaluacion de configuraciones RAG</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
          Mide combinaciones de chunking y recuperacion para priorizar respuestas fieles al corpus.
        </p>
      </div>
      <Card>
        <CardContent className="flex flex-wrap items-center gap-4 p-5">
          <Input className="w-32" type="number" min={1} max={5} value={numQueries} onChange={(event) => setNumQueries(Number(event.target.value))} />
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={forceReindex} onChange={(event) => setForceReindex(event.target.checked)} />
            Forzar reindexado
          </label>
          <Button onClick={run} disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <BarChart3 className="h-4 w-4" />}
            Correr benchmark
          </Button>
        </CardContent>
      </Card>
      {summary.length ? (
        <Card>
          <CardHeader>
            <CardTitle>Resultados</CardTitle>
            <CardDescription>{best ? `Mejor faithfulness: ${best.config}` : "Resumen por configuracion"}</CardDescription>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="border-b text-xs text-muted-foreground">
                <tr>
                  <th className="py-2">Config</th>
                  <th>chunk</th>
                  <th>top_k</th>
                  <th>Faith</th>
                  <th>Relevancia</th>
                  <th>Alucinaciones</th>
                  <th>Veredicto</th>
                </tr>
              </thead>
              <tbody>
                {summary.map((row) => (
                  <tr key={row.config} className="border-b last:border-0">
                    <td className="py-3 font-medium">{row.config}</td>
                    <td>{row.chunk_size}</td>
                    <td>{row.top_k}</td>
                    <td>{row.promedio_faithfulness}</td>
                    <td>{row.promedio_relevancia}</td>
                    <td>{row.porcentaje_alucinaciones}%</td>
                    <td><Badge variant={verdictVariant(row.veredicto_mas_frecuente)}>{row.veredicto_mas_frecuente}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      ) : (
        <EmptyState title="Sin benchmark todavia" detail="Corre experimentos para comparar configuraciones de recuperacion." />
      )}
    </section>
  );
}

function HistoryView() {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    setLoading(true);
    try {
      setItems((await loadHistory()).items.reverse());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <section className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-primary">Trazabilidad</p>
          <h1 className="mt-1 text-2xl font-semibold">Historial de consultas</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">Audita preguntas, modo de respuesta y evaluaciones guardadas.</p>
        </div>
        <Button variant="outline" onClick={refresh} disabled={loading}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          Actualizar
        </Button>
      </div>
      {items.length ? (
        <div className="space-y-3">
          {items.map((item, index) => (
            <Card key={`${item.timestamp}-${index}`}>
              <CardContent className="p-4">
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <Badge variant="outline">{item.modo}</Badge>
                  {item.veredicto && <Badge variant={verdictVariant(item.veredicto)}>{item.veredicto}</Badge>}
                  <span className="text-xs text-muted-foreground">{new Date(item.timestamp).toLocaleString()}</span>
                </div>
                <p className="font-medium">{item.query}</p>
                <p className="mt-2 line-clamp-2 text-sm leading-6 text-muted-foreground">{item.respuesta}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState title="No hay consultas guardadas" detail="El historial se completa cuando ejecutas consultas o comparaciones." />
      )}
    </section>
  );
}

function CorpusView({ documents, reload }: { documents: DocumentInfo[]; reload: () => Promise<void> }) {
  const [selected, setSelected] = useState<DocumentInfo | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function handleUpload(files: FileList | null) {
    if (!files?.length) return;
    setBusy(true);
    setMessage("");
    try {
      const response = await uploadDocuments(files);
      setMessage(`Guardados ${response.saved.length} PDF. Indexados ${response.index.chunks_indexados} chunks.`);
      await reload();
    } finally {
      setBusy(false);
    }
  }

  async function reindex() {
    setBusy(true);
    setMessage("");
    try {
      const response = await indexCorpus();
      setMessage(`Corpus reindexado: ${response.chunks_indexados} chunks en ${response.archivos_procesados} documentos.`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-5">
      <div>
        <p className="text-sm font-medium text-primary">Biblioteca</p>
        <h1 className="mt-1 text-2xl font-semibold">Corpus documental</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
          Administra PDFs, reindexa embeddings y abre documentos para validar la evidencia original.
        </p>
      </div>
      <Card>
        <CardContent className="flex flex-wrap items-center gap-3 p-5">
          <label className="inline-flex cursor-pointer items-center gap-2 rounded-md border border-border bg-white px-4 py-2 text-sm font-medium hover:bg-secondary">
            <Upload className="h-4 w-4" />
            Subir PDFs
            <input className="hidden" type="file" accept="application/pdf" multiple onChange={(event) => void handleUpload(event.target.files)} />
          </label>
          <Button variant="outline" onClick={reindex} disabled={busy}>
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Reindexar corpus
          </Button>
          {message && <span className="text-sm text-muted-foreground">{message}</span>}
        </CardContent>
      </Card>
      <div className="grid gap-5 xl:grid-cols-[360px_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Documentos</CardTitle>
            <CardDescription>{documents.length} PDFs disponibles</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {documents.map((doc) => (
              <button
                key={doc.name}
                onClick={() => setSelected(doc)}
                className={`w-full rounded-md border px-3 py-3 text-left transition ${
                  selected?.name === doc.name ? "border-primary bg-emerald-50" : "border-border bg-white hover:bg-secondary"
                }`}
              >
                <p className="truncate text-sm font-medium">{doc.name}</p>
                <p className="mt-1 text-xs text-muted-foreground">{doc.size_kb} KB · {doc.modified}</p>
              </button>
            ))}
            {!documents.length && <p className="text-sm text-muted-foreground">No hay PDFs en el corpus.</p>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>{selected ? selected.name : "Vista del documento"}</CardTitle>
            <CardDescription>{selected ? "PDF servido desde el backend local" : "Selecciona un PDF para abrirlo aqui."}</CardDescription>
          </CardHeader>
          <CardContent>
            {selected ? (
              <iframe className="h-[720px] w-full rounded-lg border border-border bg-white" src={selected.url} title={selected.name} />
            ) : (
              <EmptyState title="Ningun documento seleccionado" detail="El visor permite contrastar las citas contra el PDF fuente." />
            )}
          </CardContent>
        </Card>
      </div>
    </section>
  );
}

export default function App() {
  const [active, setActive] = useState<View>("consulta");
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);

  async function refreshDocuments() {
    setLoadingDocs(true);
    try {
      setDocuments((await listDocuments()).documents);
    } finally {
      setLoadingDocs(false);
    }
  }

  useEffect(() => {
    void refreshDocuments();
  }, []);

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,#f8fafc_0%,#eef2f6_100%)]">
      <div className="grid min-h-screen workspace-grid">
        <Sidebar active={active} setActive={setActive} documents={documents} onRefresh={() => void refreshDocuments()} busy={loadingDocs} />
        <main className="min-w-0 px-5 py-5 lg:px-8">
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">EIF420 · Inteligencia Artificial</p>
              <p className="mt-1 text-sm text-slate-600">Sistema RAG para responder con PDFs, fuentes y evaluacion automatica.</p>
            </div>
            <div className="flex items-center gap-2 rounded-md border border-border bg-white px-3 py-2 text-sm text-slate-600">
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
              API local conectada
            </div>
          </div>
          {active === "consulta" && <QueryView />}
          {active === "comparacion" && <CompareView />}
          {active === "experimentos" && <ExperimentsView />}
          {active === "historial" && <HistoryView />}
          {active === "corpus" && <CorpusView documents={documents} reload={refreshDocuments} />}
        </main>
      </div>
    </div>
  );
}
