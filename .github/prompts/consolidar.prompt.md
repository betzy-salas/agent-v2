---
mode: 'agent'
agent: 'verificador-t1-arquitectura'
description: 'Ejecuta el consolidador y muestra la tabla por hoja de un vendor'
tools: ['runCommands', 'codebase']
---
Ejecuta en el terminal `python scripts/03_consolidar.py ${input:vendor:nombre de la carpeta en vendors/}` y muestra
la tabla resultante de vendors/${input:vendor}/verif/00_consolidado.md. No modifiques ningún archivo de verif/.
