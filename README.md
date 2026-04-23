# RAG Academico (PP1)

## Descripción general

Este proyecto implementa un sistema RAG (Retrieval-Augmented Generation) orientado a consultas académicas sobre documentos PDF locales.

En su estado actual (PP1), el flujo principal permite:

- Ingestar documentos desde `corpus/` a una base vectorial local.
- Recuperar fragmentos relevantes por similitud semántica.
- Generar respuestas en modo sin RAG y con RAG.
- Registrar trazabilidad de cada consulta en logs JSON.

## Funcionalidades disponibles

- Ingestión de PDFs:
  - Lectura de archivos `.pdf` desde `corpus/`.
  - Extracción de texto por página.
  - Segmentación en chunks con tamaño y solapamiento configurables.
  - Generación de embeddings con OpenAI (`text-embedding-3-small`).
  - Persistencia en ChromaDB con `upsert` y metadatos (`source`, `page`, `chunk`).

- Recuperación semántica (retrieval):
  - Embedding de la consulta.
  - Búsqueda Top-k en ChromaDB.
  - Retorno de resultados con texto, fuente, página y score.

- Generación de respuestas:
  - `responder_sin_rag(query)`: baseline sin contexto recuperado.
  - `responder_con_rag(query, chunks)`: respuesta basada en evidencia recuperada.
  - En ausencia de evidencia, retorna mensaje explícito de evidencia insuficiente.

- CLI interactiva (`main.py`):
  - Modo `Solo RAG`.
  - Modo `Comparación RAG vs Sin-RAG`.
  - Visualización de chunks recuperados en consola.
  - Reintento automático con ingestión si la colección no existe.
  - Registro automático en `logs/consultas.json`.

- Demo automatizada (`demo_pp1.py`):
  - Ejecuta consultas predefinidas.
  - Guarda respuestas sin RAG y con RAG en logs.

- Módulos adicionales presentes en el código:
  - Evaluación estructurada de respuestas (`src/evaluator.py`).
  - Script de experimentación comparativa de configuraciones (`src/experimenter.py`).

## Tecnologías utilizadas

- Python 3.11+
- OpenAI API (`openai`)
- ChromaDB (`chromadb`)
- Extracción de PDF (`pypdf`)
- Chunking de texto (`langchain-text-splitters`)
- Variables de entorno (`python-dotenv`)
- Validación de esquemas (`pydantic`)
- Soporte numérico (`numpy`)
- Dependencia declarada en el proyecto: `pandas`

## Instalación y ejecución

### 1) Instalar dependencias

```bash
cd rag_academico
python -m venv .venv
```

Windows PowerShell:

```powershell
& .\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Instalar paquetes:

```bash
pip install -r requirements.txt
```

### 2) Configurar variables de entorno

Crear archivo `.env` en la carpeta `rag_academico/`:

```env
OPENAI_API_KEY=tu_api_key_real
OPENAI_MODEL=gpt-4.1-mini
```

### 3) Preparar el corpus

Colocar los archivos PDF en `rag_academico/corpus/`.

### 4) Ejecutar ingestión

```bash
python -m src.ingestion
```

### 5) Ejecutar aplicación principal

```bash
python main.py
```

### 6) (Opcional) Ejecutar demo PP1

```bash
python demo_pp1.py
```

## Estructura del proyecto

```text
rag_academico/
├── corpus/
├── demo_pp1.py
├── main.py
├── README.md
├── README2.md
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

## Estado del proyecto

Avance parcial correspondiente a PP1.

El flujo principal funcional está centrado en ingestión, recuperación, generación y logging para consultas académicas con evidencia.

## Notas y limitaciones actuales

- Requiere `OPENAI_API_KEY` válida para embeddings y generación.
- Depende de calidad de extracción de texto en PDFs (documentos escaneados pueden extraer poco o nada).
- El sistema trabaja sobre corpus local; no hay integración con fuentes externas.
- Interfaz actual basada en consola (no incluye interfaz web).
- No se observan pruebas automatizadas en la estructura actual.
- La calidad final depende de la cobertura del corpus y de la recuperación Top-k configurada.
