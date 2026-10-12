#!/usr/bin/env python3
"""Informe por vendor de la rúbrica de implementación leída por bloques (EI estrategia, F fabricante, I implementador):
fortalezas, brechas y contradicciones, a partir ÚNICAMENTE de vendors/<vendor>/verif/IMPL.md (verificador-implementacion).
No recalifica ni redacta hechos nuevos: clasifica cada criterio por el puntaje ya verificado y copia su descriptor,
evidencia y justificación; las secciones de hallazgos, contradicciones, señales y preguntas se copian tal cual.

Clasificación por criterio (puntaje 0–5 de la verificación):
  fortaleza  = puntaje ≥ 4      · intermedio = 3      · brecha = puntaje ≤ 2 (incluye «Solo declarado» con tope y «No encontrado»)
Los criterios informativos (sin puntaje) no se clasifican; se listan al final del bloque F/I como datos registrados.

Uso:  python scripts/16_informe_bloques_impl.py <vendor> [--pdf]        → vendors/<vendor>/informes/11_bloques_impl.md (+ .html/.pdf)
      python scripts/16_informe_bloques_impl.py --todos [--pdf]         → lo anterior para cada vendor con verif/IMPL.md
                                                                          + vendors/INFORME_BLOQUES_IMPLEMENTACION.html/.pdf (todos, uno por sección)
"""
import datetime, html, importlib.util, re, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parent
spec = importlib.util.spec_from_file_location('m', AQUI / '07_informe_implementacion.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
esc = html.escape

def puntaje(txt):
    mm = re.match(r'^\s*(\d+(?:\.\d+)?)\s*[-—–]', txt or '')
    return float(mm.group(1)) if mm else None

def col(hdr, *pref):
    for i, h in enumerate(hdr):
        if any(m._norm(h).startswith(m._norm(p)) for p in pref): return i
    return None

def filas_tabla(body, con_impl=False):
    hdr, rows = m.first_table(body)
    if not hdr: return []
    ic, icr, ip, ir, ie, ij = col(hdr, 'codigo', 'código'), col(hdr, 'criterio'), col(hdr, 'puntaje'), col(hdr, 'respaldo'), col(hdr, 'evidencia'), col(hdr, 'justificacion', 'justificación')
    iresp, ii = col(hdr, 'respuesta'), col(hdr, 'implementador')
    out = []
    for r in rows:
        r = r + [''] * (len(hdr) - len(r))
        g = lambda i: m.nombres_en_texto(r[i]).strip() if i is not None else ''
        out.append({'impl': g(ii) if con_impl else '', 'cod': g(ic), 'crit': g(icr), 'resp': g(iresp), 'punt': g(ip), 'n': puntaje(g(ip)),
                    'respaldo': g(ir), 'ev': g(ie), 'just': g(ij)})
    return out

def leer(vendor):
    f = m.VENDORS / vendor / 'verif' / 'IMPL.md'
    if not f.exists(): return None
    md = m.leer_md(f); secs = m.sections(md)
    cab = md.split('\n## ', 1)[0]
    d = {'vendor': vendor, 'nombre': m.nombre(vendor), 'cabecera': cab,
         'fecha': (re.search(r'Fecha:\s*(\S+)', cab) or [None, ''])[1],
         'docs': re.findall(r'^\s*-\s+(.+?)\s+\(docs/txt/', cab, re.M),
         'impls': (re.search(r'Implementadores identificados:\s*(.+)', cab) or [None, ''])[1].strip(),
         'EI': filas_tabla(m.find_section(secs, 'Tabla EI')), 'F': filas_tabla(m.find_section(secs, 'Tabla F')), 'I': filas_tabla(m.find_section(secs, 'Tabla I'), True),
         'resumen': m.first_table(m.find_section(secs, 'Resumen por bloque')),
         'hallazgos': m.find_section(secs, 'Hallazgos').strip(), 'contradicciones': m.find_section(secs, 'Contradicciones').strip(),
         'senales': m.find_section(secs, 'Senales', 'Señales').strip(), 'preguntas': m.find_section(secs, 'Preguntas').strip()}
    return d

def item(c, con_resp=False):
    s = f'- **{c["cod"]} {c["crit"]}** — {c["punt"]}'
    if c['respaldo'] and m._norm(c['respaldo']) not in ('documentado', 'informativo'): s += f' · *{c["respaldo"]}*'
    if con_resp and c['resp']: s += f'. Respuesta del vendor: {c["resp"]}'
    if c['just']: s += f'. {c["just"].rstrip(".")}.'
    if c['ev']: s += f' Evidencia: {c["ev"]}'
    return s

def bloque(titulo, filas, con_resp=False):
    punt = [c for c in filas if c['n'] is not None]; info = [c for c in filas if c['n'] is None]
    fort = [c for c in punt if c['n'] >= 4]; medio = [c for c in punt if 3 <= c['n'] < 4]; brecha = [c for c in punt if c['n'] < 3]
    L = [f'## {titulo}', '']
    L += [f'**Fortalezas (puntaje 4 o 5): {len(fort)} de {len(punt)} criterios.**', ''] + ([item(c, con_resp) for c in fort] or ['- Ninguna.']) + ['']
    L += [f'**Brechas (puntaje 0 a 2): {len(brecha)} de {len(punt)} criterios.**', ''] + ([item(c, con_resp) for c in brecha] or ['- Ninguna.']) + ['']
    if medio: L += [f'**En nivel intermedio (3):** ' + '; '.join(f'{c["cod"]} {c["crit"]} ({c["punt"]})' for c in medio) + '.', '']
    if info: L += ['**Datos informativos registrados:** ' + '; '.join(f'{c["cod"]} {c["crit"].rstrip(".")}: {c["resp"] or "—"}' for c in info) + '.', '']
    return L

def construir(d, hoy):
    L = [f'# Implementación por bloques — {d["nombre"]}', '', f'Fortalezas, brechas y contradicciones de la rúbrica corporativa de implementación, leídas por bloque. Fuente única: verificación de implementación del vendor (verif/IMPL.md, {d["fecha"] or "sin fecha"}) sobre sus documentos: ' + ('; '.join(d['docs']) if d['docs'] else '—') + f'. Informe generado el {hoy}; no recalifica.', '']
    if d['impls']: L += [f'Implementador(es) identificado(s): {m.nombres_en_texto(d["impls"])}', '']
    hdr, rows = d['resumen']
    if hdr:
        L += ['## Resultado por bloque', '', '| ' + ' | '.join(hdr) + ' |', '|' + '---|' * len(hdr)] + ['| ' + ' | '.join(r) + ' |' for r in rows] + ['']
    L += bloque('Bloque EI · Estrategia de implementación', d['EI'])
    L += bloque('Bloque F · Perfil del fabricante', d['F'], True)
    impls = []
    for c in d['I']:
        if c['impl'] and c['impl'] not in impls: impls.append(c['impl'])
    if len(impls) > 1:
        for nm in impls: L += bloque(f'Bloque I · Perfil del implementador: {nm}', [c for c in d['I'] if c['impl'] == nm], True)
    else:
        L += bloque('Bloque I · Perfil del implementador' + (f': {impls[0]}' if impls else ''), d['I'], True)
    for t, k in (('Contradicciones', 'contradicciones'), ('Señales de alerta', 'senales'), ('Hallazgos clave de la verificación', 'hallazgos'), ('Preguntas al vendor', 'preguntas')):
        if d[k]: L += [f'## {t}', '', m.nombres_en_texto(d[k]), '']
    return '\n'.join(L)

CSS = """body{font-family:Aptos,'Segoe UI',Arial,sans-serif;font-size:9.6pt;color:#171f2a;max-width:1000px;margin:0 auto;padding:24px;line-height:1.42}
h1{font-size:18pt;color:#00205b;margin:0 0 8pt} h2{font-size:13pt;color:#00529b;margin:16pt 0 6pt;border-bottom:2px solid #e3e6ec;padding-bottom:3pt} h3{font-size:11pt;color:#00205b;margin:10pt 0 4pt}
table{border-collapse:collapse;width:100%;font-size:8.6pt;margin:6pt 0 10pt} th{background:#003b70;color:#fff;padding:4pt 6pt;text-align:left} td{padding:3pt 6pt;border-bottom:1px solid #e3e6ec;vertical-align:top} td:first-child{font-weight:600;background:#f6f8fb}
li{margin:3pt 0} em{color:#9c5700;font-style:normal;font-weight:700} section.v{page-break-before:always} section.v:first-of-type{page-break-before:auto}
@media print{h2{page-break-after:avoid} table{page-break-inside:avoid} @page{size:A4;margin:14mm}}"""

def a_html(mds, titulo):
    cuerpo = ''.join(f'<section class="v">{m.md_to_html(x)}</section>' for x in mds)
    return f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{esc(titulo)}</title><style>{CSS}</style></head><body>{cuerpo}</body></html>'

def main():
    args = sys.argv[1:]; pdf = '--pdf' in args; pos = [a for a in args if not a.startswith('--')]
    if '--todos' in args: vendors = sorted(p.name for p in m.VENDORS.iterdir() if (p / 'verif' / 'IMPL.md').exists())
    elif pos: vendors = [pos[0]]
    else: sys.exit('Uso: python scripts/16_informe_bloques_impl.py <vendor> | --todos [--pdf]')
    hoy = datetime.date.today().strftime('%d-%m-%Y'); mds = []
    for v in vendors:
        d = leer(v)
        if not d: print(f'{v}: sin verif/IMPL.md, se omite'); continue
        md = construir(d, hoy); mds.append(md)
        out = m.VENDORS / v / 'informes' / '11_bloques_impl.md'; out.parent.mkdir(exist_ok=True); out.write_text(md, encoding='utf-8'); print(f'{out}')
        if pdf:
            h = out.with_suffix('.html'); h.write_text(a_html([md], f'Implementación por bloques · {d["nombre"]}'), encoding='utf-8'); m.a_pdf(h, h.with_suffix('.pdf'))
    if '--todos' in args and mds:
        out = m.VENDORS / 'INFORME_BLOQUES_IMPLEMENTACION.html'; out.write_text(a_html(mds, 'Implementación por bloques · todos los vendors'), encoding='utf-8'); print(f'HTML: {out}')
        if pdf: m.a_pdf(out, out.with_suffix('.pdf'))

if __name__ == '__main__':
    main()
