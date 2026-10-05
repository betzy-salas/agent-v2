---
mode: 'agent'
agent: 'redactor-fortalezas-debilidades'
description: 'Escribe el informe de fortalezas y debilidades por dimensión de un vendor en vendors/<vendor>/informes/6_fortalezas_debilidades.md'
tools: ['codebase', 'search', 'editFiles']
---
Escribe el informe de fortalezas y debilidades por dimensión del vendor ${input:vendor:nombre de la carpeta en vendors/}.

Sigue .github/copilot-instructions.md y tu definición de agente. Fuentes exclusivas: vendors/${input:vendor}/verif/
(T1.md … T8.md y 00_consolidado.md). No abras docs/, matriz/, verif/parciales/ ni verif/anteriores/.
Las evaluaciones se escriben con la clasificación textual y el número, por ejemplo «Completamente Cubierto (4)».
Toda cita se copia tal como aparece en las verificaciones, con el nombre oficial del documento de NOMBRES.md.
Salida: vendors/${input:vendor}/informes/6_fortalezas_debilidades.md.
