#!/usr/bin/env python3
"""Crea la carpeta de un vendor nuevo: vendors/<vendor>/{docs/raw, docs/txt, matriz, verif, informes} + INVENTARIO.md.

Uso: python scripts/00_nuevo_vendor.py <vendor>
Luego: copia los documentos del vendor a vendors/<vendor>/docs/raw y ejecuta
       python scripts/04_ingesta.py <vendor>
"""
import sys
from _comun import arg_vendor, vendor_dir, VENDORS

v = arg_vendor()
if (VENDORS / v).exists():
    sys.exit(f"vendors/{v} ya existe.")
d = vendor_dir(v, crear=True)
(d / 'INVENTARIO.md').write_text(f"""# INVENTARIO — {v}

| Archivo (docs/raw) | Tipo | Fecha/versión | Dimensiones que toca | Notas |
|---|---|---|---|---|
| _(lo rellena scripts/04_ingesta.py; completa Tipo y Dimensiones a mano)_ | | | | |

## Estado de la ingesta

_(lo rellena scripts/04_ingesta.py)_

## Documentos referenciados y no presentes

_(anexos, correos o adjuntos que la propuesta cita y no están en docs/raw)_
""", encoding='utf-8')
for s in ('docs/raw', 'docs/txt', 'matriz', 'verif', 'informes'):
    (d / s / '.gitkeep').touch()
print(f"Creado vendors/{v}/ con docs/raw, docs/txt, matriz, verif, informes e INVENTARIO.md")
print(f"Siguiente: copia los documentos a vendors/{v}/docs/raw y ejecuta  python scripts/04_ingesta.py {v}")
