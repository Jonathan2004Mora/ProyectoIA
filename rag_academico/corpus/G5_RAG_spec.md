# EIF420-O • Inteligencia Artificial — SPEC

## RAG (LLM + búsqueda): reducir alucinaciones con evidencia y citas

> TI + PP1 + PP2 unificados

---

## 1. Reglas generales

- Todo el trabajo del grupo debe mantener coherencia entre investigación, diseño experimental y prototipo/simulación.
- PP1 y PP2 no son trabajos aparte sin relación; forman parte del desarrollo del TI y deben integrarse claramente en el reporte final.
- El producto final debe ser reproducible: README, dependencias, instrucciones y evidencia.
- Si se usa IA generativa, debe declararse qué herramienta se usó, para qué, y el grupo debe poder explicar y defender todo lo entregado.
- La defensa en vivo es obligatoria y forma parte de la evaluación, tal como lo establece la carta al estudiante.

---

## 2. Propósito específico del tema

El grupo investigará y desarrollará un prototipo académico de tipo RAG (Retrieval-Augmented Generation), es decir, un sistema que combine un modelo de lenguaje con un componente de búsqueda/recuperación de información para responder preguntas apoyándose en fuentes concretas.

El propósito del trabajo es demostrar que la incorporación explícita de evidencia y citas puede reducir alucinaciones, mejorar la trazabilidad de las respuestas y hacer más defendible el uso del sistema.

La intención no es construir un "nuevo ChatGPT", sino comprender y demostrar, de manera técnica y medible, cómo la búsqueda, la selección de documentos y la referencia explícita a fuentes pueden mejorar la calidad de un sistema de preguntas y respuestas.

---

## 3. Qué deben investigar y comprender

- Qué es un sistema RAG y cuál es la diferencia entre un LLM que responde solo con su conocimiento paramétrico y un sistema que recupera evidencia externa antes de responder.
- Cuál es la función de cada componente mínimo del pipeline: corpus, chunking o segmentación, índice/búsqueda, recuperación de contexto, generación de respuesta y citas o referencias.
- Qué tipos de errores puede tener un sistema de este tipo: alucinaciones, recuperación irrelevante, evidencia insuficiente, citas débiles o respuestas demasiado seguras sin soporte.
- Cómo evaluar, al menos de forma básica, si un sistema mejora al incorporar recuperación: comparación cualitativa y/o cuantitativa entre una respuesta sin recuperación y otra con recuperación.
- Qué implicaciones éticas y profesionales tiene responder sin evidencia en dominios sensibles o académicos.

---

## 4. Qué NO se espera en este tema

- No deben entrenar un LLM desde cero ni desarrollar un sistema comercial a gran escala.
- No se espera una arquitectura distribuida, autenticación de usuarios, despliegue web profesional ni interfaces complejas.
- No necesitan usar un corpus masivo; pueden trabajar con un corpus pequeño o mediano, siempre que esté bien documentado y sea suficiente para demostrar el concepto.
- No se espera evaluación avanzada con métricas de investigación de posgrado; basta una evaluación básica pero seria, clara y reproducible.
- No deben usar fuentes privadas, confidenciales o con problemas evidentes de licencia. El corpus debe poder justificarse académicamente.

---

## 5. Preguntas orientadoras de investigación

- ¿En qué condiciones un sistema RAG reduce alucinaciones respecto a un sistema que responde sin recuperación explícita?
- ¿Qué decisiones de diseño del pipeline (chunking, número de documentos recuperados, criterio de selección, formato de cita) afectan más la calidad de la respuesta?
- ¿Qué tipo de errores siguen existiendo incluso cuando se agrega búsqueda y evidencia?
- ¿Qué significa realmente "responder con evidencia" y cómo se puede mostrar eso de forma comprensible para el usuario?

---

## 6. Entregables integrados por fase

### PP1 — Avance inicial

- Definir claramente el dominio y el corpus de trabajo. Debe quedar claro qué documentos utilizarán, por qué fueron seleccionados y cuál es el tipo de preguntas que esperan responder.
- Diseñar y documentar el pipeline mínimo del sistema: fuente(s) de información, preprocesamiento básico, mecanismo de búsqueda o recuperación, y forma esperada de respuesta.
- Implementar una primera versión funcional que permita al menos: cargar o indexar el corpus, recibir una consulta y devolver documentos/fragmentos recuperados relevantes.
- Entregar evidencia preliminar: al menos 3 consultas de prueba, con sus resultados recuperados, y una breve explicación de qué funciona y qué todavía falta.

### PP2 — Avance de consolidación

- Ampliar el prototipo para generar una respuesta final apoyada en los documentos recuperados, con una forma visible de referencia o cita (por ejemplo, lista de fuentes, fragmentos citados o marcadores simples).
- Comparar al menos dos configuraciones o escenarios del sistema. Ejemplos válidos: con y sin recuperación, con distinto tamaño de chunk, con distinto número de documentos recuperados, o con distinta estrategia de selección.
- Mostrar con evidencia básica si la recuperación mejora la calidad, pertinencia o verificabilidad de las respuestas.
- Entregar un MVP académico reproducible: notebook o repositorio con instrucciones claras, código, corpus o enlaces al corpus, consultas de prueba y evidencia de resultados.

### TI final — Reporte técnico y presentación

- Entregar un reporte técnico breve que explique el problema, el contexto, el marco teórico de RAG, el diseño del pipeline, las decisiones tomadas, la evaluación realizada, los resultados y las limitaciones.
- Integrar los avances de PP1 y PP2 dentro del TI, de modo que el TI sea la explicación y análisis del trabajo desarrollado durante el semestre.
- Incluir una discusión sobre riesgos de alucinación, límites del sistema, calidad de las fuentes y consecuencias de responder sin soporte suficiente.

---

## 7. Criterios de aceptación (gates)

- El sistema debe contar con un corpus definido, consultable y documentado.
- Debe existir una separación clara entre la parte de recuperación y la parte de generación o formulación de respuesta.
- El sistema debe correr con instrucciones claras y producir resultados reproducibles en al menos un conjunto pequeño de consultas.
- La respuesta final debe incluir alguna forma visible de soporte o referencia a la evidencia usada.
- Debe existir evidencia de comparación entre al menos dos configuraciones o escenarios relevantes.
- El entregable final debe funcionar como simulación, prototipo funcional o MVP académico; no como idea solamente.

---

## 8. Evidencia mínima esperada

- Tabla comparativa con al menos 5 consultas de prueba y columnas como: consulta, documentos recuperados, respuesta generada, evidencia/cita mostrada, observación o error detectado.
- Al menos una figura o esquema del pipeline RAG implementado.
- Ejemplo claro de una respuesta mejorada por recuperación y, si es posible, al menos un ejemplo donde el sistema todavía falle o cite mal.
- Explicación breve de por qué una configuración fue preferible a otra.

---

## 9. Demo / Defensa en vivo

- Mostrar en vivo al menos 3 consultas y cómo el sistema recupera evidencia antes de responder.
- Explicar qué corpus se está usando y por qué fue escogido.
- Responder una modificación breve del docente, por ejemplo: cambiar una consulta, limitar el número de documentos recuperados o mostrar qué pasa si se elimina la recuperación.
- Defender por qué el sistema puede considerarse una mejora respecto a responder sin evidencia.
