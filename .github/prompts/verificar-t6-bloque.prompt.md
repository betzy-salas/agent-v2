---
mode: 'agent'
agent: 'verificador-t6-seguridad'
description: 'Verifica un bloque de la hoja T6 (E1–E56, E57–E112 o E113–E167) de un vendor y escribe vendors/<vendor>/verif/parciales/T6_bloque<n>.md'
tools: ['codebase', 'search', 'editFiles', 'runCommands']
---
Verifica T6 del vendor ${input:vendor:nombre de la carpeta en vendors/}, SOLO el bloque ${input:bloque:1, 2 o 3}:
bloque 1 = ítems E1–E56, bloque 2 = E57–E112, bloque 3 = E113–E167.

Sigue .github/copilot-instructions.md y tu definición de agente. Lee primero vendors/${input:vendor}/NOMBRES.md.
Procesa todos los ítems del bloque desde vendors/${input:vendor}/matriz/T6.txt y escribe
vendors/${input:vendor}/verif/parciales/T6_bloque${input:bloque}.md con: título «# Verificación T6 — Bloque ${input:bloque}»,
cabecera con documentos consultados, la tabla bajo «## Tabla de verificación» (7 columnas), y las secciones
«## (a)», «## (b)», «## (c)», «## (d) Controles delegados al banco», «## (e) Respuestas desplazadas detectadas»,
todas referidas solo a tu bloque. No uses «|» dentro de las celdas.
Al terminar responde solo con: ruta, ítems procesados, ítems con calificación distinta, controles delegados y las 3
contradicciones principales del bloque.
