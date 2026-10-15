---
mode: 'agent'
agent: 'evaluador-dimensiones'
description: 'Matrices nuevas (matrices\*.xlsx): evaluación en prosa por dimensión (hoja) y por vendor del resultado calificado por el Banco, basada en los sustentos del evaluador; sin recalificar, sin conteos'
tools: ['codebase', 'search', 'editFiles', 'runCommands']
---
Evalúa las matrices técnicas nuevas de ${input:vendor:todos (uno por uno) o un vendor}, que están en matrices\ (un Excel por vendor, con el vendor en el nombre del archivo).

Lee entera tu definición de agente (.github/agents/evaluador-dimensiones.agent.md) y .github/copilot-instructions.md antes de empezar. Pasos:

1. `.venv\Scripts\python scripts\20_evaluacion_dimensiones.py` (con `--vendor <nombre>` si es uno). Genera matrices\evaluacion\<vendor>\<hoja>.md (lectura completa: pregunta, respuesta del proveedor, calificación, sustento y otros comentarios del evaluador de cada ítem) y EVALUACION_<vendor>.md con un marcador por dimensión.
2. El deber ser: tomar la evaluación del Banco (calificaciones y comentarios del evaluador) y escribir las razones que la complementan. Por cada dimensión, lee ENTERA la lectura <hoja>.md y sustituye `<!-- evaluacion: hoja -->` por tres párrafos en prosa con estos títulos en negrita:
   - **Razones que sostienen el resultado.** Fortalezas concretas con su sustento: qué ofrece el proveedor y en qué se apoyó el evaluador para darlo por cubierto (cita corta entre comillas de su sustento cuando exista; si no dejó sustento, dilo). Ejemplo de forma: «Se evidencia robustez en el proceso de desarrollo: el proveedor describe CI/CD con revisión de código y pruebas automatizadas en cada commit, y el evaluador lo considera “respuesta sólida y alineada a buenas prácticas” (E3).»
   - **Razones que restan.** Qué pidió el Banco, qué respondió el proveedor y qué anotó el evaluador, citando sus palabras entre comillas (hasta 20 palabras) con el ítem, empezando por los Indispensables o Killer. Ejemplo: «Se detecta debilidad en el enmascaramiento de datos: el proveedor no provee herramientas nativas y el evaluador anota que “traslada la responsabilidad al banco si se requieren datos productivos” (E16).»
   - **Lo que el evaluador deja abierto.** Dudas, «por revisar», segundo evaluador, ítems bajos sin sustento y lo pendiente de aclarar con el proveedor.
3. Sustituye `<!-- evaluacion-general -->` por la evaluación general del vendor en prosa (8 a 14 frases), construida solo con lo anterior.
4. Ejecuta `.venv\Scripts\python scripts\20_evaluacion_dimensiones.py --validar --vendor <vendor>` y reescribe cada frase que señale hasta que imprima «Validación: sin hallazgos». No des por terminado un vendor sin ese resultado.
5. Con más de un vendor, al final sustituye `<!-- lectura-comparada -->` en matrices\evaluacion\EVALUACION_DIMENSIONES.md (una o dos frases factuales por dimensión, sin ranking).

PROHIBIDO en la prosa: cualquier conteo o puntaje («15 criterios en No cumple», «la mayoría obtuvo 4», «58,8», «Parcial porque…»), listas telegráficas del tipo «E16: sin segmentación; E20: sin arquitectura», códigos E<n> como sujeto de la frase (van al final, entre paréntesis), opiniones, recomendaciones, ranking, hechos que no estén en la lectura de la hoja y cualquier cambio de calificación. Nada de PDF. Fuentes: solo matrices\evaluacion\<vendor>\.
Reporta solo: vendors procesados, rutas, dimensiones con su nivel (de la tabla) y la salida literal del validador.
