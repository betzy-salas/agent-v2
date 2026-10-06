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


## Paso 1b — Propuesta de implementación (opcional, no requiere verificaciones)
Puede hacerse justo después de la ingesta. Lee directamente los documentos del vendor y escribe
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
