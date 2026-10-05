---
mode: 'agent'
agent: 'revisor-cruzado'
description: 'Lista los 20 ítems con mayor diferencia entre evaluación del Banco y sugerida de un vendor'
tools: ['codebase', 'search', 'editFiles']
---
Para el vendor ${input:vendor:nombre de la carpeta en vendors/}, lee vendors/${input:vendor}/verif/T1.md … T8.md y lista
los 20 ítems con mayor diferencia entre «Evaluación Banco» y «Evaluación sugerida» (killers primero a igualdad de
diferencia). Para cada uno: hoja-N°, criticidad, evaluación del Banco → sugerida, veredicto, evidencia con el nombre oficial
del documento y página u hoja/fila, y la justificación. No modifiques ningún archivo.
