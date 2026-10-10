---
mode: 'agent'
agent: 'redactor-ficha-t5'
description: 'Escribe la ficha T5 de un vendor (fortalezas, debilidades, pendientes, contradicciones, resumen por categoría) en <base>/<vendor>/10_ficha_T5.md'
tools: ['codebase', 'search', 'editFiles']
---
Escribe la ficha T5 del vendor ${input:vendor:nombre de la carpeta en vendors/} en la carpeta base ${input:base:vendors o presentacion_t5}.

Sigue .github/copilot-instructions.md y tu definición de agente. Fuentes exclusivas: ${input:base}/${input:vendor}/9_semaforo_T5.md
(o vendors/${input:vendor}/informes/9_semaforo_T5.md), y si existen vendors/${input:vendor}/verif/T5.md y
vendors/${input:vendor}/informes/2_ejecutivo_T5.md. Salida: ${input:base}/${input:vendor}/10_ficha_T5.md con las secciones y el
formato exactos de tu definición. Escribe el archivo con la herramienta de edición. Sin ranking ni recalificación. Cada viñeta debe describir qué propone el vendor y qué observó el evaluador (nunca «cumple con el criterio E3»); al terminar corre `.venv\Scripts\python scripts\11_validar_ficha.py ${input:vendor} --base ${input:base}` y corrige hasta que diga OK.
