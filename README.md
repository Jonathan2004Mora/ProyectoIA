# RAG Academico

$pid8000 = (Get-NetTCPConnection -LocalPort 8000 -State Listen).OwningProcess
Stop-Process -Id $pid8000 -Force
$pid5173 = (Get-NetTCPConnection -LocalPort 5173 -State Listen).OwningProcess
Stop-Process -Id $pid5173 -Force
Get-Process node -ErrorAction SilentlyContinue
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force

.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
cd frontend
npm run dev



Remove-Item -Recurse -Force .\chroma_db -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force .\logs -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force .\logs | Out-Null
Set-Content .\logs\consultas.json "[]"

.\.venv\Scripts\python.exe -m src.ingestion

Aplicacion academica para consultar un corpus de PDFs usando RAG
(`Retrieval-Augmented Generation`). La app combina un backend **FastAPI**, una
interfaz **React + Tailwind** y una base vectorial local con **ChromaDB**.

El objetivo es reducir alucinaciones: cada respuesta RAG se genera a partir de
fragmentos recuperados del corpus y muestra fuentes con documento, pagina y
evaluacion automatica.

## Que puedes probar en la app

- **Consulta RAG**: pregunta al corpus y revisa respuesta, fuentes, chunks y
  evaluacion.
- **Comparacion**: compara una respuesta sin RAG contra una respuesta con RAG.
- **Experimentos**: ejecuta un benchmark de configuraciones de `chunk_size` y
  `top_k`.
- **Historial**: revisa consultas guardadas y sus metricas.
- **Corpus**: sube PDFs, reindexa embeddings y abre documentos originales.

## Arquitectura

```text
ProyectoIA/
|-- api.py                  # API HTTP FastAPI para la interfaz React
|-- corpus/                 # PDFs usados como fuente documental
|-- chroma_db/              # Base vectorial local generada al indexar
|-- logs/                   # Historial JSON de consultas y experimentos
|-- frontend/               # App React + Vite + Tailwind
|-- src/
|   |-- ingestion.py        # Lee PDFs, crea chunks, embeddings e indice ChromaDB
|   |-- retrieval.py        # Recupera chunks relevantes desde ChromaDB
|   |-- generation.py       # Genera respuestas con y sin RAG
|   |-- evaluator.py        # Evalua faithfulness, relevancia y alucinaciones
|   |-- logger.py           # Guarda historial de consultas
|   `-- experimenter.py     # Ejecuta experimentos comparativos
|-- requirements.txt        # Dependencias Python
`-- README.md
```

## Requisitos

- Python 3.10 o superior.
- Node.js y npm.
- Una API key de OpenAI.
- PDFs dentro de `corpus/` o PDFs listos para subir desde la pantalla **Corpus**.

## Instalacion inicial

Todos los comandos se ejecutan desde la raiz del proyecto:

```powershell
cd "C:\Users\jonat\source\repos\Proyecto IA-RAG\ProyectoIA"
```

### 1. Crear el entorno virtual de Python

Si ya existe la carpeta `.venv`, puedes pasar al paso siguiente.

```powershell
python -m venv .venv
```

### 2. Instalar dependencias del backend

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Crea un archivo `.env` en la raiz del proyecto:

```env
OPENAI_API_KEY=tu_api_key_aqui
OPENAI_MODEL=gpt-4.1-mini
OPENAI_EVAL_MODEL=gpt-4o-mini
```

`OPENAI_API_KEY` es obligatoria. `OPENAI_MODEL` y `OPENAI_EVAL_MODEL` son
opcionales; si no se definen, la app usa los valores por defecto del codigo.

### 4. Instalar dependencias del frontend

```powershell
cd frontend
npm install
cd ..
```

## Ejecutar la aplicacion

La app necesita dos procesos activos: el backend en FastAPI y el frontend en
Vite.

### 1. Levantar el backend

Desde la raiz del proyecto:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

El backend queda disponible en:

```text
http://127.0.0.1:8000
```

Puedes verificarlo abriendo:

```text
http://127.0.0.1:8000/api/health
```

Debe responder:

```json
{"status":"ok"}
```

### 2. Levantar el frontend

En otra ventana, desde la raiz del proyecto:

```powershell
cd frontend
npm run dev
```

Abre la app en el navegador:

```text
http://localhost:5173
```

El frontend usa un proxy de Vite: toda llamada a `/api` se redirige al backend
en `http://127.0.0.1:8000`.

## Preparar el corpus

La app necesita PDFs indexados para responder con evidencia.

1. Abre `http://localhost:5173`.
2. Entra a la vista **Corpus**.
3. Verifica que aparezcan PDFs disponibles.
4. Si quieres agregar documentos, sube archivos PDF desde esa misma vista.
5. Despues de subir PDFs, la app los guarda en `corpus/` y ejecuta la
   indexacion automaticamente.
6. Si ya tenias PDFs en `corpus/`, usa el boton de reindexar para crear o
   actualizar `chroma_db/`.

La indexacion hace lo siguiente:

- Lee todos los PDFs de `corpus/`.
- Extrae texto por pagina.
- Divide el contenido en chunks de tamano `500` con solapamiento `50`.
- Genera embeddings con `text-embedding-3-small`.
- Guarda documentos, metadatos y embeddings en ChromaDB.

Cada chunk conserva:

- `source`: nombre del PDF.
- `page`: pagina del documento.
- `chunk`: numero de fragmento dentro de la pagina.

## Flujo recomendado para probar

1. Confirma que el backend responde en `/api/health`.
2. Abre `http://localhost:5173`.
3. En **Corpus**, confirma que hay PDFs e indexalos si hace falta.
4. En **Consulta RAG**, escribe una pregunta relacionada con tus documentos.
5. Ajusta `top_k` si quieres recuperar mas o menos evidencia.
6. Ejecuta la consulta.
7. Revisa:
   - respuesta generada;
   - fuentes citadas;
   - chunks recuperados;
   - score de faithfulness;
   - score de relevancia;
   - veredicto de evaluacion.
8. En **Comparacion**, usa la misma pregunta para comparar respuesta sin RAG y
   respuesta con RAG.
9. En **Historial**, verifica que las consultas hayan quedado registradas.
10. En **Experimentos**, corre el benchmark para comparar configuraciones.

## Endpoints principales

| Metodo | Ruta | Descripcion |
| --- | --- | --- |
| `GET` | `/api/health` | Verifica que el backend este activo. |
| `GET` | `/api/documents` | Lista PDFs disponibles en `corpus/`. |
| `GET` | `/api/documents/{filename}/file` | Abre un PDF del corpus en el navegador. |
| `POST` | `/api/documents` | Sube PDFs y reindexa el corpus. |
| `POST` | `/api/index` | Reindexa los PDFs existentes. |
| `POST` | `/api/query` | Ejecuta una consulta RAG. |
| `POST` | `/api/compare` | Compara respuesta sin RAG contra respuesta con RAG. |
| `POST` | `/api/experiments` | Ejecuta experimentos con varias configuraciones. |
| `GET` | `/api/history` | Devuelve el historial de consultas guardadas. |

## Datos que se guardan

- `chroma_db/`: indice vectorial persistente de ChromaDB.
- `logs/consultas.json`: historial de preguntas, respuestas, chunks y
  evaluaciones.
- `logs/experimentos.json`: resultados acumulados de benchmarks.
- `corpus/`: PDFs originales usados como fuente.

## Modelos usados

- Embeddings: `text-embedding-3-small`.
- Respuestas: `OPENAI_MODEL` o `gpt-4.1-mini` por defecto.
- Evaluacion automatica: `OPENAI_EVAL_MODEL` o `gpt-4o-mini` por defecto.

## Como interpretar la evaluacion

La evaluacion automatica devuelve:

- `score_faithfulness`: que tanto la respuesta se mantiene fiel a los chunks.
- `score_relevancia`: que tanto responde a la pregunta.
- `tiene_alucinacion`: si detecta informacion no respaldada.
- `citas_validas`: si las fuentes usadas son consistentes.
- `problemas_detectados`: lista de alertas.
- `veredicto`: `CONFIABLE`, `DUDOSO` o `ALUCINACION`.

## Solucion de problemas

**El frontend abre, pero las consultas fallan**

Verifica que el backend este corriendo en `http://127.0.0.1:8000` y que
`/api/health` responda `{"status":"ok"}`.

**Aparece un error sobre `OPENAI_API_KEY`**

Revisa que el archivo `.env` exista en la raiz del proyecto y que contenga una
API key valida.

**No hay documentos o no hay evidencia**

Sube PDFs desde **Corpus** o coloca PDFs en `corpus/` y reindexa. Si el PDF es
escaneado como imagen, puede que no tenga texto extraible.

**La respuesta no cita fuentes**

Revisa los chunks recuperados. Si la evidencia es pobre o no relacionada,
prueba aumentando `top_k`, agregando mejores documentos o reindexando el
corpus.

**Los experimentos tardan**

Es normal: cada configuracion puede crear embeddings, consultar el modelo y
evaluar respuestas. Reindexar forzadamente aumenta el tiempo y el costo.
