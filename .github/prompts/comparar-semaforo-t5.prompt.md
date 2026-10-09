---
mode: 'agent'
agent: 'comparador-semaforo-t5'
description: 'Redacta los comentarios (por categoría, por vendor y final) del comparativo del semáforo T5 generado por scripts/10_presentacion_t5.py'
tools: ['codebase', 'search', 'editFiles']
---
Redacta los comentarios del comparativo del semáforo T5 en la carpeta base ${input:base:carpeta base (vendors o presentacion_t5)}.

Sigue .github/copilot-instructions.md y tu definición de agente. Fuentes exclusivas: ${input:base}/COMPARATIVO_SEMAFORO_T5.md
(generado por scripts/10_presentacion_t5.py --base ${input:base}) y el 9_semaforo_T5.md de cada vendor bajo esa carpeta, leídos uno
por uno. Sustituye únicamente los marcadores <!-- comentario-categoria: … -->, <!-- comentario-vendor: … --> y <!-- comentario-final -->
con la herramienta de edición de archivos. Sin ranking ni recomendación; no cambies ningún puntaje.
