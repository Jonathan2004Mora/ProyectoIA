"""Interfaz PP2 del RAG academico usando Streamlit.

La app integra:
- Consulta RAG con visualizacion de evidencia.
- Comparacion RAG vs Sin RAG.
- Ejecucion de experimentos de configuracion.
- Historial de consultas con metricas.
"""

from __future__ import annotations

import re
from typing import Any, cast

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.evaluator import EvaluadorRAG
from src.experimenter import ejecutar_experimentos
from src.generation import responder_con_rag, responder_sin_rag
from src.ingestion import ingestar_corpus
from src.logger import cargar_consultas, guardar_consulta
from src.retrieval import recuperar_chunks

Chunk = dict[str, Any]
Evaluacion = dict[str, Any]

# Configuracion base de la pagina para una presentacion profesional en wide layout.
st.set_page_config(page_title="RAG Académico · EIF420", page_icon="📚", layout="wide")


# Inyeccion solicitada de Tailwind + DaisyUI.
components.html(
    """
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
      tailwind.config = { content: ["**/*"], theme: { extend: { colors: { emerald: "#1D9E75" } } } }
    </script>
    <link href="https://cdn.jsdelivr.net/npm/daisyui@4/dist/full.min.css" rel="stylesheet" type="text/css" />
    """,
    height=0,
)

# CSS custom para asegurar apariencia oscura consistente dentro de Streamlit.
st.markdown(
    """
    <style>
      :root {
        --bg-main: #0D0F14;
        --bg-card: #1A1D27;
        --accent: #1D9E75;
        --text-main: #E8E9F0;
        --text-muted: #6B7094;
        --border: #252836;
      }

      .stApp {
        background: radial-gradient(circle at 15% 10%, #1a2338 0%, var(--bg-main) 45%);
        color: var(--text-main);
      }

      .block-container {
        padding-top: 1.2rem;
      }

      .hero {
        position: sticky;
        top: 0.5rem;
        z-index: 999;
        background: rgba(13, 15, 20, 0.88);
        border: 1px solid var(--border);
        backdrop-filter: blur(6px);
        border-radius: 16px;
        padding: 0.9rem 1rem;
        margin-bottom: 1rem;
      }

      .hero-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.8rem;
        flex-wrap: wrap;
      }

      .logo-r {
        width: 42px;
        height: 42px;
        border-radius: 12px;
        display: grid;
        place-items: center;
        font-size: 1.2rem;
        font-weight: 700;
        color: white;
        background: linear-gradient(120deg, #1D9E75, #6f46ff);
      }

      .title-wrap {
        display: flex;
        gap: 0.7rem;
        align-items: center;
      }

      .title-main {
        font-size: 1.06rem;
        font-weight: 700;
        color: var(--text-main);
      }

      .title-sub {
        font-size: 0.84rem;
        color: var(--text-muted);
      }

      .badge-corpus {
        background: rgba(29, 158, 117, 0.2);
        color: #89f8cf;
        border: 1px solid rgba(29, 158, 117, 0.5);
        border-radius: 999px;
        padding: 0.35rem 0.75rem;
        font-size: 0.78rem;
        font-weight: 600;
      }

      .panel {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 0.9rem;
      }

      .chunk-card {
        background: #161923;
        border: 1px solid var(--border);
        border-left: 4px solid var(--accent);
        border-radius: 12px;
        padding: 0.8rem;
        margin-bottom: 0.65rem;
      }

      .chunk-meta {
        color: #9adfca;
        font-size: 0.8rem;
        margin-bottom: 0.35rem;
      }

      .chunk-text {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        color: var(--text-main);
        font-size: 0.86rem;
        white-space: pre-wrap;
      }

      .metric-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.55rem;
      }

      .metric-card {
        background: #151823;
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 0.65rem;
      }

      .metric-name {
        color: var(--text-muted);
        font-size: 0.78rem;
      }

      .metric-value {
        font-size: 1.02rem;
        color: var(--text-main);
        font-weight: 700;
      }

      .veredicto {
        font-size: 1.1rem;
        font-weight: 700;
        padding: 0.45rem 0.65rem;
        border-radius: 10px;
        display: inline-block;
        margin-bottom: 0.7rem;
      }

      .veredicto-confiable { background: rgba(29, 158, 117, 0.22); color: #9cf8d9; border: 1px solid rgba(29, 158, 117, 0.55); }
      .veredicto-dudoso { background: rgba(240, 178, 62, 0.2); color: #ffd79a; border: 1px solid rgba(240, 178, 62, 0.45); }
      .veredicto-alucinacion { background: rgba(239, 68, 68, 0.2); color: #ffb4b4; border: 1px solid rgba(239, 68, 68, 0.5); }

      .resp-card-red {
        background: #1a1618;
        border: 1px solid #4a2a32;
        border-radius: 12px;
        padding: 0.8rem;
      }

      .resp-card-green {
        background: #151b1a;
        border: 1px solid #275948;
        border-radius: 12px;
        padding: 0.8rem;
      }

      .source-badge {
        display: inline-block;
        margin: 0.15rem 0.2rem 0.15rem 0;
        background: rgba(29, 158, 117, 0.22);
        color: #b4ffe6;
        border: 1px solid rgba(29, 158, 117, 0.6);
        border-radius: 999px;
        padding: 0.22rem 0.6rem;
        font-size: 0.77rem;
      }

      @media (max-width: 900px) {
        .metric-grid {
          grid-template-columns: 1fr;
        }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def _render_header() -> None:
    """Header fijo con identidad visual del proyecto."""
    st.markdown(
        """
        <div class="hero">
          <div class="hero-row">
            <div class="title-wrap">
              <div class="logo-r">R</div>
              <div>
                <div class="title-main">RAG Académico · EIF420</div>
                <div class="title-sub">Inteligencia Artificial · UCR</div>
              </div>
            </div>
            <div class="badge-corpus">corpus activo</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _extraer_badges_fuentes(respuesta: str) -> list[str]:
    """Detecta posibles menciones de fuentes para mostrarlas como badges."""
    # Soporta formatos tipo: archivo.pdf p.3 | archivo.pdf pagina 3.
    patron = r"([\w\-. ]+\.pdf)\s*(?:\||,)?\s*(?:p\.?|pagina)\s*([0-9]+)"
    coincidencias = re.findall(patron, respuesta, flags=re.IGNORECASE)
    return [f"{archivo.strip()} p.{pagina}" for archivo, pagina in coincidencias]


def _clase_veredicto(veredicto: str) -> str:
    """Mapea veredicto a clase CSS para color semantico."""
    if veredicto == "CONFIABLE":
        return "veredicto veredicto-confiable"
    if veredicto == "DUDOSO":
        return "veredicto veredicto-dudoso"
    return "veredicto veredicto-alucinacion"


def _render_chunks(chunks: list[Chunk]) -> None:
    """Renderiza fragmentos recuperados como cards estilizadas."""
    if not chunks:
        st.info("No se recuperaron fragmentos para esta consulta.")
        return

    for chunk in chunks:
        source = chunk.get("source", "desconocido")
        page = chunk.get("page", "?")
        score = chunk.get("score", "?")
        text = chunk.get("text", "")
        st.markdown(
            f"""
            <div class="chunk-card">
              <div class="chunk-meta">📄 {source} · pág. {page} | score: {score}</div>
              <div class="chunk-text">{text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_metricas(evaluacion: Evaluacion) -> None:
    """Muestra metricas clave de evaluacion en cards compactas."""
    veredicto = evaluacion.get("veredicto", "ALUCINACION")
    st.markdown(
        f"<div class=\"{_clase_veredicto(veredicto)}\">Veredicto: {veredicto}</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="metric-grid">
          <div class="metric-card"><div class="metric-name">Faithfulness</div><div class="metric-value">{evaluacion.get("score_faithfulness", 0)}/10</div></div>
          <div class="metric-card"><div class="metric-name">Relevancia</div><div class="metric-value">{evaluacion.get("score_relevancia", 0)}/10</div></div>
          <div class="metric-card"><div class="metric-name">Citas válidas</div><div class="metric-value">{evaluacion.get("citas_validas", False)}</div></div>
          <div class="metric-card"><div class="metric-name">Alucinación</div><div class="metric-value">{evaluacion.get("tiene_alucinacion", True)}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    problemas_raw = evaluacion.get("problemas_detectados", [])
    if isinstance(problemas_raw, list):
      problemas = [str(p) for p in cast(list[Any], problemas_raw)]
    else:
      problemas = []
    if problemas:
        st.warning("Problemas detectados: " + " | ".join(problemas))


def _asegurar_corpus_indexado() -> None:
    """Indexa corpus por defecto al inicio si se solicita desde la UI."""
    with st.spinner("Indexando corpus base (chunk_size=500)..."):
        ingestar_corpus(chunk_size=500, chunk_overlap=50)


def _render_dataframe(data: Any) -> None:
  """Wrapper tipado para mostrar dataframes sin ruido del type checker."""
  cast(Any, st).dataframe(data, use_container_width=True)


def _render_bar_chart(data: Any) -> None:
  """Wrapper tipado para graficos de barras con stubs parcialmente tipados."""
  cast(Any, st).bar_chart(data)


def tab_consulta_rag(evaluador: EvaluadorRAG) -> None:
    """Tab 1: consulta RAG con evidencia y evaluacion visual."""
    st.markdown("### Consulta asistida por evidencia")
    query = st.text_area("Pregunta", height=140, placeholder="Escribe una pregunta academica sobre el corpus...")
    top_k = st.slider("top_k", min_value=1, max_value=10, value=3)

    if st.button("Ejecutar consulta →", type="primary", use_container_width=True):
        if not query.strip():
            st.error("Debes escribir una pregunta antes de ejecutar.")
            return

        try:
            with st.spinner("Recuperando evidencia y generando respuesta..."):
                chunks = recuperar_chunks(query=query, k=top_k)
                respuesta = responder_con_rag(query=query, chunks=chunks)
                evaluacion: Evaluacion = evaluador.evaluar(
                  query=query, respuesta=respuesta, chunks=chunks
                )

                guardar_consulta(
                    query=query,
                    modo="con_rag",
                    chunks_recuperados=chunks,
                    respuesta=respuesta,
                    evaluacion=evaluacion,
                )

            col_izq, col_der = st.columns([1.05, 0.95], gap="large")

            with col_izq:
                st.markdown("#### Fragmentos recuperados")
                _render_chunks(chunks)

            with col_der:
                st.markdown("#### Respuesta generada")
                st.markdown('<div class="panel">', unsafe_allow_html=True)
                badges = _extraer_badges_fuentes(respuesta)
                if badges:
                    st.markdown("".join([f'<span class="source-badge">[{b}]</span>' for b in badges]), unsafe_allow_html=True)
                st.markdown(respuesta)
                st.markdown("</div>", unsafe_allow_html=True)
                _render_metricas(evaluacion)
        except Exception as exc:
            st.error(f"Error durante la consulta: {exc}")


def tab_comparacion(evaluador: EvaluadorRAG) -> None:
    """Tab 2: comparacion LLM solo vs RAG con evidencia."""
    st.markdown("### Comparación directa")
    query = st.text_area("Pregunta para comparar", height=120, key="query_compare")
    top_k_compare = st.slider(
        "top_k para comparación",
        min_value=1,
        max_value=10,
        value=3,
        key="top_k_compare",
    )

    if st.button("Comparar", use_container_width=True):
        if not query.strip():
            st.error("Debes escribir una pregunta para comparar.")
            return

        try:
            with st.spinner("Ejecutando comparación RAG vs Sin RAG..."):
                chunks = recuperar_chunks(query=query, k=top_k_compare)
                resp_llm = responder_sin_rag(query=query)
                resp_rag = responder_con_rag(query=query, chunks=chunks)

                eval_llm: Evaluacion = evaluador.evaluar(
                    query=query, respuesta=resp_llm, chunks=[]
                )
                eval_rag: Evaluacion = evaluador.evaluar(
                    query=query, respuesta=resp_rag, chunks=chunks
                )

                guardar_consulta(query, "sin_rag", [], resp_llm, evaluacion=eval_llm)
                guardar_consulta(query, "con_rag", chunks, resp_rag, evaluacion=eval_rag)

            col1, col2 = st.columns(2, gap="large")
            with col1:
                st.markdown('<div class="resp-card-red">', unsafe_allow_html=True)
                st.markdown("**LLM solo**")
                st.markdown(resp_llm)
                _render_metricas(eval_llm)
                st.markdown("</div>", unsafe_allow_html=True)

            with col2:
                st.markdown('<div class="resp-card-green">', unsafe_allow_html=True)
                st.markdown("**RAG + evidencia**")
                st.markdown(resp_rag)
                _render_metricas(eval_rag)
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("#### Evaluación comparativa (JSON)")
            st.json({"llm_solo": eval_llm, "rag_con_evidencia": eval_rag})
        except Exception as exc:
            st.error(f"Error durante la comparación: {exc}")


def tab_experimentos() -> None:
    """Tab 3: benchmark de configuraciones chunk_size/top_k."""
    st.markdown("### Experimentos de configuraciones")

    num_queries = st.slider(
        "Cantidad de queries para este experimento",
        min_value=1,
        max_value=5,
        value=5,
        help="Usa menos queries para pruebas rapidas. Para evaluacion formal usa 5.",
    )
    force_reindex = st.checkbox(
        "Forzar reindexado de colecciones",
        value=False,
        help="Activalo solo si cambiaste el corpus o quieres reconstruir embeddings.",
    )

    if st.button("Correr experimentos de configuraciones →", type="primary", use_container_width=True):
        try:
            with st.spinner("Corriendo benchmark de configuraciones (puede tardar)..."):
                queries_demo = [
                    "Que es Retrieval-Augmented Generation y cual es su objetivo principal?",
                    "Como ayuda RAG a reducir alucinaciones en modelos de lenguaje?",
                    "Cual es la diferencia entre usar evidencia recuperada y responder solo con memoria parametric?",
                    "Que elementos deberia incluir una cita valida en una respuesta academica asistida por IA?",
                    "Que limitaciones se mencionan sobre la calidad de recuperacion en sistemas RAG?",
                ]
                resultado: dict[str, Any] = ejecutar_experimentos(
                    queries=queries_demo[:num_queries],
                    force_reindex=force_reindex,
                )

            resumen: list[dict[str, Any]] = []
            resumen_raw = resultado.get("resumen_por_config", [])
            if isinstance(resumen_raw, list):
                for fila in cast(list[Any], resumen_raw):
                    if isinstance(fila, dict):
                        resumen.append(cast(dict[str, Any], fila))

            if not resumen:
                st.warning("No se obtuvieron resultados de experimento.")
                return

            mejor_faith = max(
                resumen,
                key=lambda x: float(x.get("promedio_faithfulness", 0) or 0),
            )
            menor_aluc = min(
                resumen,
                key=lambda x: float(x.get("porcentaje_alucinaciones", 100) or 100),
            )

            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric("Configuraciones", len(resumen))
            kpi2.metric(
                "Mejor Faith",
                f"{mejor_faith['config']} ({mejor_faith['promedio_faithfulness']})",
            )
            kpi3.metric(
                "Menor % alucinación",
                f"{menor_aluc['config']} ({menor_aluc['porcentaje_alucinaciones']}%)",
            )

            filas_tabla: list[dict[str, Any]] = []
            for fila in resumen:
                faith = float(fila.get("promedio_faithfulness", 0) or 0)
                relev = float(fila.get("promedio_relevancia", 0) or 0)
                promedio = round((faith + relev) / 2, 2)
                filas_tabla.append(
                    {
                        "Config": str(fila.get("config", "N/A")),
                        "chunk_size": int(fila.get("chunk_size", 0) or 0),
                        "top_k": int(fila.get("top_k", 0) or 0),
                        "Faith": faith,
                        "Relev": relev,
                        "Veredicto": str(fila.get("veredicto_mas_frecuente", "N/A")),
                        "Promedio": promedio,
                    }
                )

            _render_dataframe(filas_tabla)

            st.markdown("#### Comparación visual de scores")
            chart_data = pd.DataFrame(
                {
                    "Config": [f["Config"] for f in filas_tabla],
                    "Faithfulness": [f["Faith"] for f in filas_tabla],
                    "Relevancia": [f["Relev"] for f in filas_tabla],
                }
            ).set_index("Config")
            _render_bar_chart(chart_data)

            st.markdown("#### Conclusión automática")
            st.markdown(
                f"La configuración con mejor faithfulness fue **{mejor_faith['config']}**, "
                f"mientras que la de menor tasa de alucinación fue **{menor_aluc['config']}**. "
                "Se recomienda priorizar configuraciones que balanceen faithfulness y relevancia "
                "sin elevar el porcentaje de alucinaciones."
            )
        except Exception as exc:
            st.error(f"Error al correr experimentos: {exc}")


def tab_historial() -> None:
    """Tab 4: visualizacion del historial de consultas y metricas."""
    st.markdown("### Historial de consultas")

    if st.button("Actualizar", use_container_width=False):
        st.rerun()

    try:
        consultas = cargar_consultas()
        if not consultas:
            st.info("Aun no hay consultas registradas en logs/consultas.json")
            return

        filas: list[dict[str, Any]] = []
        for item in consultas:
            evaluacion: Evaluacion = item.get("evaluacion") or {}
            filas.append(
                {
                    "timestamp": item.get("timestamp", ""),
                    "query": item.get("query", ""),
                    "modo": item.get("modo", ""),
                    "veredicto": item.get("veredicto") or evaluacion.get("veredicto"),
                    "score_faith": item.get("score_faithfulness")
                    if item.get("score_faithfulness") is not None
                    else evaluacion.get("score_faithfulness"),
                    "score_relev": item.get("score_relevancia")
                    if item.get("score_relevancia") is not None
                    else evaluacion.get("score_relevancia"),
                }
            )

        _render_dataframe(filas)
    except Exception as exc:
        st.error(f"No se pudo cargar historial: {exc}")


def main() -> None:
    """Orquestador principal de la interfaz PP2."""
    _render_header()

    with st.sidebar:
        st.markdown("### Centro de control")
        st.caption("EIF420 · RAG académico")
        if st.button("Re-indexar corpus base", use_container_width=True):
            try:
                _asegurar_corpus_indexado()
                st.success("Corpus indexado correctamente.")
            except Exception as exc:
                st.error(f"Error al indexar corpus: {exc}")

    evaluador = EvaluadorRAG()
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🔍 Consulta RAG", "⚔️ RAG vs Sin RAG", "🧪 Experimentos", "📊 Historial"]
    )

    with tab1:
        tab_consulta_rag(evaluador)
    with tab2:
        tab_comparacion(evaluador)
    with tab3:
        tab_experimentos()
    with tab4:
        tab_historial()


if __name__ == "__main__":
    main()
