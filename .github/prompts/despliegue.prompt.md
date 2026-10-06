---
mode: 'agent'
agent: 'analista-despliegue'
description: 'Determina para cada vendor qué modelos de despliegue (SaaS, PaaS, privada, on-prem) y qué nubes ofrece, con fuente verificable, y escribe vendors/COMPARATIVO_DESPLIEGUE.md'
tools: ['codebase', 'search', 'editFiles']
---
Analiza el modelo de despliegue y las nubes ofrecidas por ${input:vendors:«todos» o lista de vendors separados por coma}.

Sigue .github/copilot-instructions.md y tu definición de agente. Procesa los vendors uno por uno; mientras analizas uno,
lee solo vendors/<ese vendor>/. Para cada vendor lee su NOMBRES.md y sus .toc.md, busca los términos de despliegue y nube
en TODOS sus documentos, y escribe vendors/<vendor>/informes/8_modelo_despliegue.md con las tablas «Modelos» y «Nubes»,
cada fila con documento, página, sección y título del índice, cita literal y confianza. Al final escribe
vendors/COMPARATIVO_DESPLIEGUE.md agregando solo lo ya escrito por vendor. Sin recomendación. Al terminar responde solo
con: vendors procesados, rutas, y por vendor una línea «modelos / nubes para el Banco / contradicciones».
