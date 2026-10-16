---
mode: 'agent'
agent: 'analista-plataforma'
description: 'Para cada vendor: modelos de despliegue y plataformas que soporta, cuál propone al Banco y cuál es la más fuerte en su documentación (con cita); escribe informes/13_plataforma_principal.md y vendors/COMPARATIVO_PLATAFORMA.md'
tools: ['codebase', 'search', 'editFiles']
---
Determina la plataforma de despliegue propuesta al Banco y la más fuerte en la documentación de ${input:vendors:«todos» o lista de vendors separados por coma}.

Sigue .github/copilot-instructions.md y tu definición de agente. Procesa los vendors uno por uno; mientras analizas uno,
lee solo vendors/<ese vendor>/. Para cada vendor lee su NOMBRES.md y sus .toc.md, busca todos los términos de despliegue,
nube y plataforma en TODOS sus documentos (propuesta, anexos, Excel y PPTX convertidos) y en matriz/T1..T8.txt, clasifica
cada pasaje (P propuesto al Banco / O opción / E en producción / C certificado o compatible / G genérico / X excluido) y
escribe vendors/<vendor>/informes/13_plataforma_principal.md con la respuesta corta, las tablas «Modelos de despliegue»,
«Plataformas declaradas», «Propuesta al Banco», «Peso documental» (y la plataforma más fuerte con su razonamiento citado),
«Coincidencia», el inventario de pasajes, lo excluido o no especificado, contradicciones y preguntas. Software requerido
(Kafka, PostgreSQL, Istio, Prometheus, Docker) no es plataforma. Al final escribe vendors/COMPARATIVO_PLATAFORMA.md
agregando solo lo ya escrito por vendor. Sin recomendación ni conocimiento general. Al terminar responde solo con: vendors
procesados, rutas, y por vendor una línea «propuesta al Banco / más fuerte / coinciden / contradicciones».
