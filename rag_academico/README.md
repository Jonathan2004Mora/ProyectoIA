# RAG Academico

Sistema de Retrieval-Augmented Generation (RAG) para consultas academicas con trazabilidad por fuente y pagina.

El proyecto incluye:
- Ingestion de PDFs a ChromaDB.
- Recuperacion semantica de fragmentos relevantes.
- Generacion de respuesta en modo SIN RAG y CON RAG.
- Logging estructurado de consultas para analisis y evidencia.

## Objetivo

Reducir alucinaciones del modelo obligando a responder con evidencia recuperada.
En modo CON RAG, la respuesta debe apoyarse en los fragmentos entregados y reportar fuentes.

## Estructura real del proyecto

```text
rag_academico/
├── corpus/                  # PDFs fuente
├── chroma_db/               # Base vectorial persistente
├── logs/                    # Salidas JSON de consultas/experimentos
├── main.py                  # CLI interactiva principal
├── demo_pp1.py              # Demo automatica de PP1
├── requirements.txt
├── README.md
└── src/
    ├── __init__.py
    ├── init.py
    ├── ingestion.py         # Carga, chunking, embeddings y upsert
    ├── retrieval.py         # Top-k retrieval desde Chroma
    ├── generation.py        # Respuesta con/sin contexto RAG
    ├── logger.py            # Persistencia en logs/consultas.json
    ├── evaluator.py         # Evaluacion estructurada de respuestas
    └── experimenter.py      # Corridas comparativas de configuracion
```

## Requisitos

- Python 3.11+
- API key valida de OpenAI

## Instalacion

### 1) Entrar al proyecto

```bash
cd rag_academico
```

### 2) Crear entorno virtual

```bash
python -m venv .venv
```

### 3) Activar entorno virtual

Windows PowerShell:

```powershell
& .\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 4) Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5) Configurar variables de entorno

Crear archivo `.env` en la carpeta `rag_academico/`:

```env
OPENAI_API_KEY=tu_api_key_real
OPENAI_MODEL=gpt-4.1-mini
```

`OPENAI_MODEL` es opcional; si no se define, se usa el default del codigo.

## Flujo recomendado de uso

### Paso 1: Preparar corpus

Copiar PDFs a `rag_academico/corpus/`.

### Paso 2: Ejecutar ingestion

Desde la carpeta `rag_academico/`:

```bash
python -m src.ingestion
```

Que hace este paso:
- Extrae texto por pagina.
- Aplica chunking (tamano y solapamiento configurables).
- Genera embeddings.
- Inserta/actualiza en ChromaDB con metadatos (`source`, `page`, `chunk`).

### Paso 3: Ejecutar CLI principal

Forma recomendada (desde la raiz del repo `RAG_AI/`):

```bash
python -m rag_academico.main
```

Forma alternativa (desde cualquier ruta):

```bash
python rag_academico/main.py
```

La CLI permite:
- Elegir modo `Solo RAG` o `Comparacion RAG vs Sin-RAG`.
- Ver chunks recuperados (transparencia).
- Registrar cada consulta en `logs/consultas.json`.
- Reintento automatico con ingestion si la coleccion no existe.

### Paso 4 (opcional): Ejecutar demo automatica PP1

Desde la carpeta `rag_academico/`:

```bash
python demo_pp1.py
```

Ejecuta consultas predefinidas y guarda resultados para evidencia.

## Salidas generadas

- `logs/consultas.json`: historial de consultas y respuestas.
- `chroma_db/`: almacenamiento persistente de embeddings y metadatos.

## Modulos clave

- `src/ingestion.py`: ingestion y indexacion vectorial.
- `src/retrieval.py`: recuperacion top-k por similitud.
- `src/generation.py`: respuesta del modelo con o sin RAG.
- `src/logger.py`: persistencia JSON.
- `main.py`: orquestacion de flujo interactivo.

## Troubleshooting rapido

### Error: OPENAI_API_KEY no encontrada

Verificar `.env` y que el entorno virtual activo tenga acceso al archivo.

### Error: coleccion no existe

Ejecutar ingestion manualmente o dejar que `main.py` haga auto-ingestion.

### Error de importacion al ejecutar main

Usar `python -m rag_academico.main` desde la raiz del repo.

## Buenas practicas para el equipo

- Mantener `corpus/` con documentos versionados si corresponde a pruebas compartidas.
- Evitar subir claves en `.env`.
- Correr ingestion despues de cambios grandes en corpus.
- Validar con una consulta de control antes de demos.
