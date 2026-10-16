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

## Paso 7f — Presentación de la hoja T5 (ranking, puntajes por categoría, fichas por vendor y comentarios)
Un solo agente lo hace todo, en una carpeta aparte para no mezclar con el expediente (`presentacion_t5/`): regenera la matriz T5
de cada vendor desde su Excel (`02_matriz_a_texto.py <vendor> --hoja T5`, ingesta corregida), verifica la hoja T5 contra los documentos del vendor si aún no existe `verif/T5.md` (los sustentos
de la presentación salen de esas evidencias) y la valida con 06, genera el semáforo
de cada vendor con el script 09 (puntaje ponderado por criticidad, igual al consolidado del Banco), redacta sus conclusiones,
escribe la ficha de cada vendor (fortalezas, debilidades, pendientes, contradicciones, resumen por categoría; usa `verif/T5.md`
y `2_ejecutivo_T5.md` si existen), arma el comparativo con el script 10, redacta los comentarios y genera las diapositivas
(ranking en portada, dos diapositivas por vendor, comentarios por categoría, resultado final y pendientes).
```
/presentacion-t5   (base: presentacion_t5 · vendors: todos · matriz: desde el Excel)
```
Si Copilot entrega fichas pobres («cumple con el criterio E3»), lanza `/ficha-t5 <vendor> presentacion_t5` vendor por vendor y
valida cada una con `.venv\Scripts\python scripts/11_validar_ficha.py <vendor> --base presentacion_t5`; luego `/presentacion-t5` reutiliza las fichas válidas. Para corregir una ficha ya escrita sin rehacerla: `/mejorar-ficha-t5 <vendor> presentacion_t5`.

Ruta manual, paso a paso, si se prefiere controlar cada etapa:
```
.venv\Scripts\python scripts\09_semaforo_t5.py <vendor> --matriz vendors\<vendor>\matriz\T5.txt --salida presentacion_t5\<vendor>   # por vendor
/semaforo-t5 <vendor>   (archivo: presentacion_t5/<vendor>/9_semaforo_T5.md)
/ficha-t5 <vendor> presentacion_t5
.venv\Scripts\python scripts\10_presentacion_t5.py --base presentacion_t5
/comparar-semaforo-t5 presentacion_t5
.venv\Scripts\python scripts\10_presentacion_t5.py --base presentacion_t5 --pdf
.venv\Scripts\python scripts\10_presentacion_t5.py --base presentacion_t5 --pdf --estilo coe   # PDF 16:9 con el diseño del deck corporativo (logo y foto: presentacion_t5\assets\logo.png y portada.jpg)
.venv\Scripts\python scripts\12_presentacion_t5_pptx.py --base presentacion_t5                 # PowerPoint con el mismo diseño (pip install python-pptx)
.venv\Scripts\python scripts\13_laminas_correo.py --base presentacion_t5                     # dos láminas PNG (16:9, 2560×1440) + PDF para adjuntar a un correo
.venv\Scripts\python scripts\14_laminas_correo_pptx.py --base presentacion_t5                # las mismas dos láminas en PowerPoint
.venv\Scripts\python scripts\15_lamina_despliegue.py --base presentacion_t5     # LAMINA_3_despliegue.png / .pdf / .pptx (resumen de modelos de despliegue y nubes)
.venv\Scripts\python scripts\17_imagenes_despliegue.py --base presentacion_t5   # HOJA_4_plataformas_por_modelo.png y DIAPOSITIVA_plataformas_por_modelo.png (cuadrícula como imagen; antes: 08 --pdf y 10 --pdf --estilo coe)

# Resumen de la matriz técnica por hoja y categoría, calificaciones tal cual (cualquier conjunto de hojas):
# Deja cada Excel en matrices\ con el nombre del vendor en el archivo (p. ej. matrices\tm.xlsx); el script lo encuentra solo.
.venv\Scripts\python scripts\18_resumen_matriz.py <vendor> [ruta\al\xlsx]   # → vendors\<vendor>\informes\12_resumen_matriz.md + matriz\<hoja>.txt; después /resumen-matriz (agente) redacta los párrafos
.venv\Scripts\python scripts\19_resumen_matriz_pptx.py --todos --completo   # → vendors\RESUMEN_MATRIZ_TODOS.pdf y .pptx (todos los vendors: comparativa vendors × hojas + cada vendor); con <vendor> en lugar de --todos: informes\RESUMEN_MATRIZ_<vendor>.pdf y .pptx (el agente /resumen-matriz lo ejecuta al final; a mano si solo cambiaste el diseño)
# Todo lo de despliegue de una vez (08, 10, 12, 17 y 15), sin redactar nada: prompt /generar-despliegue (agente generador-despliegue)
# Plataforma propuesta al Banco y plataforma más fuerte en la documentación de cada vendor (sin script; solo agente): prompt /plataforma vendors: todos (agente analista-plataforma)
#   → vendors\<vendor>\informes\13_plataforma_principal.md (respuesta corta, modelos, plataformas declaradas con nivel P/O/E/C/G/X, propuesta al Banco, peso documental, coincidencia, inventario de pasajes) y vendors\COMPARATIVO_PLATAFORMA.md
.venv\Scripts\python scripts\16_informe_bloques_impl.py --todos --pdf     # informes/11_bloques_impl.md/.pdf por vendor + vendors\INFORME_BLOQUES_IMPLEMENTACION.pdf (fortalezas, brechas y contradicciones por bloque EI/F/I)
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


## Matrices nuevas: evaluación por dimensión (flujo independiente)

1. Deja el Excel nuevo de cada vendor en `matrices\` con el vendor en el nombre (p. ej. `matrices\tm.xlsx`).
2. En Copilot: `/evaluar-dimensiones vendor: todos`. El agente ejecuta `scripts\20_evaluacion_dimensiones.py` y escribe las evaluaciones.
3. Resultado en `matrices\evaluacion\`: por vendor `EVALUACION_<vendor>.md` (evaluación por dimensión + general) y la lectura completa de cada hoja (`<hoja>.md`); consolidado `EVALUACION_DIMENSIONES.md`.
A mano, solo el cálculo: `.venv\Scripts\python scripts\20_evaluacion_dimensiones.py [--vendor tm]`.

## Regla actual: los agentes no generan PDF

El PDF es opcional (`--pdf`) en todos los scripts y los agentes no lo piden. El análisis produce Markdown, HTML y PowerPoint; los PDF y los PNG
se generan después, aparte, ejecutando el script correspondiente con `--pdf` (y 17 para los PNG) cuando el navegador sin ventana funcione.

## Si el PDF no se genera (el navegador «intenta abrirse» o falla)

Los PDF se producen con Edge o Chrome en modo sin ventana. Los scripts prueban cuatro modos (con perfil temporal y sin él) y, si ninguno
funciona, muestran el error real del navegador y dejan el HTML. Para diagnosticar, en PowerShell (ajusta la ruta del HTML):

    & "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless=new --disable-gpu --print-to-pdf="$env:TEMP\prueba.pdf" "file:///C:/ruta/al/archivo.html"
    Test-Path "$env:TEMP\prueba.pdf"

- Si devuelve True, el problema es el perfil o el lanzamiento desde Copilot: vuelve a ejecutar el script desde una terminal normal (no desde Copilot).
- Si la política corporativa impide Edge sin ventana, hay tres salidas: 1) `set RFP_SIN_PDF=1` y usar los HTML (Imprimir → Guardar como PDF, horizontal,
  gráficos de fondo activados); 2) usar las salidas PowerPoint, que no necesitan navegador: 12 (deck), 14 (láminas de correo), 15 (lámina 3), 19 (resumen de matriz);
  3) si Chrome o Edge están en otra ruta, `set RFP_PDF_NAVEGADOR=C:\ruta\al\msedge.exe`.
- Copia en el chat las líneas «No se pudo generar el PDF … Último intento: …» que imprime el script: dicen el código de salida y el error.
