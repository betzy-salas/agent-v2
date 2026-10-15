---
mode: 'agent'
agent: 'generador-despliegue'
description: 'Ejecuta los scripts 08, 10, 12 y 15 (HTML y PowerPoint, sin PDF) para regenerar el informe de comparativos, el deck, el PowerPoint y la lámina 3; con pdf: sí añade los PDF y los PNG (17)'
tools: ['codebase', 'search', 'runCommands']
---
Regenera las salidas de despliegue en la carpeta base ${input:base:presentacion_t5}. Salidas: ${input:salidas:todo (o lista entre informe, deck, pptx, lamina)}. PDF: ${input:pdf:no (por defecto; «sí» solo cuando el navegador sin ventana funcione)}.

Sigue .github/copilot-instructions.md y tu definición de agente: verifica los requisitos previos, ejecuta los scripts en orden con runCommands usando .venv\Scripts\python, comprueba que los archivos existen y reporta solo comandos, resultados, rutas y pendientes. No edites ningún archivo.
