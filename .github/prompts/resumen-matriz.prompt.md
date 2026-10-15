---
mode: 'agent'
agent: 'resumen-matriz'
description: 'Resumen por hoja y por categoría de la matriz técnica de un vendor, con las calificaciones del Banco tal cual (cualquier conjunto de hojas); ejecuta 18_resumen_matriz y redacta los resúmenes'
tools: ['codebase', 'search', 'editFiles', 'runCommands']
---
Resume la matriz técnica de ${input:vendor:todos (uno por uno) o un vendor} por hoja y por categoría, con las calificaciones del Banco tal como están.
Matriz: ${input:matriz:«automática» (matrices\*<vendor>*.xlsx, la más reciente; si no, vendors\<vendor>\docs\raw) o la ruta del Excel}.

Sigue .github/copilot-instructions.md y tu definición de agente: ejecuta con runCommands `.venv\Scripts\python scripts\18_resumen_matriz.py <vendor> [ruta]`,
lee solo vendors/<vendor>/informes/12_resumen_matriz.md y vendors/<vendor>/matriz/<hoja>.txt, y sustituye cada marcador
`<!-- resumen: hoja | categoría -->` y `<!-- resumen-hoja: hoja -->` por su párrafo. Sin recalificar, sin verificar contra documentos,
sin opinión. Al final ejecuta `.venv\Scripts\python scripts\19_resumen_matriz_pptx.py <vendor> --completo` por vendor y, con «todos», `--todos --completo` (vendors\RESUMEN_MATRIZ_TODOS.html y .pptx, con la lámina comparativa vendors × hojas). Nunca con --pdf: el PDF se hace después, aparte.
Reporta solo: rutas (.md, .html, .pptx), hojas con puntaje y nivel y categorías con fundamento.
