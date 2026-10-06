# Agente redactor-implementacion (en preparación)

Analiza la propuesta de implementación de un vendor leyendo directamente sus documentos y produce
`vendors/<vendor>/informes/7_implementacion_pros_contras.md`: ficha resumen, pros y contras con fuente y nivel de
confianza (ALTA / MEDIA / BAJA), riesgos de ejecución, responsabilidades del Banco, señales de alerta y preguntas al
vendor. No recomienda ni compara vendors. No requiere verificaciones T1–T8 previas: basta con haber corrido la ingesta.

Esta carpeta está fuera de `.github/` a propósito: el agente aún no forma parte del flujo oficial. Para probarlo:

```powershell
copy implementacion\redactor-implementacion.agent.md .github\agents\
copy implementacion\implementacion.prompt.md .github\prompts\
```
Recarga la ventana de VS Code y, en Copilot Chat (modo Agent): `/implementacion` → nombre del vendor.

Cuando se apruebe, los archivos pasan a `.github/` de forma definitiva y se añaden a `EJECUCION.md` y al README principal.
