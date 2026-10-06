---
mode: 'agent'
agent: 'verificador-implementacion'
description: 'Puntúa la rúbrica corporativa de implementación de un vendor (estrategia, fabricante, implementador; 0–5) contra sus documentos y escribe vendors/<vendor>/verif/IMPL.md'
tools: ['codebase', 'search', 'editFiles', 'runCommands']
---
Verifica la implementación del vendor ${input:vendor:nombre de la carpeta en vendors/}.

Sigue .github/copilot-instructions.md y tu definición de agente. Lee vendors/${input:vendor}/NOMBRES.md y
vendors/${input:vendor}/matriz/IMPL.txt (si no existe, ejecuta `python scripts/02b_rubrica_implementacion.py ${input:vendor}`
con el intérprete del entorno). Puntúa los 61 criterios (EI-01…12, F-01…24, I-01…25 por implementador) con el descriptor
exacto de cada escala, respaldo Documentado / Solo declarado / No encontrado, y evidencia con documento, página, sección y
cita literal. Escribe vendors/${input:vendor}/verif/IMPL.md con las tablas EI, F e I, el resumen por bloque, hallazgos,
contradicciones, señales de alerta y preguntas. Sin recomendación. Al terminar responde solo con: ruta, criterios por bloque,
porcentaje por bloque, nº «Solo declarado» y «No encontrado», y las 3 contradicciones principales.
