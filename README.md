# RAG Academico - Reducir Alucinaciones con Evidencia y Citas

Proyecto para EIF420 (Universidad de Costa Rica) orientado a comparar respuestas de un modelo:
- SIN RAG (sin evidencia externa)
- CON RAG (con evidencia recuperada de documentos del curso)

El objetivo es reducir alucinaciones usando fragmentos del corpus y citas de fuente/pagina.

## Estructura del proyecto

```text
rag_academico/
├── corpus/                 # PDFs y documentos del curso
├── chroma_db/              # Vector store persistente
├── logs/                   # JSON logs de consultas
├── src/
│   ├── __init__.py
│   ├── init.py             # Archivo de compatibilidad solicitado
│   ├── ingestion.py        # Carga y chunking de documentos
│   ├── retrieval.py        # Busqueda en ChromaDB
│   ├── generation.py       # Llamada OpenAI con/sin contexto
│   └── logger.py           # Guardado de logs en JSON
├── main.py                 # CLI principal
├── demo_pp1.py             # Script de demostracion automatica
├── requirements.txt
└── README.md
```

## Requisitos

- Python 3.10+
- API key de OpenAI

## Instalacion

1. Entrar a la carpeta del proyecto:

```bash
cd rag_academico
```

2. Crear y activar entorno virtual (recomendado):

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Linux/macOS
# source .venv/bin/activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Crear archivo `.env` en la raiz del proyecto con:

```env
OPENAI_API_KEY=tu_api_key_aqui
# Opcional:
OPENAI_MODEL=gpt-4.1-mini
```

## Uso

### 1) Ingestion del corpus

Coloca los PDFs del curso dentro de `corpus/` y ejecuta:

```bash
python -m src.ingestion
```

Esto extrae texto, hace chunking (`chunk_size=500`, `chunk_overlap=50`) y crea/actualiza la coleccion en ChromaDB.

### 2) CLI interactivo

```bash
python main.py
```

La CLI permite:
- Elegir modo: Solo RAG o Comparacion RAG vs Sin-RAG.
- Mostrar chunks recuperados antes de la respuesta.
- Guardar cada consulta en `logs/consultas.json`.

### 3) Demo automatica para PP1

```bash
python demo_pp1.py
```

Este script ejecuta 3 consultas de prueba en modo comparacion y guarda resultados en logs para evidencia academica.

## Detalle de modulos

- `src/ingestion.py`:
  - Carga todos los PDFs de `corpus/`.
  - Extrae texto por pagina con `pypdf`.
  - Aplica chunking con `RecursiveCharacterTextSplitter`.
  - Indexa en ChromaDB con metadatos: `source`, `page`, `chunk`.

- `src/retrieval.py`:
  - Recupera top-k chunks relevantes (default `k=3`).
  - Retorna estructura: `{text, source, page, score}`.

- `src/generation.py`:
  - `responder_sin_rag(query)` para baseline.
  - `responder_con_rag(query, chunks)` para respuesta guiada por evidencia y citas.

- `src/logger.py`:
  - Guarda logs en JSON con timestamp, query, modo, chunks y respuesta.

## Prompt del sistema para RAG

El modo RAG usa el siguiente prompt de sistema:

> "Eres un asistente academico. Responde UNICAMENTE basandote en los fragmentos de documentos proporcionados. Al final de tu respuesta, incluye una seccion '📚 Fuentes:' listando cada documento y pagina usada. Si la informacion no esta en los fragmentos, di explicitamente que no tienes evidencia suficiente."

## Notas academicas

- Si no hay evidencia suficiente en chunks recuperados, el sistema lo indica explicitamente.
- Los logs permiten comparar calidad, trazabilidad y alucinaciones entre modos.
