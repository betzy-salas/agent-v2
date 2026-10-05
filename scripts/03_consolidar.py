#!/usr/bin/env python3
"""F3 · Consolida vendors/<vendor>/verif/T*.md en vendors/<vendor>/verif/00_consolidado.md

Uso: python scripts/03_consolidar.py <vendor>
"""
import re, glob
from pathlib import Path
from _comun import arg_vendor, vendor_dir
v = arg_vendor(); d = vendor_dir(v)
W = {'T1':.11,'T2':.11,'T3':.12,'T4':.11,'T5':.12,'T6':.14,'T7':.15,'T8':.14}
num = lambda s: (lambda m: int(m.group()) if m else None)(re.search(r'\d', s))
out = [f'# Consolidado — {v}\n', '| Hoja | n | Calif Banco | Calif sugerida | Δ | Confirma | Completa | Contradice | Sin evid. | Killers suben | Killers bajan |', '|---|---|---|---|---|---|---|---|---|---|---|']
tb = ts = 0; wsum = 0; hojas = []
for f in sorted(glob.glob(str(d / 'verif' / 'T*.md'))):
    h = Path(f).stem  # nombre de hoja; Path funciona con / y con \
    if h not in W: continue  # ignora archivos que no sean T1..T8
    it = []; vistos = set(); en_tabla = True
    # Solo la tabla principal: antes de la primera sección "## (" y, si existe, después de "## Tabla de verificación".
    for line in open(f, encoding='utf-8'):
        if line.startswith('## Tabla'): en_tabla = True; continue
        if line.startswith('## ('): en_tabla = False
        if not en_tabla: continue
        c = [x.strip() for x in re.split(r'(?<!\\)\|', line.strip().strip('|'))]  # respeta «\|» escapadas dentro de celdas
        if len(c) >= 5 and re.match(r'^E\d+$', c[0]) and c[0] not in vistos:
            vistos.add(c[0]); it.append((c[0], c[1], num(c[2]), num(c[4]), c[3].upper()))
    n = len(it); b = sum((x[2] or 0) for x in it)/n/4*100; s = sum((x[3] if x[3] is not None else x[2] or 0) for x in it)/n/4*100  # N/A o sin calificar → se mantiene lo del Banco
    v = {k: sum(1 for x in it if k in x[4]) for k in ['CONFIRMA','COMPLETA','CONTRADICE','SIN']}
    up = [x[0] for x in it if 'Killer' in x[1] and x[3] is not None and x[2] is not None and x[3] > x[2]]
    dn = [x[0] for x in it if 'Killer' in x[1] and x[3] is not None and x[2] is not None and x[3] < x[2]]
    b, s = round(b, 1), round(s, 1)  # Δ sobre los valores ya redondeados, para que cuadre con lo impreso
    out.append(f"| {h} | {n} | {b:.1f} | {s:.1f} | {s-b:+.1f} | {v['CONFIRMA']} | {v['COMPLETA']} | {v['CONTRADICE']} | {v['SIN']} | {', '.join(up)} | {', '.join(dn)} |")
    tb += W[h]*b; ts += W[h]*s; wsum += W[h]; hojas.append(h)
if len(hojas) < 8:
    tb, ts = tb / wsum, ts / wsum  # normalizado por los pesos presentes
    out.append(f'\n**Total ponderado PARCIAL ({", ".join(hojas)}; faltan {8-len(hojas)} hojas):** Banco {tb:.1f} → sugerido {ts:.1f}. '
               f'Normalizado por los pesos de las hojas verificadas; no es comparable con un total de 8 hojas.\n')
else:
    out.append(f'\n**Total ponderado:** Banco {tb:.1f} → sugerido {ts:.1f}\n')
open(d / 'verif' / '00_consolidado.md', 'w', encoding='utf-8').write('\n'.join(out)); print('\n'.join(out))