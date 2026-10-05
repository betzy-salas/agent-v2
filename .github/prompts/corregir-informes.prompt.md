---
mode: 'agent'
agent: 'redactor-ejecutivo'
description: 'Aplica a los informes de un vendor las correcciones de la revisión cruzada'
tools: ['codebase', 'search', 'editFiles']
---
Para el vendor ${input:vendor:nombre de la carpeta en vendors/}, aplica a ${input:informe:nombre del archivo en informes/, p.ej. 3_resumen_ejecutivo.md}
las correcciones que le afectan de vendors/${input:vendor}/informes/5_revision_cruzada.md. Parte del archivo actual,
cambia solo lo objetado, conserva todo lo demás y verifica cada cifra contra vendors/${input:vendor}/verif/. Al final del
informe añade una sección «Cambios aplicados» con cada corrección y su origen. Responde solo con la lista de cambios.
