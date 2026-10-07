---
mode: 'agent'
agent: 'comparador-t5'
description: 'Los 8 pros y 8 contras más importantes de la dimensión de desarrollo (T5) por vendor, a partir de sus informes ejecutivos de T5, en vendors/COMPARATIVO_T5.md'
tools: ['codebase', 'search', 'editFiles']
---
Compara la dimensión de desarrollo (T5) de ${input:vendors:«todos» o lista de vendors separados por coma}.

Sigue .github/copilot-instructions.md y tu definición de agente. Vendor por vendor, lee solo
vendors/<ese vendor>/informes/2_ejecutivo_T5.md (principal), verif/T5.md (códigos y notas) y verif/00_consolidado.md
(puntaje T5); matriz/T5.txt solo para el campo cat=; no abras docs/. Escribe vendors/COMPARATIVO_T5.md con la tabla resumen, 8 pros y 8 contras por
vendor elegidos con el criterio fijo (criticidad, diferencia de nota, confianza, alcance), la tabla por categoría de la matriz (campo cat= de matriz/T5.txt),
las diferencias transversales y las preguntas pendientes. Sin recomendación ni orden de vendors. Al terminar responde
solo con: vendors comparados, ruta, puntaje T5 por vendor y las 3 diferencias principales.
