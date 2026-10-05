#!/usr/bin/env python3
"""Valida las verificaciones de un vendor: vendors/<vendor>/verif/T<n>.md

Comprueba, por hoja: filas de la tabla principal = ítems de la matriz (sin faltantes ni repetidos), 7 columnas
(10 en T5), formato textual de las evaluaciones, Evaluación Banco coherente con el VA de la matriz, veredictos
válidos, y que toda cita de página/hoja/fila lleve delante un nombre oficial de vendors/<vendor>/NOMBRES.md.

Uso: python scripts/06_validar_verif.py <vendor> [T1 ... T8]
Código de salida 1 si alguna hoja tiene errores.
"""
import re, sys, collections
from pathlib import Path
from _comun import arg_vendor, vendor_dir

v = arg_vendor(); d = vendor_dir(v)
hojas = [a for a in sys.argv[2:] if re.fullmatch(r'T[1-8]', a)] or [f'T{i}' for i in range(1, 9)]
FMT = re.compile(r'^(Completamente Cubierto \(4\)|Cubierto: Modificación Menor \((3|VA=\d ⚠)\)|Cubierto: Modificación Mayor \((2|VA=\d ⚠)\)|Parcialmente Cubierto \((1|VA=\d ⚠)\)|No Cubierto \((0|VA=\d ⚠)\)|Sin calificar \(—\)|N/A)$')
VER = {'CONFIRMA', 'COMPLETA', 'CONTRADICE', 'SIN EVIDENCIA'}
nombres = [m.group(1).strip() for m in re.finditer(r'^\|\s*`[^`]+`\s*\|\s*([^|]+?)\s*\|', (d / 'NOMBRES.md').read_text(encoding='utf-8'), re.M)] if (d / 'NOMBRES.md').exists() else []
NOM = '(' + '|'.join(re.escape(x) for x in nombres) + r')(?:, hoja [^,]+)?' if nombres else None
num = lambda s: (lambda m: int(m.group()) if m else None)(re.search(r'\d', s))
total_err = 0
for h in hojas:
    f = d / 'verif' / f'{h}.md'; m = d / 'matriz' / f'{h}.txt'
    if not f.exists(): print(f'{h}: sin verificación (verif/{h}.md no existe)'); continue
    if not m.exists(): print(f'{h}: sin matriz'); continue
    mtx = m.read_text(encoding='utf-8'); t = f.read_text(encoding='utf-8')
    ids = re.findall(r'^\[(E\d+)\]', mtx, re.M)
    va = {k: (None if x == 'None' else int(x)) for k, x in re.findall(r'^\[(E\d+)\] .*? va=(\S+)', mtx, re.M)}
    ev = dict(re.findall(r'^\[(E\d+)\] .*? eval=(.*?) evaluador=', mtx, re.M))
    sec = None; rows = {}; dup = []
    for l in t.split('\n'):
        if l.startswith('## '): sec = l
        if re.match(r'^\|\s*E\d+\s*\|', l) and (sec is None or sec.startswith('## Tabla')):
            c = [x.strip() for x in re.split(r'(?<!\\)\|', l.strip().strip('|'))]
            if c[0] in rows: dup.append(c[0])
            else: rows[c[0]] = c
    err = []
    faltan = [i for i in ids if i not in rows]; sobran = [i for i in rows if i not in ids]
    if faltan: err.append(f'faltan {len(faltan)} ítems: {faltan[:8]}')
    if sobran: err.append(f'sobran ids no presentes en la matriz: {sobran[:8]}')
    if dup: err.append(f'ids repetidos: {dup[:8]}')
    esperado = 10 if h == 'T5' else 7
    malcol = [k for k, r in rows.items() if len(r) != esperado]
    if malcol: err.append(f'{len(malcol)} filas sin {esperado} columnas (¿«|» dentro de una celda?): {malcol[:8]}')
    fmt = [k for k, r in rows.items() if len(r) >= 5 and (not FMT.match(r[2]) or not FMT.match(r[4]))]
    if fmt: err.append(f'{len(fmt)} filas con evaluación fuera de formato: {fmt[:8]}')
    verd = [k for k, r in rows.items() if len(r) >= 4 and r[3].upper() not in VER]
    if verd: err.append(f'{len(verd)} filas con veredicto no válido: {verd[:8]}')
    bcp = []
    for k, r in rows.items():
        if len(r) < 3 or k not in va: continue
        if ev.get(k) == 'Seleccionar' or va[k] is None:
            if 'Sin calificar' not in r[2]: bcp.append(k)
        elif str(va[k]) not in r[2]: bcp.append(k)
    if bcp: err.append(f'{len(bcp)} filas cuya Evaluación Banco no refleja el VA de la matriz: {bcp[:8]}')
    sueltas = []
    if NOM:
        for l in t.split('\n'):
            if l.startswith(('| Propuesta', '| Anexo', '| Key Roles', '| Nombre')) or re.match(r'^\|\s*`', l): continue
            l_sin_citas = re.sub(r'«[^»]*»', lambda m: ' ' * len(m.group(0)), l)  # lo entrecomillado es cita literal, no referencia propia
            for mm in re.finditer(r"(?<![\w.])(p\.\s?\d+|f\.\s?\d+|slide \d+)", l_sin_citas):
                if not re.search(NOM + r"[^|]*$", l[max(0, mm.start() - 110):mm.start()]): sueltas.append(l[max(0, mm.start() - 30):mm.end()].strip())
        if sueltas: err.append(f'{len(sueltas)} citas sin nombre oficial de documento, p.ej. «…{sueltas[0][-60:]}»')
    vc = collections.Counter(r[3].upper() for r in rows.values() if len(r) >= 4)
    dif = [(k, va[k], num(r[4])) for k, r in rows.items() if len(r) >= 5 and k in va and va[k] is not None and num(r[4]) is not None and num(r[4]) != va[k]]
    estado = 'OK' if not err else f'{len(err)} ERRORES'
    print(f'{h}: {len(rows)}/{len(ids)} ítems · {dict(vc)} · nota distinta {len(dif)} (bajan {sum(1 for x in dif if x[2] < x[1])}, suben {sum(1 for x in dif if x[2] > x[1])}) → {estado}')
    for e in err: print('   ✗', e)
    total_err += len(err)
sys.exit(1 if total_err else 0)
