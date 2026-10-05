---
mode: 'agent'
agent: 'verificador-t5-desarrollo'
description: 'Verifica la hoja T5 de un vendor contra sus documentos y escribe vendors/<vendor>/verif/T5.md'
tools: ['codebase', 'search', 'editFiles', 'runCommands']
---
Verifica T5 del vendor ${input:vendor:nombre de la carpeta en vendors/}.

Sigue .github/copilot-instructions.md y tu definición de agente. Lee primero vendors/${input:vendor}/NOMBRES.md.
Procesa TODOS los ítems de vendors/${input:vendor}/matriz/T5.txt sin omitir ninguno y escribe
vendors/${input:vendor}/verif/T5.md con la tabla principal bajo «## Tabla de verificación» y las secciones (a), (b), (c) y las de tu definición.
No uses el carácter «|» dentro de las celdas. Antes de terminar, comprueba que toda cita de página, hoja o fila lleva
delante el nombre oficial del documento de NOMBRES.md y que el número de filas coincide con el de ítems de la matriz.
Al terminar responde solo con: ruta, ítems procesados, ítems con calificación distinta (cuántos bajan y suben) y las 5
contradicciones principales.
