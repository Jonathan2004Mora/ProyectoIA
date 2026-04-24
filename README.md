# Integrantes

- Jose Andres Gonzalez Martinez
- Fabricio Herrera Fuentes
- Santiago Coronado Dejuk
- Jonathan Mora Castro
- Josue Navarro Sanchez

## RAG Academico (MVP)

> Prototipo academico de Retrieval-Augmented Generation que indexa PDFs, recupera evidencia relevante y compara respuestas con y sin recuperacion para reducir alucinaciones.

## Objetivo y Audiencia

Este sistema está dirigido principalmente a estudiantes universitarios de carreras técnicas que necesitan consultar documentos académicos y obtener respuestas verificables con citas explícitas, evitando información generada sin respaldo real.
Como público secundario, también es útil para docentes, investigadores y profesionales en dominios donde responder sin evidencia tiene consecuencias directas (salud, derecho, educación), ya que el sistema muestra siempre el fragmento y la fuente que respaldaron cada respuesta.

### Que hace esta entrega (MVP)

- Carga e indexa un corpus de documentos PDF en una base vectorial local.
- Recupera fragmentos relevantes para una consulta (top-k).
- Genera respuestas en dos modos: sin RAG (baseline) y con RAG (con evidencia recuperada).
- Registra trazabilidad de consultas y respuestas en logs JSON.

### Que problema resuelve

- Reduce respuestas sin soporte explicito al obligar que el modo con RAG se base en evidencia recuperada.
- Permite auditar el comportamiento del sistema mediante logs y comparacion entre escenarios.

### A quien esta dirigida

- Estudiantes o investigadores que necesitan un prototipo reproducible para estudiar alucinaciones en QA academico.

## Configuracion y Requisitos

### Lenguaje y stack

- Python 3.11+
- Arquitectura modular en scripts Python (CLI)
- Base vectorial local con ChromaDB
- API de OpenAI para embeddings y generacion

### Librerias clave

- openai
- chromadb
- numpy
- pypdf
- langchain-text-splitters
- python-dotenv
- pydantic
- pandas (declarada en dependencias)

## Instalacion paso a paso

1. Entrar al proyecto:

```bash
cd rag_academico
```

1. Crear entorno virtual:

```bash
python -m venv .venv
```

1. Activar entorno virtual:

Windows PowerShell:

```powershell
& .\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

1. Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Guia de Ejecucion

## 1. Configuracion previa

Crear archivo .env en la raiz de rag_academico con:

```env
OPENAI_API_KEY=tu_api_key_real
OPENAI_MODEL=gpt-4.1-mini
```

Notas:

- OPENAI_API_KEY es obligatoria.
- OPENAI_MODEL es opcional; si no se define, el proyecto usa su valor por defecto.

## 2. Comandos para ejecutar el proyecto

1) Preparar corpus:

- Colocar archivos PDF en la carpeta corpus.

1) Ejecutar ingestion (indexacion):

```bash
python -m src.ingestion
```

1) Ejecutar la CLI principal:

```bash
python main.py
```

1) Ejecutar demo automatica (opcional):

```bash
python demo_pp1.py
```

1) Ejecutar experimentos comparativos (avance implementado):

```bash
python -m src.experimenter
```

## 3. Resultado esperado

Al ejecutar la CLI, el usuario deberia ver:

- Chunks recuperados con fuente, pagina y score.
- Respuesta del modelo en modo sin RAG y/o con RAG segun el flujo elegido.
- Registro automatico en logs/consultas.json.

Al ejecutar experimentos, deberia generarse persistencia en logs/experimentos.json.

## Estructura del Proyecto

```text
rag_academico/
├── corpus/
│   ├── Alucinaciones de la inteligencia artificial impacto en tecnologia, politica y sociedad.pdf
│   ├── G5_RAG_spec.md
│   ├── La nueva realidad de la educación ante los avances de la inteligencia artificial generativa.pdf
│   ├── Redes neuronales artificiales fundamentos y aplicaciones.pdf
│   └── Volley.pdf
├── demo_pp1.py
├── main.py
├── README.md
├── README2.md
├── README4.md
├── requirements.txt
└── src/
  ├── __init__.py
  ├── evaluator.py
  ├── experimenter.py
  ├── generation.py
  ├── ingestion.py
  ├── init.py
  ├── logger.py
  └── retrieval.py
```

## Estado Actual y Limitaciones

## Estado actual (implementado)

- Pipeline modular de RAG implementado:
  - Ingestion: lectura de PDF, extraccion por pagina, chunking, embeddings y upsert a ChromaDB.
  - Retrieval: embedding de consulta y recuperacion top-k con metadatos.
  - Generacion: respuesta sin RAG y con RAG usando evidencia recuperada.
  - Logging: persistencia JSON de consultas y respuestas.

- Comparacion de escenarios disponible:
  - En CLI/demo: comparacion sin RAG vs con RAG.
  - En experimentacion: 4 configuraciones de chunk_size y top_k.        VER ANALIZAR

- Evaluacion automatica basica implementada:
  - Modulo evaluador con salida estructurada (faithfulness, relevancia, alucinacion, veredicto).     REVISAR

- Reproducibilidad basica:
  - Archivo de dependencias y pasos de ejecucion documentados.

## Notas y limitaciones actuales

- Requiere `OPENAI_API_KEY` valida para embeddings y generacion.
- Interfaz actual basada en consola (no incluye interfaz web).
- No existe figura o diagrama del pipeline dentro del repositorio.

## Roadmap (Vision Futura)

Funcionalidades y entregables pendientes para cumplir G5_RAG_spec.md:

1. Interfaz de usuario:  
   - Disenar e implementar una interfaz (web) para consultas sin depender de la terminal.
   - Mantener en la interfaz la trazabilidad actual: chunks recuperados, fuentes y paginas.

1. Evidencia visual del pipeline:
   - Agregar al menos un esquema del flujo RAG implementado.

1. Cierre TI final:
   - Integrar PP1 y PP2 en un reporte tecnico breve con resultados, limitaciones, riesgos de alucinacion y recomendaciones.
