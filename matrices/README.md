# matrices/ — matrices técnicas del Banco (una por vendor)

Deja aquí el Excel de la matriz técnica calificada de cada vendor, con el nombre del vendor en el archivo, por ejemplo:
`matrices/tm.xlsx`, `matrices/Evaluacion Sunline.xlsx`, `matrices/infosys_v2.xlsx`. Vale cualquier nombre que contenga la carpeta
del vendor (`vendors/<vendor>`) o su nombre oficial (Thought Machine, Sunline, FIS, Infosys, Pismo, Temenos).

Cualquier conjunto de hojas sirve: una hoja cuenta como hoja de matriz si tiene la fila de cabecera con las columnas N° y VA.

Cómo se usa (Copilot): `/resumen-matriz vendor: todos` → el agente toma de aquí la matriz de cada vendor, ejecuta
`scripts/18_resumen_matriz.py`, redacta los fundamentos por categoría y por hoja y genera `vendors/RESUMEN_MATRIZ_TODOS.pdf` y `.pptx`.
Orden de búsqueda del script: 1) ruta dada en el comando, 2) `matrices/*<vendor>*.xlsx`, 3) `vendors/<vendor>/docs/raw`, 4) `vendors/<vendor>/`.
Si en `matrices/` hay más de un archivo para el mismo vendor, se usa el más reciente (fecha de modificación) y se avisa.

Los Excel de esta carpeta son confidenciales: no se suben al repositorio (.gitignore).
