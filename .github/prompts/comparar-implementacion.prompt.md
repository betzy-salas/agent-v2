---
mode: 'agent'
agent: 'comparador-implementacion'
description: 'Resumen ejecutivo comparativo de las implementaciones de todos los vendors (fortalezas y debilidades por vendor, rúbrica criterio a criterio) en vendors/COMPARATIVO_IMPLEMENTACION.md'
tools: ['codebase', 'search', 'editFiles']
---
Compara las propuestas de implementación de ${input:vendors:«todos» o lista de vendors separados por coma}.

Sigue .github/copilot-instructions.md y tu definición de agente. Vendor por vendor, lee solo vendors/<ese vendor>/verif/IMPL.md,
informes/7_implementacion_pros_contras.md e informes/8_modelo_despliegue.md si existe; no abras docs/ ni matriz/. Escribe
vendors/COMPARATIVO_IMPLEMENTACION.md con la tabla resumen por vendor, la tabla criterio a criterio EI-01…EI-12, una sección
de fortalezas y debilidades por vendor, la comparación transversal y las preguntas pendientes. Sin recomendación ni ranking.
Al terminar responde solo con: vendors comparados, ruta, porcentajes EI/F/I por vendor y las 3 diferencias principales.
