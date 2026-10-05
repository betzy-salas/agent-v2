#!/usr/bin/env python3
"""Compara los consolidados de todos los vendors: vendors/*/verif/00_consolidado.md → vendors/COMPARATIVO.md

Uso: python scripts/05_comparar.py
"""
import re
from pathlib import Path
from _comun import VENDORS
HOJAS = ['T1','T2','T3','T4','T5','T6','T7','T8']
datos = {}
for c in sorted(VENDORS.glob('*/verif/00_consolidado.md')):
    v = c.parts[-3]; t = c.read_text(encoding='utf-8'); d = {}
    for l in t.splitlines():
        m = re.match(r'^\|\s*(T\d)\s*\|\s*(\d+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|', l)
        if m: d[m.group(1)] = (int(m.group(2)), float(m.group(3)), float(m.group(4)))
    mt = re.search(r'(?:BCP|Banco) ([\d.]+) → sugerido ([\d.]+)', t)
    if mt: d['TOTAL'] = (sum(x[0] for x in d.values()), float(mt.group(1)), float(mt.group(2)))
    datos[v] = d
if not datos: raise SystemExit("No hay consolidados todavía (vendors/*/verif/00_consolidado.md).")
nivel = lambda x: 'Cumple plenamente' if x >= 85 else 'Cumple' if x >= 70 else 'Parcial' if x >= 50 else 'No cumple'
out = ['# Comparativo de vendors (puntaje verificado; entre paréntesis el del Banco)', '',
       '| Hoja | ' + ' | '.join(datos) + ' |', '|---|' + '---|' * len(datos)]
for h in HOJAS + ['TOTAL']:
    fila = [f"{d[h][2]:.1f} ({d[h][1]:.1f})" if h in d else '—' for d in datos.values()]
    out.append(f"| {'**Total ponderado**' if h=='TOTAL' else h} | " + ' | '.join(fila) + ' |')
out += ['', '| Vendor | Ítems | Banco | Verificado | Δ | Nivel verificado |', '|---|---|---|---|---|---|']
for v, d in sorted(datos.items(), key=lambda kv: -kv[1].get('TOTAL', (0,0,0))[2]):
    if 'TOTAL' in d: n,b,s = d['TOTAL']; out.append(f"| {v} | {n} | {b:.1f} | {s:.1f} | {s-b:+.1f} | {nivel(s)} |")
(VENDORS / 'COMPARATIVO.md').write_text('\n'.join(out) + '\n', encoding='utf-8'); print('\n'.join(out))
