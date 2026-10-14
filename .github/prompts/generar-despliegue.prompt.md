---
mode: 'agent'
agent: 'generador-despliegue'
description: 'Ejecuta los scripts 08, 10, 12, 17 y 15 para regenerar el informe de comparativos, el deck, el PowerPoint, los PNG de la cuadrícula «plataformas por modelo» y la lámina 3'
tools: ['codebase', 'search', 'runCommands']
---
Regenera las salidas de despliegue en la carpeta base ${input:base:presentacion_t5}. Salidas: ${input:salidas:todo (o lista entre informe, deck, pptx, imagenes, lamina)}.

Sigue .github/copilot-instructions.md y tu definición de agente: verifica los requisitos previos, ejecuta los scripts en orden con runCommands usando .venv\Scripts\python, comprueba que los archivos existen y reporta solo comandos, resultados, rutas y pendientes. No edites ningún archivo.
