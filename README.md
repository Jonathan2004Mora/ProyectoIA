# Integrantes

- Jose Andres Gonzalez Martinez
- Fabricio Herrera Fuentes
- Santiago Coronado Dejuk
- Jonathan Mora Castro
- Josue Navarro Sanchez

## RAG Academico (MVP)

> Prototipo academico de Retrieval-Augmented Generation que indexa PDFs, recupera evidencia relevante y compara respuestas con y sin recuperacion para reducir alucinaciones.

## Objetivo y Audiencia

Esta entrega corresponde a un MVP funcional centrado en el pipeline base de RAG para consultas academicas.

### Que hace esta entrega (MVP)

- Carga e indexa un corpus de documentos PDF en una base vectorial local.
- Recupera fragmentos relevantes para una consulta (top-k).
- Genera respuestas en dos modos: sin RAG (baseline) y con RAG (con evidencia recuperada).
- Registra trazabilidad de consultas y respuestas en logs JSON.

### Que problema resuelve

- Reduce respuestas sin soporte explicito al obligar que el modo con RAG se base en evidencia recuperada.
- Permite auditar el comportamiento del sistema mediante logs y comparacion entre escenarios.

### A quien esta dirigida

- Equipo del curso EIF420-O y docente evaluador.
- Estudiantes o investigadores que necesitan un prototipo reproducible para estudiar alucinaciones en QA academico.

## Justificacion del Corpus y del Dominio

### Dominio elegido

Inteligencia Artificial: fundamentos tecnicos, modelos de lenguaje y riesgos de uso.

Este dominio es directamente pertinente al objetivo del sistema RAG, ya que permite formular preguntas tecnicas verificables cuyas respuestas correctas pueden contrastarse contra los documentos recuperados.

### Documento 1 - Redes neuronales artificiales: fundamentos y aplicaciones

Molina Arias, M. (2025). Evidencias en Pediatria, 21:25. Hospital Universitario La Paz, Madrid.

Este articulo cubre los fundamentos del aprendizaje automatico y las redes neuronales, base tecnica sobre la que se construyen los LLMs y, por extension, los sistemas RAG. Su inclusion permite al sistema responder preguntas sobre como aprenden los modelos, que son las capas neuronales y que diferencia hay entre aprendizaje supervisado y no supervisado.

Al estar escrito para un publico medico no especializado en IA, el lenguaje es preciso pero accesible, lo que facilita evaluar si el sistema recupera y cita correctamente conceptos tecnicos fundamentales. Tiene 6 paginas, licencia CC BY-NC-ND y acceso abierto, por lo que no presenta problemas de licencia academica.

### Documento 2 - Alucinaciones de la IA: impacto en tecnologia, politica y sociedad

Barria Huidobro, C. (2024). Revista Estrategia, Poder y Desarrollo, 3(5), pp. 47-64.

Este documento esta directamente alineado con el problema central del proyecto: las alucinaciones en LLMs. Explica que son, por que ocurren, como se manifiestan y que consecuencias tienen en distintos dominios.

Su presencia en el corpus permite al sistema RAG demostrar de forma concreta su proposito, ya que las preguntas sobre alucinaciones tendran respuestas verificables y citables. Ademas, permite construir el escenario comparativo requerido por el spec: una respuesta sin recuperacion frente a una con recuperacion basada en evidencia. Tiene 18 paginas y es de acceso abierto en una revista academica con ISSN registrado.

### Documento 3 - La nueva realidad de la educacion ante los avances de la IA generativa

Garcia-Penalvo, F.J.; Llorens-Largo, F.; Vidal, J. (2024). RIED, vol. 27, num. 1. Universidades de Salamanca, Alicante y Leon.

Este articulo cubre el funcionamiento de los LLMs, el impacto de ChatGPT y GPT como modelos de lenguaje de gran escala, y las implicaciones eticas y academicas de la IA generativa.

Complementa los otros dos documentos al operar en un nivel intermedio: mas aplicado que el articulo de redes neuronales y mas conceptual que el de alucinaciones. Su autoria proviene de tres universidades espanolas de prestigio, lo que refuerza la credibilidad academica del corpus. Tiene 17 paginas, licencia Creative Commons y esta indexado en Redalyc, lo que garantiza trazabilidad y justificacion academica sin ambiguedades de licencia.

### Por que estos tres documentos funcionan juntos

Los tres documentos cubren el dominio de forma complementaria y sin solapamiento excesivo, lo cual es favorable para un sistema RAG: cada consulta puede recuperar uno o mas documentos relevantes segun su alcance semantico.

El articulo de Molina responde preguntas sobre funcionamiento tecnico de modelos, el de Barria responde preguntas sobre fallas y alucinaciones, y el de Garcia-Penalvo responde preguntas sobre LLMs y su impacto academico. Esta separacion de subtemas maximiza la utilidad de la recuperacion y permite construir la tabla comparativa de 5 consultas exigida por el spec con resultados distinguibles y verificables.

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

### Dependencias

Instalar desde requirements:

```bash
pip install -r requirements.txt
```

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

Crear archivo .env en la raiz de rag_academico con al menos:

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

Al ejecutar la CLI o demo, el usuario deberia ver:

- Chunks recuperados con fuente, pagina y score.
- Respuesta del modelo en modo sin RAG y/o con RAG segun el flujo elegido.
- Registro automatico en logs/consultas.json.

Al ejecutar experimentos, deberia generarse resumen por configuracion y persistencia en logs/experimentos.json.

## Estructura del Proyecto

```text
rag_academico/
├── corpus/
│   ├── Alucinaciones de la inteligencia artificial impacto en tecnologia, politica y sociedad.pdf
│   ├── G5_RAG_spec.md
│   ├── La nueva realidad de la educación ante los avances de la inteligencia artificial generativa.pdf
│   └── Redes neuronales artificiales fundamentos y aplicaciones.pdf
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

Este analisis se basa en el estado real del repositorio y en los entregables esperados en G5_RAG_spec.md.

## Estado actual (implementado)

- Pipeline modular de RAG implementado:
  - Ingestion: lectura de PDF, extraccion por pagina, chunking, embeddings y upsert a ChromaDB.
  - Retrieval: embedding de consulta y recuperacion top-k con metadatos.
  - Generacion: respuesta sin RAG y con RAG usando evidencia recuperada.
  - Logging: persistencia JSON de consultas y respuestas.

- Comparacion de escenarios disponible:
  - En CLI/demo: comparacion sin RAG vs con RAG.
  - En experimentacion: 4 configuraciones de chunk_size y top_k.

- Evaluacion automatica basica implementada:
  - Modulo evaluador con salida estructurada (faithfulness, relevancia, alucinacion, veredicto).

- Reproducibilidad basica:
  - Archivo de dependencias y pasos de ejecucion documentados.

## Notas y limitaciones actuales

- Requiere `OPENAI_API_KEY` valida para embeddings y generacion.
- Interfaz actual basada en consola (no incluye interfaz web).

- El repositorio no incluye, en este momento, evidencia corrida ya persistida (logs no versionados al estado inspeccionado).
- No se observa una tabla final consolidada de evidencia minima (al menos 5 consultas con columnas de consulta, recuperacion, respuesta, cita y observacion).
- No existe figura o diagrama del pipeline dentro del repositorio.
- No hay suite de pruebas automatizadas para validacion del pipeline.

## Diferencias entre el MVP actual y lo esperado segun el spec

Brecha principal hacia PP2/TI:

- El codigo cubre buena parte del comportamiento requerido, pero falta convertir ejecuciones en evidencia academica entregable y trazable.
- El spec exige evidencia comparativa clara y reproducible en formato de entregable; actualmente el soporte para producirla existe, pero no esta consolidada en artefactos finales dentro del repo.
- El spec pide integracion narrativa (reporte tecnico y discusion de riesgos); hoy existe implementacion tecnica, pero no cierre documental completo de TI.

## Roadmap (Vision Futura)

Direccion del proyecto:

- Evolucionar de MVP funcional a entrega academica completa, reproducible y defendible en vivo.

Funcionalidades y entregables pendientes para cumplir G5_RAG_spec.md:

1. Cierre de evidencia minima requerida:
   - Ejecutar y guardar una tabla comparativa con al menos 5 consultas.
   - Incluir observaciones de errores, evidencia mostrada y casos de mejora/fallo.

2. Documentacion academica de corpus y dominio:
   - Justificar seleccion de fuentes.
   - Definir explicitamente alcance tematico y tipos de preguntas objetivo.

3. Evidencia visual del pipeline:
   - Agregar al menos un esquema del flujo RAG implementado.

4. Consolidacion de evaluacion:
   - Presentar resultados comparativos interpretados (sin RAG vs con RAG y configuraciones de chunk/top-k).
   - Justificar por que una configuracion es preferible segun metricas y observaciones cualitativas.

5. Cierre TI final:
   - Integrar PP1 y PP2 en un reporte tecnico breve con resultados, limitaciones, riesgos de alucinacion y recomendaciones.

Mejoras tecnicas y de producto recomendadas:

- Agregar pruebas automatizadas para ingestion, retrieval y manejo de errores.
- Incorporar validaciones de calidad de citas (formato y cobertura de fuentes).
- Estandarizar scripts de corrida para generar evidencia con un solo comando.
- Mejorar mensajes de UX en CLI para facilitar demostracion.
