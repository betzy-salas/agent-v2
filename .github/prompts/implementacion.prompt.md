---
mode: 'agent'
agent: 'redactor-implementacion'
description: 'Analiza la propuesta de implementación de un vendor y escribe vendors/<vendor>/informes/7_implementacion_pros_contras.md con pros y contras'
tools: ['codebase', 'search', 'editFiles']
---
Analiza la implementación del vendor ${input:vendor:nombre de la carpeta en vendors/}.

Sigue .github/copilot-instructions.md y tu definición de agente. Lee primero vendors/${input:vendor}/NOMBRES.md y los
.toc.md de vendors/${input:vendor}/docs/txt/ para localizar las secciones de implementación; luego lee esas secciones
completas y los anexos de perfiles, roles y referencias. No necesitas verificaciones previas; si existen verif/T5.md,
T7.md o T8.md úsalas solo para cruzar contradicciones. Escribe vendors/${input:vendor}/informes/7_implementacion_pros_contras.md
con la estructura de tu definición (ficha de 15 filas, pros y contras con confianza, riesgos, responsabilidades del Banco,
señales de alerta y preguntas). Sin recomendación final. Al terminar responde solo con: ruta, enfoque y duración propuestos,
número de pros y contras por confianza, y las 3 señales de alerta principales.
