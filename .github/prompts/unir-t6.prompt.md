---
mode: 'agent'
agent: 'verificador-t6-seguridad'
description: 'Une los tres bloques parciales de T6 en vendors/<vendor>/verif/T6.md'
tools: ['codebase', 'search', 'editFiles']
---
Une los tres parciales de T6 del vendor ${input:vendor:nombre de la carpeta en vendors/}:
vendors/${input:vendor}/verif/parciales/T6_bloque1.md, T6_bloque2.md y T6_bloque3.md → vendors/${input:vendor}/verif/T6.md.

Reglas: una sola cabecera (verificador, 167 ítems, nota sobre que se hizo en tres bloques, recuento total de
veredictos y de ítems con calificación distinta); la tabla principal completa bajo «## Tabla de verificación» con las
167 filas en orden E1…E167; las secciones (a), (b), (c) y (e) con un subapartado por bloque; la sección (d) como
una sola tabla que une las filas de los tres bloques. No cambies el contenido de ninguna fila. Comprueba al final
que hay exactamente 167 filas y ningún ID repetido. No ejecutes verificación nueva.
