---
mode: 'agent'
agent: 'redactor-ficha-t5'
description: 'Corrige una ficha T5 existente a partir de los errores que reporta scripts/11_validar_ficha.py (viñetas vacías, sin fuente, sin ítem o cortas)'
tools: ['codebase', 'search', 'editFiles', 'runCommands']
---
Mejora la ficha T5 del vendor ${input:vendor:nombre de la carpeta en vendors/} en ${input:base:presentacion_t5}/${input:vendor}/10_ficha_T5.md.

1. Ejecuta `.venv\Scripts\python scripts\11_validar_ficha.py ${input:vendor} --base ${input:base}` y lee la lista de errores.
2. Para cada viñeta marcada, reescríbela según tu definición (qué propone el vendor, qué pidió el Banco y qué observó el
   evaluador o la verificación, con ítem E<n>, fuente y confianza), releyendo el ítem en ${input:base}/${input:vendor}/9_semaforo_T5.md
   y, si existe, en vendors/${input:vendor}/verif/T5.md. Nunca «cumple con el criterio E<n>» ni frases cortadas.
3. Vuelve a ejecutar el validador y repite hasta que diga OK. No cambies puntajes, colores ni calificaciones.
Al terminar responde solo con: ruta, viñetas corregidas y el resultado final del validador.
