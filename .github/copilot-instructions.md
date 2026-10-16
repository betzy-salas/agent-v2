<!-- Generado desde CLAUDE.md del proyecto rfp-core-verificacion. Copilot lee este archivo automáticamente
     en Copilot Chat, en el agente de VS Code y en el Copilot coding agent. Mantenerlo sincronizado con CLAUDE.md. -->

# Verificación técnica RFP core bancario — reglas comunes

## Contexto
Proceso de selección de core bancario para un banco regulado. Para CADA vendor se verifica
la matriz técnica diligenciada por el proveedor y calificada por evaluadores del Banco contra la documentación
entregada por ese proveedor. Hay varios vendors; cada uno vive en su carpeta y se evalúa con las mismas
reglas y los mismos agentes.

## Estructura multi-vendor
```
vendors/<vendor>/docs/raw/      ← documentos originales del vendor (solo lectura)
vendors/<vendor>/docs/txt/      ← texto con marcadores + <doc>.toc.md
vendors/<vendor>/matriz/T1..T8.txt
vendors/<vendor>/verif/T1..T8.md, 00_consolidado.md
vendors/<vendor>/informes/
vendors/<vendor>/INVENTARIO.md
vendors/<vendor>/NOMBRES.md     ← nombres oficiales de documento para citar (generado; editable)
vendors/COMPARATIVO.md          ← lo genera scripts/05_comparar.py
```
**Todo agente o prompt recibe el vendor como argumento** («verifica T3 del vendor acme») y trabaja solo dentro de
`vendors/<vendor>/`. Nunca lee ni escribe en la carpeta de otro vendor. Si no se indica el vendor y hay más
de uno en `vendors/`, el agente se detiene y lo pregunta.

## Fuentes
- Matriz por hoja: vendors/<vendor>/matriz/T1.txt … T8.txt. Cada ítem:
  `[N°] cat=<categoría> crit=<criticidad> va=<0-4> eval=<clasificación textual> evaluador=<nombre>` / Q / PROVEEDOR / SUSTENTO.
  - **Calif Banco = `va`** (columna VA del Excel, número 0–4). Es la que va en la tabla y la que compara el consolidado.
  - `eval` es la clasificación textual que escribió el evaluador. Si no coincide con `va` según la escala
    (p. ej. eval=«Cubierto: Modificación Menor» y va=4), repórtalo en (a) como «incoherencia Eval/VA en la matriz».
  - `eval=Seleccionar` o `va=None` = ítem sin calificar por el Banco: escribe «—» en Calif Banco y dilo en la cabecera.
  - `evaluador` es el nombre del evaluador del Banco; no es una calificación.
- Documentos en texto: vendors/<vendor>/docs/txt/*.txt. Marcadores:
  - PDF: "===== PAGE n =====" (n = página del PDF; el desfase con la página impresa está en el .toc.md).
  - Excel: "===== SHEET <hoja> =====" y cada fila "f.<n>: celda | celda | …".
  - PPTX: "===== SLIDE n =====".
- Mapa de secciones de cada documento: vendors/<vendor>/docs/txt/*.toc.md. Léelo antes de buscar; trae el
  desfase de páginas y una asignación sugerida de secciones a T1–T8.
- Inventario de documentos: vendors/<vendor>/INVENTARIO.md.
- La matriz de evaluación del Banco (xlsx) no está en docs/txt: es la matriz misma y ya está en matriz/T*.txt.

## Forma de citar
**Toda evidencia nombra el documento.** Nunca se escribe una página, hoja o fila suelta («p.21», «f.101»,
«T6 f.101»): siempre va precedida del nombre oficial del documento, incluso si es la segunda cita de la
misma celda o el mismo documento que la cita anterior.

Nombres oficiales: están en **vendors/<vendor>/NOMBRES.md** (columna «Nombre oficial»), generado por los scripts
de ingesta a partir de los archivos de docs/raw y editable a mano. Léelo al empezar y usa exactamente ese texto.
Unidad de cita según el tipo: PDF → «p.<n>» (página PDF del marcador); Excel → «hoja <nombre>, f.<fila>»;
PPTX → «slide <n>». Para referirte a la celda de la matriz: «Matriz del Banco, hoja T<n>, ítem E<m>» (nunca como evidencia).

Ejemplos correctos (con nombres oficiales de ejemplo):
- «<Nombre oficial de la propuesta> p.70: “framework moderno de microservicios cloud-native…”»
- «<Nombre oficial del anexo>, hoja T6, f.101: “diseñado principalmente para single-tenant”»
- «<Nombre oficial del PPTX>, slide 2»

Ejemplos incorrectos (no usar): «Propuesta p.70» · «p.21» · «Anexo 5 f.5» · «T2 f.31» · «ver diagrama».

En Excel la hoja es obligatoria: la misma fila existe en varias hojas. En la cabecera de verif/T<n>.md
lista los documentos consultados con su nombre oficial y su archivo. Busca en TODOS los
vendors/<vendor>/docs/txt/*.txt, no solo en la propuesta.

## Orden de búsqueda
1. Propuesta técnica principal. 2. Anexos del proveedor (el resto de docs/txt). 3. Respuestas v2 dentro de la matriz, si las hay.

## Escala de calificación
Es la de la hoja «Metodo de Evaluacion» de la matriz de evaluación del Banco (xlsx, f.5–f.9), copiada textualmente. Toda calificación
sugerida usa exactamente estos valores y estas definiciones; no se interpolan ni se inventan niveles.
La hoja «Hoja4» del mismo Excel (valores 0, 2, 4, 6, 8) NO se usa: ignórala.

| Calif | Clasificación | Descripción (textual de la hoja) |
|---|---|---|
| 0 | No Cubierto | No se cubre el requerimiento. |
| 1 | Parcialmente Cubierto | Requerimiento cubierto, pero no en la forma en la que se solicita. (No hay posibilidad de modificar la solucion) |
| 2 | Cubierto: Modificación Mayor | Para cubrir el requerimiento se necesita una modificación en el core o estructura del Sistema en el laboratorio. |
| 3 | Cubierto: Modificación Menor | Para cubrir el requerimiento se necesita una modificación en la aplicación durante el desarrollo del Proyecto. |
| 4 | Completamente Cubierto | El requerimiento se encuentra cubierto sin realizar modificaciones a la solución. |

En la columna «Calif sugerida» se escribe el número (0–4) o N/A. Para elegir entre 2 y 3 fíjate en la definición:
2 es modificación del core o de la estructura del sistema (laboratorio del proveedor); 3 es modificación de la
aplicación durante el proyecto. Si el documento no permite distinguirlo, usa 2 y dilo en la justificación.

## Niveles de cumplimiento por dimensión y total
Se calculan sobre el puntaje 0–100 del consolidado (media de calificaciones 0–4 sobre 4, por hoja y ponderado):
**Cumple plenamente ≥ 85 · Cumple 70–84 · Parcial 50–69 · No cumple < 50.** Es la única escala de niveles que
usan los informes; cualquier informe que mencione un nivel cita esta sección como fuente.

## Veredictos
- CONFIRMA: la evidencia respalda la respuesta de la matriz y la calificación del Banco es razonable.
- COMPLETA: hay evidencia que la celda no dio y que justificaría subir la calificación.
- CONTRADICE: la evidencia dice algo distinto a la celda de la matriz.
- SIN EVIDENCIA: ningún documento respalda lo que dice la celda. La calificación sugerida es como máximo 1 (ver «Tratamiento de la respuesta del proveedor»).

## Tratamiento de la respuesta del proveedor
La columna PROVEEDOR de la matriz es una declaración, no una evidencia. Siempre hay que buscar sustento
en docs/txt/ (propuesta, anexos, Key Roles), diga lo que diga la celda. Tres casos:

1. **El proveedor afirma cumplir y no hay sustento en ningún documento** → veredicto SIN EVIDENCIA,
   Calif sugerida = 1 (Parcialmente Cubierto). Justificación obligatoria con esta idea:
   «Solo se encontró la respuesta del proveedor en la matriz; ningún documento evidencia que la respuesta
   corresponda a la pregunta ni que indique, explícita o medianamente explícitamente, que lo cumple.»
   Si el Banco calificó 2, 3 o 4, el ítem va en la sección (a) de calificación distinta.

2. **El proveedor responde que NO lo tiene o no lo cubre** → igualmente buscar en propuesta y anexos.
   - Si un documento sí muestra la capacidad → veredicto CONTRADICE, Calif sugerida = 1 (Parcialmente
     Cubierto). Justificación: «El proveedor declara no contar con ello, pero en <documento, página/hoja>
     se encontró <qué>.» Es un hallazgo que debe listarse en la sección (c).
   - Si ningún documento lo muestra → veredicto CONFIRMA (la celda y los documentos coinciden en que no
     está), Calif sugerida = 0, y la justificación explica el motivo concreto por el que no está cubierto
     (qué se pidió y qué falta).

3. **El proveedor afirma cumplir y hay sustento** → CONFIRMA o COMPLETA según el caso, con la cita.
   Si el sustento es parcial (cubre parte de la pregunta, o es genérico, o depende de condiciones), la
   calificación sugerida refleja esa parcialidad y la justificación dice qué parte queda sin respaldo.

En todos los casos de 0 o 1 la justificación dice POR QUÉ no está cubierto o solo parcialmente: qué pide
la pregunta, qué dice la celda y qué se encontró (o no) en los documentos. Nunca «sin evidencia» a secas.

## Aislamiento por vendor y prohibición de inventar
Cada vendor es un expediente independiente. Para una tarea sobre `<vendor>`:
- **Únicas fuentes admitidas:** `vendors/<vendor>/matriz/`, `vendors/<vendor>/docs/txt/`, `vendors/<vendor>/NOMBRES.md`,
  `vendors/<vendor>/INVENTARIO.md` y, para los redactores, `vendors/<vendor>/verif/`. Nada más.
- **Prohibido** leer, citar o «recordar» cualquier otra carpeta de `vendors/`, aunque trate el mismo tema o la misma
  pregunta E<n>. Lo verificado para un vendor no sirve de evidencia ni de referencia para otro.
- **Prohibido** usar conocimiento general sobre el producto, la empresa o la industria (lo que «suele» tener un core
  bancario, lo que el proveedor publica en su web, lo que se sabe de versiones o certificaciones). Si no está en los
  documentos de ese vendor, no existe para la verificación.
- **Prohibido** completar, suponer o inferir: una capacidad que no aparece textualmente es SIN EVIDENCIA; una página,
  fila o cifra que no se pudo leer es NO ENCONTRADO. Nunca se redondea, estima ni interpola.
- **Prohibido** consultar internet o archivos fuera del proyecto.
- Si un documento de `docs/raw` no se convirtió a `docs/txt`, no se cita: se reporta en la cabecera como no verificable.
- **Autocomprobación obligatoria** antes de entregar: toda ruta que leíste empieza por `vendors/<vendor>/`; toda cita
  nombra un documento que está en `vendors/<vendor>/NOMBRES.md`; ninguna afirmación carece de cita o de la marca
  SIN EVIDENCIA / NO ENCONTRADO. Si algo no cumple, corrígelo antes de escribir el archivo.

**Excepción comparativa.** Los agentes `analista-despliegue`, `analista-plataforma`, `comparador-implementacion`, `comparador-t5`, `comparador-semaforo-t5` y `presentador-t5` (y cualquier otro declarado
explícitamente como comparativo) lee varios vendors. Lo hace uno por uno: mientras analiza un vendor, solo lee `vendors/<ese vendor>/`; nunca
usa lo concluido de un vendor para inferir o completar a otro; la tabla comparativa final solo agrega lo ya escrito y
citado en el archivo de cada vendor. Un agente no comparativo sigue limitado a un solo vendor.

## Reglas inviolables
- Toda afirmación cita documento y página del PDF (u hoja/fila). Si no hay evidencia, escribe SIN EVIDENCIA. Nunca inventes páginas, cifras, nombres de producto ni capacidades.
- "Depende de la arquitectura", "se definirá en el contrato" o "puede integrarse" es parcial (1), no completo.
- Un ítem calificado 0 por "no relevante" se marca N/A en la columna Calif sugerida.
- Señala siempre: respuestas copy-paste desplazadas (la celda responde la pregunta anterior), material
  reciclado de otros clientes (nombres de países, bancos o sistemas ajenos), marcadores [verificar]/[TBD],
  sustentos del evaluador cuyas páginas no corresponden al contenido, preguntas repetidas con calificaciones distintas,
  y cifras incompatibles entre secciones del mismo documento.
- Tono neutral de comité. Sin lenguaje comercial del proveedor. Español.

## Formato de salida de los verificadores
Archivo vendors/<vendor>/verif/T<n>.md con la tabla
| N° | Crit | Evaluación Banco | Veredicto | Evaluación sugerida | Evidencia (nombre oficial del documento + pág. PDF u hoja/fila + cita ≤20 palabras) | Justificación (≤25 palabras) |
Las dos columnas de evaluación se escriben con la clasificación textual de la escala seguida del número
entre paréntesis, exactamente así: «Completamente Cubierto (4)», «Cubierto: Modificación Menor (3)»,
«Cubierto: Modificación Mayor (2)», «Parcialmente Cubierto (1)», «No Cubierto (0)». Nunca el número solo.
- Evaluación Banco: la clasificación textual de la columna `eval` de la matriz y el `va` entre paréntesis.
  Si `eval` y `va` no coinciden, escribe la textual con el va real y márcalo: «Cubierto: Modificación Menor (VA=4 ⚠)».
  Sin calificar («Seleccionar» o va=None): «Sin calificar (—)».
- Evaluación sugerida: tu clasificación según la evidencia, con la misma forma. «N/A» para ítems «no relevante».
La columna Evidencia empieza siempre por el nombre oficial del documento (ver «Forma de citar»); si cita
varios documentos, cada uno lleva su nombre. Las secciones (a), (b) y (c) y la Justificación siguen la
misma regla cuando mencionan páginas o filas.
Después de la tabla: (a) ítems con calificación distinta, (b) 5-8 hallazgos clave con página,
(c) contradicciones matriz vs documentos. Todos los ítems, sin saltar ninguno.
Al terminar, responder en el chat solo con: ruta, ítems procesados, ítems con calificación distinta,
5 contradicciones principales.

## Pipeline por vendor (scripts/, se ejecutan en el terminal)
```
python scripts/00_nuevo_vendor.py <vendor>        # crea vendors/<vendor>/
# copiar documentos a vendors/<vendor>/docs/raw
python scripts/04_ingesta.py <vendor>             # 01 PDF→txt, 01a .toc.md, 01b anexos→txt, 02 matriz→T1..T8, INVENTARIO
# revisar NOMBRES.md y los .toc.md; lanzar los 8 agentes verificadores con el vendor (uno por hoja)
# implementación (si docs/raw trae la rúbrica del Banco, la ingesta genera matriz/IMPL.txt con 02b):
#   verificador-implementacion → verif/IMPL.md (0–5 por criterio); redactor-implementacion → informes/7_implementacion_pros_contras.md
#   python scripts/16_informe_bloques_impl.py <vendor>|--todos [--pdf] → informes/11_bloques_impl.md (+pdf): fortalezas (≥4), brechas (≤2) y contradicciones por bloque EI/F/I, solo desde verif/IMPL.md; --todos además vendors/INFORME_BLOQUES_IMPLEMENTACION.pdf
# comparativos entre vendors: analista-despliegue → vendors/COMPARATIVO_DESPLIEGUE.md;
#   analista-plataforma (comparativo; recorre TODA la documentación de cada vendor, uno por uno) → informes/13_plataforma_principal.md por vendor y vendors/COMPARATIVO_PLATAFORMA.md: modelos que soporta, plataformas en las que dice poder instalarse (AWS, GCP, Azure, Huawei, OCI, OpenShift/Kubernetes, VMware…), cuál propone al Banco (pasajes P/O) y cuál es la más fuerte en su documentación (nivel P>O>E>C>G, luego evidencia de clientes/arquitectura/certificación/región, luego nº de documentos y pasajes; tabla «Peso documental» + inventario de pasajes), y si coinciden. No recomienda. En Copilot: /plataforma
#   comparador-implementacion (tras verificar y redactar la implementación de cada vendor) → vendors/COMPARATIVO_IMPLEMENTACION.md;
#   comparador-t5 (tras el informe ejecutivo de T5 de cada vendor) → vendors/COMPARATIVO_T5.md
python scripts/18_resumen_matriz.py <vendor> [xlsx] [--limpiar]   # --limpiar aparta a matriz/_anterior/ los <hoja>.txt de una matriz anterior; xlsx por defecto: matrices/*<vendor>*.xlsx (carpeta matrices/, una matriz por vendor, no versionada; ver matrices/README.md). informes/12_resumen_matriz.md: puntaje y nivel por hoja y por categoría con la calificación del Banco tal cual, para CUALQUIER hoja con columnas N° y VA (T1–T8 o un documento nuevo); escribe matriz/<hoja>.txt; luego el agente resumen-matriz redacta el fundamento de cada categoría y hoja (sin recalificar ni contar) y ejecuta 19. En Copilot: /resumen-matriz
python scripts/19_resumen_matriz_pptx.py <vendor>|--todos [--completo]   # informes/RESUMEN_MATRIZ_<vendor>.pdf y .pptx; --todos: vendors/RESUMEN_MATRIZ_TODOS.pdf y .pptx (lámina comparativa vendors × hojas + cada vendor): resumen ejecutivo 16:9 (resultado por hoja; por hoja: categorías + fundamento; --completo: fundamento de cada categoría)
python scripts/09_semaforo_t5.py <vendor>     # informes/9_semaforo_T5.md: color por categoría (media de la calificación del Banco en T5 y niveles oficiales); luego el agente semaforo-t5 redacta el detalle
python scripts/10_presentacion_t5.py [--base carpeta]   # COMPARATIVO_SEMAFORO_T5.md (tablas) → agente comparador-semaforo-t5 (comentarios) → --pdf: PRESENTACION_T5.pdf
#   --pdf --estilo coe: PRESENTACION_T5_COE.pdf con el diseño del deck corporativo (16:9); python scripts/12_presentacion_t5_pptx.py --base carpeta → PRESENTACION_T5.pptx (PowerPoint, mismo diseño; requiere python-pptx)
#   python scripts/13_laminas_correo.py --base carpeta → LAMINA_1_resultado_T5.png y LAMINA_2_implementacion.png (2560×1440) + LAMINAS_CORREO.pdf: dos láminas para adjuntar a un correo (ranking T5 y lectura por vendor; rúbrica de implementación, despliegue y veredictos)
#   python scripts/14_laminas_correo_pptx.py --base carpeta → LAMINAS_CORREO.pptx (las mismas dos láminas en PowerPoint)
#   python scripts/15_lamina_despliegue.py --base carpeta → LAMINA_3_despliegue.png/.pdf/.pptx: lámina independiente «Modelos de despliegue y nubes» (tabla por vendor SaaS/PaaS/privada/on-premise/híbrido, nubes ofrecidas, quién opera; conteo de vendors por nube) desde COMPARATIVO_DESPLIEGUE.md y los 8_ de cada vendor
#   python scripts/17_imagenes_despliegue.py --base carpeta → HOJA_4_plataformas_por_modelo.png y DIAPOSITIVA_plataformas_por_modelo.png (PNG de la cuadrícula, desde los PDF de 08 y 10; requiere PyMuPDF)
#   agente generador-despliegue (solo ejecuta: 08 --pdf, 10 --pdf --estilo coe, 12, 17, 15; no redacta ni toca los 8_) → todas las salidas de despliegue de una vez; en Copilot: /generar-despliegue
#   vendors/NOTAS_DESPLIEGUE.md (tabla | Vendor | Nota |, editable a mano; condensa SOLO el 8_modelo_despliegue.md de cada vendor): nota por vendor bajo cada cuadrícula de «plataformas por modelo» (08 hoja 4, 10 y 12 diapositiva); si no existe, no se muestra nada
#   Estado del modelo en esas vistas (chip): Sí · Condicionado · «Tiene, no ofrece» (Ofrecido = No en el 8_ pero la condición o las nubes muestran que el vendor lo tiene para otros clientes/regiones/nubes; p. ej. Sunline SaaS solo Asia) · No (excluido, sin evidencia de que lo tenga) · N/E. Lo decide m.chip_modelo(ofrecido, condicion, nubes) en 07; el punto de nube discontinuo = la tiene pero no la ofrece al Banco para ese modelo
#   Columna «Otras» de la cuadrícula: nubes o plataformas sin columna propia nombradas en «Nubes para ese modelo» del 8_ (lista OTRAS en 08: Kubernetes, EKS/AKS/GKE, Huawei CCE, VMware, Alibaba, Tencent, IBM Cloud, IBM LinuxONE, FIS Private Cloud, Kyndryl, Exadata), como texto; en la fila Declaradas, la lista literal (menos lo que ya tiene columna) va en una línea bajo la tabla
#   Fila «Declaradas» de la cuadrícula: la escribe el agente analista-despliegue como última fila obligatoria de la tabla Modelos del 8_ («Plataformas declaradas (todos los modelos)») (Ofrecido = Declarado; Nubes = lista literal de nubes y PLATAFORMAS DE DESPLIEGUE (Kubernetes, OpenShift, VMware, EKS/AKS/GKE/CCE, nube privada) que el vendor nombra en general, con cita hoja/fila; nunca software requerido como Kafka, PostgreSQL, Istio o Prometheus). Es la única forma de mostrar lo que el vendor declara sin atarlo a un modelo; no se infiere nada: si el 8_ no la tiene (FIS, sin docs locales), no aparece
# MATRICES NUEVAS (flujo independiente, no usa vendors/ ni verif/): deja un Excel por vendor en matrices/ (nombre con el vendor) y lanza el agente evaluador-dimensiones (Copilot: /evaluar-dimensiones).
#   python scripts/20_evaluacion_dimensiones.py [--vendor v]  → matrices/evaluacion/<vendor>/<hoja>.md (lectura completa por hoja: ítems, calificación, sustento; puntaje y nivel por categoría), EVALUACION_<vendor>.md (marcadores por dimensión) y matrices/evaluacion/EVALUACION_DIMENSIONES.md (vendors × dimensiones); el agente escribe la evaluación de cada dimensión (en qué se apoya, parcial, no cubierto, observaciones, pendientes), la general y la lectura comparada. Sin recalificar.
# El PDF es opcional en todos los scripts (--pdf en 07, 08, 10, 13, 15, 16, 19; requiere Edge/Chrome sin ventana). Los agentes NO lo generan: se hace después, aparte. Sin navegador: salidas HTML + PowerPoint (12, 14, 15, 19).
# todo lo anterior en un solo paso: agente presentador-t5 (ejecuta 09 y 10, redacta semáforos, fichas (redactor-ficha-t5) y comentarios)
python scripts/06_validar_verif.py <vendor>       # valida filas, formato, VA y citas de cada verif/T<n>.md
python scripts/03_consolidar.py <vendor>          # verif/00_consolidado.md
# lanzar los agentes redactores y el revisor con el vendor
python scripts/05_comparar.py                     # vendors/COMPARATIVO.md con todos los vendors
```

## Cómo se invocan los agentes en Copilot
- Agentes personalizados en `.github/agents/*.agent.md`: se eligen en el selector de agentes de Copilot Chat (VS Code)
  o se asignan a un issue para el Copilot coding agent. Siempre se les indica el vendor: «verifica T3 del vendor acme».
- Prompts reutilizables en `.github/prompts/*.prompt.md`: se invocan con `/nombre` en Copilot Chat y piden el vendor
  y la hoja como parámetros.
- Copilot no ejecuta agentes en paralelo dentro de un mismo chat: cada hoja se verifica en su propia conversación.
  T6 (167 ítems) se verifica en tres conversaciones (bloques E1–E56, E57–E112, E113–E167) con el prompt
  `/verificar-t6-bloque` y después se unen con `/unir-t6`.

