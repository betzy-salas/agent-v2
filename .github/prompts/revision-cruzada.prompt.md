---
mode: 'agent'
agent: 'revisor-cruzado'
description: 'Revisa los informes de un vendor buscando contradicciones entre ellos y con el consolidado'
tools: ['codebase', 'search', 'editFiles']
---
Revisa los informes del vendor ${input:vendor:nombre de la carpeta en vendors/}: vendors/${input:vendor}/informes/
1_diagnostico_evaluacion.md, 2_ejecutivo_T5.md, 3_resumen_ejecutivo.md, 4_pros_contras.md y 6_fortalezas_debilidades.md,
más vendors/${input:vendor}/verif/T5.md y 00_consolidado.md. Escribe vendors/${input:vendor}/informes/5_revision_cruzada.md
con: cifras que no coinciden, afirmaciones contradictorias, hallazgos omitidos, afirmaciones sin fuente, citas sin nombre
de documento, y la lista de correcciones por archivo y sección. No corrijas los informes.
