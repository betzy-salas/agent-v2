---
mode: 'agent'
agent: 'evaluador-dimensiones'
description: 'Matrices nuevas (matrices\*.xlsx): evaluación por dimensión (hoja) y por vendor del resultado calificado por el Banco, con evaluación general y lectura comparada; sin recalificar'
tools: ['codebase', 'search', 'editFiles', 'runCommands']
---
Evalúa las matrices técnicas nuevas de ${input:vendor:todos (uno por uno) o un vendor}, que están en matrices\ (un Excel por vendor, con el vendor en el nombre del archivo).

Sigue .github/copilot-instructions.md y tu definición de agente: ejecuta con runCommands `.venv\Scripts\python scripts\20_evaluacion_dimensiones.py` (con `--vendor <nombre>` si es uno),
lee solo matrices\evaluacion\<vendor>\<hoja>.md y completa en matrices\evaluacion\<vendor>\EVALUACION_<vendor>.md cada `<!-- evaluacion: hoja -->` (cinco párrafos: en qué se apoya, parcial o condicionado, no cubierto, observaciones del evaluador, pendiente de aclarar) y `<!-- evaluacion-general -->`; al final, con más de un vendor, `<!-- lectura-comparada -->` en matrices\evaluacion\EVALUACION_DIMENSIONES.md. Sin recalificar, sin conteos en la prosa, sin ranking. Nada de PDF.
Reporta solo: vendors procesados, rutas y, por vendor, dimensiones con su nivel.
