---
mode: 'agent'
agent: 'revisor-cruzado'
description: 'Valida formato, conteos y citas de las verificaciones de un vendor con scripts/06_validar_verif.py'
tools: ['runCommands', 'codebase']
---
Ejecuta en el terminal `python scripts/06_validar_verif.py ${input:vendor:nombre de la carpeta en vendors/}` y muestra
el resultado. Si alguna hoja tiene errores, explica cada uno en una línea y qué archivo y filas hay que corregir.
No modifiques ningún archivo de verif/.
