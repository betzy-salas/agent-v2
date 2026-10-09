---
mode: 'agent'
agent: 'presentador-t5'
description: 'Genera de principio a fin la presentación T5 (semáforos, fichas, comparativo con comentarios, ranking y PDF) en una carpeta base'
tools: ['codebase', 'search', 'editFiles', 'runCommands']
---
Produce la presentación T5 completa en la carpeta base ${input:base:presentacion_t5} para los vendors ${input:vendors:«todos» o lista separada por coma}.
Matriz: ${input:matriz:«desde el Excel» (regenera vendors/<vendor>/matriz/T5.txt con 02_matriz_a_texto --hoja T5) o la ruta de archivos T5 ya generados}.

Sigue .github/copilot-instructions.md y tu definición de agente paso a paso: ingesta de la hoja T5 por vendor (02 --hoja T5), verificación documental de T5 si falta (como verificador-t5-desarrollo, con 06_validar_verif), 09 por vendor, textos del semáforo, ficha por vendor,
comparativo con comentarios y PDF. Ejecuta los scripts con runCommands usando .venv\Scripts\python y escribe los textos en los
archivos con editFiles. Reporta al final ruta del PDF, páginas, puntaje y nivel por vendor en orden de ranking, y lo que faltó.
