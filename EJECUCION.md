# Guion de ejecución por vendor (GitHub Copilot)

Sustituye `<vendor>` por un nombre corto en minúsculas sin espacios (ej. `acme`). Las líneas con `$` van en la
terminal con el entorno activado (`source .venv/bin/activate` en macOS/Linux; `.venv\Scripts\Activate.ps1` en Windows, o anteponer `.venv\Scripts\python` a cada comando); las demás se escriben en Copilot Chat en modo Agent (VS Code), invocando el prompt con `/nombre`; cada hoja en su propia conversación.

## Paso 0 — Crear el vendor y cargar documentos
```
$ python scripts/00_nuevo_vendor.py <vendor>
```
Copia a `vendors/<vendor>/docs/raw/` la propuesta técnica (PDF), la matriz de evaluación del Banco (xlsx con hojas
T1–T8 y columna VA) y todos los anexos (xlsx, pptx). Los nombres de archivo pueden ser cualesquiera.

## Paso 1 — Ingesta
```
$ python scripts/04_ingesta.py <vendor>
```
Comprueba en la salida que la matriz detectada es la correcta y que los ítems por hoja cuadran con el Excel.
Luego revisa dos archivos:
- `vendors/<vendor>/NOMBRES.md`: nombres oficiales con los que se citará cada documento. Acórtalos si quieres.
- `vendors/<vendor>/docs/txt/<propuesta>.toc.md`: confirma el desfase de páginas y corrige la tabla
  «Secciones por dimensión», que es solo sugerida.


## Paso 1b — Implementación (rúbrica corporativa + resumen), no requiere las verificaciones T1–T8
Si en `docs/raw` está la rúbrica del Banco (xlsx con «Criterios Estrat Implementación»), la ingesta genera
`matriz/IMPL.txt` (61 criterios: estrategia, fabricante, implementador, con escalas 0–5 y las respuestas del Anexo de
perfiles). Primero se puntúa y luego se redacta:
```
/verificar-implementacion
```
Escribe `vendors/<vendor>/verif/IMPL.md` (puntaje por criterio con el descriptor exacto de la escala, respaldo
Documentado / Solo declarado / No encontrado, evidencia con documento, página, sección y cita). Después, el resumen
ejecutivo, que usa IMPL.md como base si existe. Lee directamente los documentos del vendor y escribe
`vendors/<vendor>/informes/7_implementacion_pros_contras.md` (ficha, pros y contras con confianza, riesgos, lo que asume
el Banco, alertas y preguntas; sin recomendación).
```
/implementacion
```

## Paso 2 — Verificadores (uno por uno la primera vez)
```
/verificar-t1   (pide el vendor)
```
Lee `vendors/<vendor>/verif/T1.md`. Si está bien, sigue:
```
/verificar-t2
/verificar-t3
/verificar-t4
/verificar-t5
/verificar-t7
/verificar-t8
```
T6 (167 ítems) en tres conversaciones (una por bloque) y luego unir:
```
/verificar-t6-bloque   (vendor, bloque 1)
/verificar-t6-bloque   (vendor, bloque 2)
/verificar-t6-bloque   (vendor, bloque 3)
/unir-t6
```
Copilot no lanza varios agentes en paralelo desde un chat: abre una conversación por hoja.
Tras cada hoja, valida:
```
/validar            (o en terminal: python scripts/06_validar_verif.py <vendor> T<n>)
```

## Paso 3 — Consolidar
```
$ python scripts/03_consolidar.py <vendor>
```

## Paso 4 — Revisión manual
```
/top-diferencias
```
Abre el PDF en las páginas citadas. Donde no estés de acuerdo, edita la fila en `vendors/<vendor>/verif/T<n>.md`
y repite el Paso 3.

## Paso 5 — Informes
```
/informe-diagnostico
/resumen-ejecutivo
/pros-contras
/informe-ejecutivo-t5
/fortalezas-debilidades
```
Uno por conversación; todos leen solo `verif/` y el consolidado.

## Paso 6 — Revisión cruzada
```
/revision-cruzada
```
Corrige lo que reporte con `/corregir-informes` (vendor e informe) y repite `/revision-cruzada`.

## Paso 7 — Comparar vendors
```
$ python scripts/05_comparar.py
```
Genera `vendors/COMPARATIVO.md` con el puntaje del Banco y verificado de todos los vendors por hoja y total.

## Reglas que no cambian entre vendors
Están en `.github/copilot-instructions.md` y Copilot las lee solo: escala textual de la hoja «Metodo de Evaluacion», cuatro
veredictos, respuesta del proveedor sin sustento = Parcialmente Cubierto (1), toda cita con nombre oficial
de documento, filas ocultas del Excel sí cuentan.

## Paso 7b — Modelo de despliegue y nubes, comparativo entre vendors
Requiere solo la ingesta de los vendors a comparar. Escribe `vendors/<vendor>/informes/8_modelo_despliegue.md` por vendor
(SaaS / PaaS / privada / on-prem / híbrido, nubes, quién opera, región; cada fila con documento, página, sección, título y
cita literal) y `vendors/COMPARATIVO_DESPLIEGUE.md`.
```
/despliegue        → pide «todos» o la lista de vendors
```

## Paso 7c — Comparación de implementaciones entre vendors
Requiere que cada vendor tenga `verif/IMPL.md` e `informes/7_implementacion_pros_contras.md` (Paso 1b). Escribe
`vendors/COMPARATIVO_IMPLEMENTACION.md`: tabla resumen por vendor (% EI/F/I, enfoque, duración, implementador),
rúbrica criterio a criterio EI-01…EI-12, fortalezas y debilidades por vendor, diferencias transversales y preguntas.
Sin recomendación ni ranking. Toda fuente es un documento del vendor (nombre oficial + página u hoja/fila), copiada del
archivo del vendor; nunca el nombre de un archivo `.md`. Si el comparativo actual cita archivos `.md`, relanzar este paso.
```
/comparar-implementacion   → pide «todos» o la lista de vendors
```

## Paso 7d — Comparación de la dimensión de desarrollo (T5) entre vendors
Requiere que cada vendor tenga `informes/2_ejecutivo_T5.md` (Paso 5). Escribe `vendors/COMPARATIVO_T5.md`: tabla resumen
(T5 Banco → verificado, killer E76, herramientas sin evidencia), 8 pros y 8 contras por vendor con ítem, notas, confianza
y fuente, tabla por bloque temático, diferencias transversales y preguntas. Sin recomendación ni orden de vendors.
```
/comparar-t5   → pide «todos» o la lista de vendors
```

## Paso 7e — Semáforo de la hoja T5 por categoría (por vendor)
Un color por categoría de la hoja T5, sin recalificar: el puntaje de la categoría es la media de las calificaciones del
Banco (columna VA) de sus ítems sobre 4, en 0–100, y el color sigue los niveles oficiales (≥ 70 🟢 verde, 50–69 🟡 amarillo,
< 50 🔴 rojo). El script genera la tabla y el anexo de ítems; luego el agente escribe, por categoría, una conclusión en una frase y su sustento, y el resumen
ejecutivo, condensando pregunta, respuesta del proveedor y sustento del evaluador, sin añadir hechos. Solo requiere la ingesta (matriz/T5.txt).
```
.venv\Scripts\python scripts\09_semaforo_t5.py <vendor>
/semaforo-t5 <vendor>
```

## Paso 8 — Documento final de estrategias de implementación (HTML + PDF)
Requiere, por vendor, `informes/7_implementacion_pros_contras.md`; si además existe `verif/IMPL.md`, incluye la rúbrica
puntuada (barras por bloque, mapa de calor de los 12 criterios y anexo con los 61 criterios). Genera
`vendors/INFORME_IMPLEMENTACION.html` (autocontenido, se abre en cualquier navegador) y, con `--pdf`, el PDF usando Edge o
Chrome instalados. No añade texto: todo sale de los informes de los agentes. Sin ranking ni recomendación.
```
.venv\Scripts\python scripts\07_informe_implementacion.py --pdf   (Windows)  ·  .venv/bin/python scripts/07_informe_implementacion.py --pdf  (macOS/Linux)
```
Versiones: `--ejecutivo` genera `INFORME_IMPLEMENTACION_EJECUTIVO` (comparativo + una página por vendor, ~13 páginas);
`--vendor <v>` genera `INFORME_IMPLEMENTACION_<v>` (especificación vertical con los 61 criterios, ~11 páginas);
`--todo` genera el ejecutivo y una especificación por vendor. Sin opción, el documento completo de antes.
Otras opciones: lista de vendors (`… sunline acme`), `--salida ruta.html`. Si no encuentra Edge/Chrome, abre el HTML e imprime a PDF.

## Paso 9 — Informe PDF de los comparativos entre vendors
Reúne en un solo documento los tres comparativos que existan en `vendors/`: `COMPARATIVO_DESPLIEGUE.md` (Paso 7b),
`COMPARATIVO_IMPLEMENTACION.md` (Paso 7c) y `COMPARATIVO.md` (05_comparar). Genera `vendors/INFORME_COMPARATIVOS.html`
y, con `--pdf`, el PDF (apaisado). Las fuentes de la comparación transversal se toman de los documentos citados por cada
vendor. Sin ranking ni recomendación.
```
.venv\Scripts\python scripts\08_comparativos_pdf.py --pdf
```
