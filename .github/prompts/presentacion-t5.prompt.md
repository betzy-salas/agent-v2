---
mode: 'agent'
agent: 'presentador-t5'
description: 'Genera de principio a fin la presentación T5 (semáforos, fichas, comparativo con comentarios, ranking y PDF) en una carpeta base'
tools: ['codebase', 'search', 'editFiles', 'runCommands']
---
Produce la presentación T5 completa en la carpeta base ${input:base:presentacion_t5} para los vendors ${input:vendors:«todos» o lista separada por coma}.
Matriz T5 de cada vendor: ${input:matriz:vendors/<vendor>/matriz/T5.txt o la ruta de los archivos T5_<VENDOR>.txt}.

Sigue .github/copilot-instructions.md y tu definición de agente paso a paso: 09 por vendor, textos del semáforo, ficha por vendor,
comparativo con comentarios y PDF. Ejecuta los scripts con runCommands usando .venv\Scripts\python y escribe los textos en los
archivos con editFiles. Reporta al final ruta del PDF, páginas, puntaje y nivel por vendor en orden de ranking, y lo que faltó.
