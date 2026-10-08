---
mode: 'agent'
agent: 'semaforo-t5'
description: 'Completa la conclusión y el sustento por categoría del semáforo T5 de un vendor en vendors/<vendor>/informes/9_semaforo_T5.md (antes: scripts/09_semaforo_t5.py <vendor>)'
tools: ['codebase', 'search', 'editFiles']
---
Completa la conclusión y el sustento de cada categoría del semáforo T5 del vendor ${input:vendor:nombre de la carpeta en vendors/}.

Sigue .github/copilot-instructions.md y tu definición de agente. Fuentes exclusivas: vendors/${input:vendor}/informes/9_semaforo_T5.md
(generado por scripts/09_semaforo_t5.py) y vendors/${input:vendor}/matriz/T5.txt. No abras docs/ ni verif/. No cambies ni
cuestiones ninguna calificación ni color: solo condensa pregunta, respuesta del proveedor y sustento del evaluador, nombrando el
ítem E<n> en cada frase. Sustituye únicamente los marcadores <!-- conclusion: … -->, <!-- lectura: … --> y <!-- resumen -->.
