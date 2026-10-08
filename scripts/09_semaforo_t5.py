#!/usr/bin/env python3
"""Semáforo de la hoja T5 (Capacidades de desarrollo) por categoría, a partir de la calificación del Banco en la matriz.

Lee vendors/<vendor>/matriz/T5.txt y escribe vendors/<vendor>/informes/9_semaforo_T5.md. No reclasifica nada:
- Puntaje de la categoría = media de las calificaciones del Banco (columna VA, 0–4) de sus ítems, sobre 4, en 0–100
  (la misma fórmula del consolidado). Los ítems sin calificar no entran en la media.
- Color de la categoría según los niveles de cumplimiento oficiales de CLAUDE.md: ≥ 70 → VERDE (positivo: cumple o cumple
  plenamente) · 50–69 → AMARILLO (parcial) · < 50 → ROJO (negativo: no cumple).
- Como apoyo, cada ítem lleva el color de su propia calificación (4 verde · 3 y 2 amarillo · 1 y 0 rojo) en el anexo.
El agente semaforo-t5 completa después, en el mismo archivo, el «Detalle» de cada categoría condensando solo lo que ya
dicen la pregunta, la respuesta del proveedor y el sustento del evaluador.

Uso:  python scripts/09_semaforo_t5.py <vendor>
"""
import datetime, re, sys
from collections import OrderedDict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
COLOR = {4: ('VERDE', '🟢'), 3: ('AMARILLO', '🟡'), 2: ('AMARILLO', '🟡'), 1: ('ROJO', '🔴'), 0: ('ROJO', '🔴'), None: ('SIN CALIFICAR', '⚪')}

def color_categoria(its):
    """Media de VA sobre 4 en 0–100 y color por los niveles oficiales (≥70 verde, 50–69 amarillo, <50 rojo)."""
    vas = [i['va'] for i in its if i['va'] is not None]
    if not vas: return None, ('SIN CALIFICAR', '⚪')
    pct = round(sum(vas) / (4 * len(vas)) * 100, 1)
    return pct, ('VERDE', '🟢') if pct >= 70 else ('AMARILLO', '🟡') if pct >= 50 else ('ROJO', '🔴')

def leer_items(ruta):
    items = []; cur = None
    for l in ruta.read_text(encoding='utf-8-sig').replace('\r\n', '\n').split('\n'):
        m = re.match(r'^\[(E\d+)\]\s+cat=(.*?)\s+crit=(.*?)\s+va=(\S+)\s+eval=(.*?)\s+evaluador=(.*)$', l)
        if m:
            va = m.group(4); va = int(va) if va.isdigit() else None
            cur = dict(id=m.group(1), cat=m.group(2).strip(), crit=m.group(3).strip(), va=va, eval=m.group(5).strip(), evaluador=m.group(6).strip(), q='', prov='', sust='', extra=[])
            items.append(cur); continue
        if cur is None or not l.strip(): continue
        if l.startswith('Q:'): cur['q'] = l[2:].strip()
        elif l.startswith('PROVEEDOR:'): cur['prov'] = l[len('PROVEEDOR:'):].strip()
        elif l.startswith('SUSTENTO:'): cur['sust'] = l[len('SUSTENTO:'):].strip()
        elif re.match(r'^[A-ZÁÉÍÓÚ]{1,4}:', l): cur['extra'].append(l.strip())
        else:
            for k in ('sust', 'prov', 'q'):
                if cur[k]: cur[k] += ' ' + l.strip(); break
    return items

def descartable(it):
    q = it['q'].lower().strip()
    return q.startswith('se elimin') or q.startswith('se elemin') or q.startswith('eliminar')

def celda(t, n=None):
    t = (t or '').replace('|', '/').replace('\n', ' ').strip()
    return t if n is None or len(t) <= n else t[:n - 1].rstrip() + '…'

def barra(v, a, r, g):
    tot = v + a + r + g
    if not tot: return ''
    return ''.join(s * n for s, n in (('🟢', v), ('🟡', a), ('🔴', r), ('⚪', g)))

def main():
    if len(sys.argv) < 2: sys.exit('Uso: python scripts/09_semaforo_t5.py <vendor>')
    vendor = sys.argv[1]; base = RAIZ / 'vendors' / vendor
    matriz = base / 'matriz' / 'T5.txt'
    if not matriz.exists(): sys.exit(f'No existe {matriz}. Corre antes la ingesta (04_ingesta.py {vendor}).')
    items = [it for it in leer_items(matriz) if not descartable(it)]
    if not items: sys.exit('La matriz T5 no tiene ítems legibles.')
    cats = OrderedDict()
    for it in items: cats.setdefault(it['cat'], []).append(it)
    cat_res = {cat: color_categoria(its) for cat, its in cats.items()}
    tot = {c: 0 for c in ('VERDE', 'AMARILLO', 'ROJO', 'SIN CALIFICAR')}
    for cat in cats: tot[cat_res[cat][1][0]] += 1
    hoy = datetime.date.today().strftime('%Y-%m-%d')
    L = [f'# 9. Semáforo T5 (Capacidades de desarrollo) por categoría — {vendor}', '',
         '## Cabecera', '',
         f'- Vendor: {vendor}', f'- Fuente única de las calificaciones: Matriz del Banco, hoja T5 (vendors/{vendor}/matriz/T5.txt, columna VA y clasificación textual del evaluador). No se recalifica ningún ítem.',
         f'- Ítems: {len(items)} · Categorías: {len(cats)} · Fecha: {hoy}',
         '- Puntaje de la categoría: media de las calificaciones del Banco (0–4) de sus ítems, sobre 4, en escala 0–100 (misma fórmula del consolidado). Los ítems sin calificar no entran en la media.',
         '- Color de la categoría según los niveles de cumplimiento oficiales (CLAUDE.md, «Niveles de cumplimiento»): 🟢 VERDE positivo ≥ 70 (Cumple / Cumple plenamente) · 🟡 AMARILLO parcial 50–69 (Parcial) · 🔴 ROJO negativo < 50 (No cumple).',
         f'- Categorías: 🟢 {tot["VERDE"]} · 🟡 {tot["AMARILLO"]} · 🔴 {tot["ROJO"]}' + (f' · ⚪ {tot["SIN CALIFICAR"]}' if tot['SIN CALIFICAR'] else ''),
         '', '## Semáforo por categoría', '',
         '| Categoría | Color | Puntaje 0–100 | Ítems | Calificaciones del Banco (4 / 3 / 2 / 1 / 0) | Criticidad Indispensable |', '|---|---|---:|---:|---|---|']
    for cat, its in cats.items():
        pct, (nombre, sim) = cat_res[cat]
        dist = ' / '.join(str(sum(1 for i in its if i['va'] == v)) for v in (4, 3, 2, 1, 0))
        ind = sum(1 for i in its if 'indispensable' in i['crit'].lower())
        L.append(f'| {cat} | {sim} {nombre} | {pct if pct is not None else "—"} | {len(its)} | {dist} | {ind} de {len(its)} |')
    L += ['', '## Detalle por categoría', '', 'Para cada categoría: su color y puntaje, el «Detalle» (lo redacta el agente semaforo-t5 condensando solo la pregunta, la respuesta del proveedor y el sustento del evaluador de la matriz, sin añadir hechos) y, como anexo, sus ítems con la calificación del Banco tal como está en la matriz. El color por ítem (4 🟢 · 3 y 2 🟡 · 1 y 0 🔴) es solo de apoyo para localizar qué ítems sostienen o restan al color de la categoría.', '']
    for cat, its in cats.items():
        v = sum(1 for i in its if COLOR[i['va']][0] == 'VERDE'); a = sum(1 for i in its if COLOR[i['va']][0] == 'AMARILLO'); r = sum(1 for i in its if COLOR[i['va']][0] == 'ROJO')
        pct, (nombre, sim) = cat_res[cat]
        L += [f'### {cat} — {sim} {nombre} ({pct if pct is not None else "—"})', '', f'{len(its)} ítems · calificaciones del Banco: 🟢 (4) {v} · 🟡 (3 y 2) {a} · 🔴 (1 y 0) {r}', '',
              '**Detalle**', '', f'<!-- lectura: {cat} -->', '', '**Ítems (anexo)**', '',
              '| Ítem | Crit | Evaluación Banco | Color del ítem | Pregunta | Respuesta del proveedor | Sustento del evaluador |', '|---|---|---|---|---|---|---|']
        for it in sorted(its, key=lambda i: int(i['id'][1:])):
            nombre, sim = COLOR[it['va']]
            ev = f'{it["eval"]} ({it["va"]})' if it['va'] is not None else 'Sin calificar (—)'
            L.append(f'| {it["id"]} | {celda(it["crit"])} | {ev} | {sim} {nombre} | {celda(it["q"], 160)} | {celda(it["prov"], 220)} | {celda(it["sust"], 160) or "—"} |')
        L += ['']
    L += ['## Nota', '', 'Documento generado por scripts/09_semaforo_t5.py a partir de la matriz; sin ranking ni recomendación. Las verificaciones (verif/T5.md) no intervienen en el color.']
    out = base / 'informes' / '9_semaforo_T5.md'; out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(L) + '\n', encoding='utf-8')
    print(f'{out}\n{len(items)} ítems en {len(cats)} categorías · categorías 🟢 {tot["VERDE"]} · 🟡 {tot["AMARILLO"]} · 🔴 {tot["ROJO"]}' + (f' · ⚪ {tot["SIN CALIFICAR"]}' if tot['SIN CALIFICAR'] else ''))

if __name__ == '__main__':
    main()
