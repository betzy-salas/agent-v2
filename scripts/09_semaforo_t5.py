#!/usr/bin/env python3
"""Semáforo de la hoja T5 (Capacidades de desarrollo) por categoría, a partir de la calificación del Banco en la matriz.

Lee vendors/<vendor>/matriz/T5.txt y escribe vendors/<vendor>/informes/9_semaforo_T5.md. No reclasifica nada: el color de
cada ítem es una traducción fija de la calificación que ya está en la matriz (columna VA, escala 0–4):
  4 → VERDE (positivo) · 3 y 2 → AMARILLO (parcial) · 1 y 0 → ROJO (negativo) · sin calificar → GRIS.
Por categoría se cuentan los ítems de cada color; no se asigna una nota nueva. El agente semaforo-t5 completa después,
en el mismo archivo, el párrafo «Lectura» de cada categoría condensando solo lo que ya dicen la pregunta, la respuesta
del proveedor y el sustento del evaluador.

Uso:  python scripts/09_semaforo_t5.py <vendor>
"""
import datetime, re, sys
from collections import OrderedDict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
COLOR = {4: ('VERDE', '🟢'), 3: ('AMARILLO', '🟡'), 2: ('AMARILLO', '🟡'), 1: ('ROJO', '🔴'), 0: ('ROJO', '🔴'), None: ('SIN CALIFICAR', '⚪')}

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
    tot = {c: 0 for c in ('VERDE', 'AMARILLO', 'ROJO', 'SIN CALIFICAR')}
    for it in items: tot[COLOR[it['va']][0]] += 1
    hoy = datetime.date.today().strftime('%Y-%m-%d')
    L = [f'# 9. Semáforo T5 (Capacidades de desarrollo) — {vendor}', '',
         '## Cabecera', '',
         f'- Vendor: {vendor}', f'- Fuente única de las calificaciones: Matriz del Banco, hoja T5 (vendors/{vendor}/matriz/T5.txt, columna VA y clasificación textual del evaluador). No se recalifica ningún ítem.',
         f'- Ítems: {len(items)} · Categorías: {len(cats)} · Fecha: {hoy}',
         '- Regla fija de color por ítem: Completamente Cubierto (4) → 🟢 VERDE positivo · Cubierto: Modificación Menor (3) o Mayor (2) → 🟡 AMARILLO parcial · Parcialmente Cubierto (1) o No Cubierto (0) → 🔴 ROJO negativo · sin calificar → ⚪.',
         '- Una categoría no recibe un color propio: se muestran sus conteos. «Mayoría» indica solo el color con más ítems.',
         f'- Totales: 🟢 {tot["VERDE"]} · 🟡 {tot["AMARILLO"]} · 🔴 {tot["ROJO"]}' + (f' · ⚪ {tot["SIN CALIFICAR"]}' if tot['SIN CALIFICAR'] else ''),
         '', '## Resumen por categoría', '',
         '| Categoría | Ítems | 🟢 Verde | 🟡 Amarillo | 🔴 Rojo | Mayoría | Barra |', '|---|---:|---:|---:|---:|---|---|']
    for cat, its in cats.items():
        v = sum(1 for i in its if COLOR[i['va']][0] == 'VERDE'); a = sum(1 for i in its if COLOR[i['va']][0] == 'AMARILLO')
        r = sum(1 for i in its if COLOR[i['va']][0] == 'ROJO'); g = len(its) - v - a - r
        may = max((('🟢 Verde', v), ('🟡 Amarillo', a), ('🔴 Rojo', r)), key=lambda x: x[1])
        may_txt = may[0] if may[1] * 2 > len(its) else f'{may[0]} (sin mayoría absoluta)' if may[1] else '—'
        L.append(f'| {cat} | {len(its)} | {v} | {a} | {r} | {may_txt} | {barra(v, a, r, g)} |')
    L += ['', '## Detalle por categoría', '', 'Cada tabla copia la calificación del Banco tal como está en la matriz y el color que le corresponde por la regla fija. La pregunta, la respuesta del proveedor y el sustento del evaluador están abreviados; el texto completo está en la matriz. La «Lectura» de cada categoría la redacta el agente semaforo-t5 condensando solo esos tres textos.', '']
    for cat, its in cats.items():
        v = sum(1 for i in its if COLOR[i['va']][0] == 'VERDE'); a = sum(1 for i in its if COLOR[i['va']][0] == 'AMARILLO'); r = sum(1 for i in its if COLOR[i['va']][0] == 'ROJO')
        L += [f'### {cat}', '', f'{len(its)} ítems · 🟢 {v} · 🟡 {a} · 🔴 {r}', '',
              '| Ítem | Crit | Evaluación Banco | Color | Pregunta | Respuesta del proveedor | Sustento del evaluador |', '|---|---|---|---|---|---|---|']
        for it in sorted(its, key=lambda i: int(i['id'][1:])):
            nombre, sim = COLOR[it['va']]
            ev = f'{it["eval"]} ({it["va"]})' if it['va'] is not None else 'Sin calificar (—)'
            L.append(f'| {it["id"]} | {celda(it["crit"])} | {ev} | {sim} {nombre} | {celda(it["q"], 160)} | {celda(it["prov"], 220)} | {celda(it["sust"], 160) or "—"} |')
        L += ['', '**Lectura**', '', f'<!-- lectura: {cat} -->', '']
    L += ['## Nota', '', 'Documento generado por scripts/09_semaforo_t5.py a partir de la matriz; sin ranking ni recomendación. Las verificaciones (verif/T5.md) no intervienen en el color.']
    out = base / 'informes' / '9_semaforo_T5.md'; out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(L) + '\n', encoding='utf-8')
    print(f'{out}\n{len(items)} ítems en {len(cats)} categorías · 🟢 {tot["VERDE"]} · 🟡 {tot["AMARILLO"]} · 🔴 {tot["ROJO"]}' + (f' · ⚪ {tot["SIN CALIFICAR"]}' if tot['SIN CALIFICAR'] else ''))

if __name__ == '__main__':
    main()
