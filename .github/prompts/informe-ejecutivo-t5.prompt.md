---
mode: 'agent'
agent: 'redactor-ejecutivo-t5'
description: 'Escribe el informe ejecutivo de T5 con fortalezas y debilidades técnicas de un vendor en vendors/<vendor>/informes/2_ejecutivo_T5.md'
tools: ['codebase', 'search', 'editFiles']
---
Escribe el informe ejecutivo de T5 con fortalezas y debilidades técnicas del vendor ${input:vendor:nombre de la carpeta en vendors/}.

Sigue .github/copilot-instructions.md y tu definición de agente. Fuentes exclusivas: vendors/${input:vendor}/verif/
(T1.md … T8.md y 00_consolidado.md). No abras docs/, verif/parciales/ ni verif/anteriores/; matriz/ solo para la sección de capacidades declaradas sin respaldo.
Las evaluaciones se escriben con la clasificación textual y el número, por ejemplo «Completamente Cubierto (4)».
Toda cita se copia tal como aparece en las verificaciones, con el nombre oficial del documento de NOMBRES.md.
Salida: vendors/${input:vendor}/informes/2_ejecutivo_T5.md.
