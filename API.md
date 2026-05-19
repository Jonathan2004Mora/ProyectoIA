# RAG Academico

Interfaz nueva con **React + Tailwind** y backend **FastAPI** para consultar un corpus PDF con RAG.

## Requisitos

- Python con `.venv` creado
- Node.js y npm
- Archivo `.env` en la raiz con:

```env
OPENAI_API_KEY=tu_api_key
```

## Instalar dependencias

Desde la raiz del proyecto:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Luego:

```powershell
cd frontend
npm install
```

## Correr backend

En una terminal, desde la raiz:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

## Correr frontend

En otra terminal:

```powershell
cd frontend
npm run dev
```

Abrir:

```text
http://localhost:5173
```

## Notas

- La API corre en `http://127.0.0.1:8000`.
- El frontend usa proxy hacia `/api`.
- Los PDFs deben estar en `corpus/`.
- La interfaz anterior de Streamlit sigue en `app.py`
