---
mode: 'agent'
agent: 'resumen-matriz'
description: 'Resumen por hoja y por categoría de la matriz técnica de un vendor, con las calificaciones del Banco tal cual (cualquier conjunto de hojas); ejecuta 18_resumen_matriz y redacta los resúmenes'
tools: ['codebase', 'search', 'editFiles', 'runCommands']
---
Resume la matriz técnica del vendor ${input:vendor} por hoja y por categoría, con las calificaciones del Banco tal como están.
Matriz: ${input:matriz:«automática» (busca el xlsx en vendors/<vendor>/docs/raw o vendors/<vendor>/) o la ruta del Excel nuevo}.

Sigue .github/copilot-instructions.md y tu definición de agente: ejecuta con runCommands `.venv\Scripts\python scripts\18_resumen_matriz.py <vendor> [ruta]`,
lee solo vendors/<vendor>/informes/12_resumen_matriz.md y vendors/<vendor>/matriz/<hoja>.txt, y sustituye cada marcador
`<!-- resumen: hoja | categoría -->` y `<!-- resumen-hoja: hoja -->` por su párrafo. Sin recalificar, sin verificar contra documentos,
sin opinión. Reporta solo: ruta, hojas con puntaje y nivel, categorías resumidas y reparto por nivel.
