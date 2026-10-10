#!/usr/bin/env python3
"""Presentación de la hoja T5 (Capacidades de desarrollo): puntaje por categoría de cada vendor, resultado final y comentarios.

Dos pasos sobre una carpeta base (por defecto vendors/, o una carpeta aparte con --base, p. ej. presentacion_t5/):
  1) python scripts/10_presentacion_t5.py [--base carpeta]
     Lee el semáforo de cada vendor (<base>/<vendor>/9_semaforo_T5.md, o vendors/<vendor>/informes/9_semaforo_T5.md) y
     escribe <base>/COMPARATIVO_SEMAFORO_T5.md: tablas categorías × vendors y resultado final (copiadas, sin recalcular) más
     marcadores para los comentarios, que redacta después el agente comparador-semaforo-t5. Si el comparativo ya existe,
     conserva los comentarios ya escritos.
  2) python scripts/10_presentacion_t5.py [--base carpeta] --pdf
     Genera <base>/PRESENTACION_T5.html (diapositivas apaisadas, mismo diseño de los informes) y el PDF.
Sin ranking: los vendors van en orden alfabético. La fuente de todos los puntajes es la calificación del Banco en la hoja T5.
"""
import datetime, html, importlib.util, re, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parent
spec = importlib.util.spec_from_file_location('informe07', AQUI / '07_informe_implementacion.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

NIVEL_COLOR = {'VERDE': ('#1baf7a', '#0b6b48'), 'AMARILLO': ('#eda100', '#7a5200'), 'ROJO': ('#e34948', '#8f1f1f'), 'SIN CALIFICAR': ('#c9c9c6', '#555')}
SIM = {'VERDE': '🟢', 'AMARILLO': '🟡', 'ROJO': '🔴', 'SIN CALIFICAR': '⚪'}
def nivel_de(pct): return 'Cumple plenamente' if pct >= 85 else 'Cumple' if pct >= 70 else 'Parcial' if pct >= 50 else 'No cumple'
def color_de(pct): return 'VERDE' if pct >= 70 else 'AMARILLO' if pct >= 50 else 'ROJO'
def esc(t): return html.escape(str(t or ''))
def codigos(t): return re.findall(r'E\d+', t or '')
def dist_corta(t): return re.sub(r' × [^()]*\((\d)\)', r' × \1', t or '')

# ----------------------------------------------------------------------------- lectura de los semáforos
def leer_semaforo(ruta, vendor):
    t = m.leer_md(ruta); d = {'vendor': vendor, 'ruta': ruta, 'cats': [], 'resumen': '', 'conclusiones': {}, 'sustentos': {}}
    mm = re.search(r'Puntaje T5 de \S+: \*\*([\d.]+) / 100\*\*.*?nivel \*\*([^*]+)\*\*', t)
    d['pct'] = float(mm.group(1)) if mm else None; d['nivel'] = mm.group(2).strip() if mm else '—'
    mm = re.search(r'- Ítems: (\d+) · Categorías: (\d+)', t); d['items'] = int(mm.group(1)) if mm else None
    mm = re.search(r'- Distribución de calificaciones: (.+)', t); d['distribucion'] = mm.group(1).strip().rstrip('.') if mm else ''
    mm = re.search(r'Ítems de criticidad Indispensable calificados 1 o 0: (.+)', t); d['indispensables'] = mm.group(1).strip().rstrip('.') if mm else ''
    mm = re.search(r'\*\*Resumen ejecutivo\*\*\n\n(?!<!--)(.+?)\n\n## ', t, re.S); d['resumen'] = mm.group(1).strip() if mm else ''
    bloque = t[t.find('## Semáforo por categoría'):t.find('## Sustento por categoría')]
    for l in bloque.split('\n'):
        mm = re.match(r'^\|\s*\*\*(.+?)\*\*\s*\((\d+) ítems?\)\s*\|\s*(🟢|🟡|🔴|⚪)\s*\*\*([^*]+?)\*\*\s*·\s*([\d.]+|—)\s*\|\s*(.*?)\s*\|\s*$', l)
        if mm:
            concl = re.sub(r'<!-- conclusion: .*? -->', '', mm.group(6)).strip()
            if 'Texto automático' in concl: concl = ''
            d['cats'].append({'cat': mm.group(1), 'n': int(mm.group(2)), 'color': mm.group(4), 'pct': float(mm.group(5)) if mm.group(5) != '—' else None})
            d['conclusiones'][mm.group(1)] = concl
    for mm in re.finditer(r'^### (.+?) — .*?\n(?:.*?\n)*?\*\*Sustento\*\*\n\n(?!<!--)(.+?)\n\n\*\*Ítems', t, re.M):
        d['sustentos'][mm.group(1)] = mm.group(2).strip()
    return d

def cargar(base):
    V = []
    for p in sorted(base.iterdir()):
        if not p.is_dir(): continue
        f = p / '9_semaforo_T5.md' if (p / '9_semaforo_T5.md').exists() else p / 'informes' / '9_semaforo_T5.md'
        if f.exists():
            d = leer_semaforo(f, p.name)
            if d['cats']: V.append(d)
    return V

# ----------------------------------------------------------------------------- comparativo (tablas + marcadores)
def construir_comparativo(V, base, hoy):
    cats = []
    for d in V:
        for c in d['cats']:
            if c['cat'] not in cats: cats.append(c['cat'])
    def celda(d, cat):
        c = next((x for x in d['cats'] if x['cat'] == cat), None)
        return f'{SIM[c["color"]]} {c["pct"]}' if c and c["pct"] is not None else '—'
    L = ['# Comparativo del semáforo T5 (Capacidades de desarrollo) por categoría', '', '## Cabecera', '',
         f'- Vendors comparados ({len(V)}, orden alfabético en las tablas; el ranking por puntaje T5 va en la presentación): ' + ', '.join(m.nombre(d['vendor']) for d in V) + '.',
         f'- Fuente por vendor: su archivo 9_semaforo_T5.md (puntajes y colores copiados tal cual; calificación del Banco en la hoja T5). Fecha: {hoy}.',
         '- Niveles: 🟢 ≥ 70 · 🟡 50–69 · 🔴 < 50 (niveles de cumplimiento oficiales). Puntaje T5 = media de las calificaciones 0–4 ponderada por criticidad (Indispensable 3, Deseable 1), sobre 4, en 0–100.',
         '', '## Tabla categorías × vendors', '',
         '| Categoría | ' + ' | '.join(m.nombre(d['vendor']) for d in V) + ' |', '|---|' + '---|' * len(V)]
    for cat in cats: L.append(f'| {cat} | ' + ' | '.join(celda(d, cat) for d in V) + ' |')
    L += ['', '## Resultado final', '', '| Vendor | Puntaje T5 | Nivel | 🟢 | 🟡 | 🔴 | Ítems |', '|---|---:|---|---:|---:|---:|---:|']
    for d in V:
        n = {k: sum(1 for c in d['cats'] if c['color'] == k) for k in ('VERDE', 'AMARILLO', 'ROJO')}
        L.append(f'| {m.nombre(d["vendor"])} | {d["pct"]} | {d["nivel"]} | {n["VERDE"]} | {n["AMARILLO"]} | {n["ROJO"]} | {d["items"] or "—"} |')
    L += ['', '## Comentario por categoría', '', 'Un párrafo por categoría (lo redacta comparador-semaforo-t5 solo a partir de las conclusiones de cada vendor): en qué coinciden, en qué se separan y qué queda sin sustento en varios.', '']
    for cat in cats: L += [f'### {cat}', '', f'<!-- comentario-categoria: {cat} -->', '']
    L += ['## Comentario por vendor', '', 'Un párrafo por vendor con su lectura global de T5 (qué sostiene su resultado y qué lo resta), a partir de su resumen ejecutivo y sus conclusiones.', '']
    for d in V: L += [f'### {m.nombre(d["vendor"])}', '', f'<!-- comentario-vendor: {d["vendor"]} -->', '']
    L += ['## Comentario final', '', '<!-- comentario-final -->', '', '## Pendientes por vendor', '', 'Categorías en 🔴 y 🟡 de cada vendor, con su puntaje (lista automática).', '']
    for d in V:
        pend = [c for c in d['cats'] if c['color'] in ('ROJO', 'AMARILLO')]
        L.append(f'- **{m.nombre(d["vendor"])}**: ' + ('; '.join(f'{SIM[c["color"]]} {c["cat"]} ({c["pct"]})' for c in sorted(pend, key=lambda x: x['pct'] or 0)) if pend else 'ninguna categoría en 🔴 ni 🟡') + '.')
    L += ['', '## Nota', '', 'Generado por scripts/10_presentacion_t5.py. Sin ranking ni recomendación; los comentarios no cambian ningún puntaje.']
    texto = '\n'.join(L) + '\n'
    out = base / 'COMPARATIVO_SEMAFORO_T5.md'
    if out.exists():
        prev = out.read_text(encoding='utf-8-sig'); conservados = 0
        for cat in cats:
            mm = re.search(r'^### ' + re.escape(cat) + r'\n\n(?!<!--)(.+?)\n\n(?=###|## )', prev, re.S | re.M)
            if mm: texto = texto.replace(f'<!-- comentario-categoria: {cat} -->', mm.group(1).strip(), 1); conservados += 1
        for d in V:
            mm = re.search(r'^### ' + re.escape(m.nombre(d['vendor'])) + r'\n\n(?!<!--)(.+?)\n\n(?=###|## )', prev[prev.find('## Comentario por vendor'):], re.S | re.M)
            if mm: texto = texto.replace(f'<!-- comentario-vendor: {d["vendor"]} -->', mm.group(1).strip(), 1); conservados += 1
        mm = re.search(r'## Comentario final\n\n(?!<!--)(.+?)\n\n## ', prev, re.S)
        if mm: texto = texto.replace('<!-- comentario-final -->', mm.group(1).strip(), 1); conservados += 1
        if conservados: print(f'(se conservaron {conservados} comentarios ya redactados)')
    out.write_text(texto, encoding='utf-8'); return out, cats

def _secciones_h3(bloque):
    """{título: cuerpo} de un bloque Markdown con encabezados ###; ignora cuerpos que sigan siendo marcadores."""
    out = {}
    for parte in re.split(r'^### ', bloque, flags=re.M)[1:]:
        titulo, _, cuerpo = parte.partition('\n'); cuerpo = cuerpo.strip()
        if cuerpo and not cuerpo.startswith('<!--'): out[titulo.strip()] = cuerpo
    return out

def leer_comentarios(base):
    f = base / 'COMPARATIVO_SEMAFORO_T5.md'
    if not f.exists(): return {}, {}, ''
    t = m.leer_md(f)
    por_cat = _secciones_h3(t[t.find('## Comentario por categoría'):t.find('## Comentario por vendor')])
    por_vendor = _secciones_h3(t[t.find('## Comentario por vendor'):t.find('## Comentario final')])
    mm = re.search(r'## Comentario final\n\n(?!<!--)(.+?)\n\n## ', t, re.S); final = mm.group(1).strip() if mm else ''
    return por_cat, por_vendor, final

# ----------------------------------------------------------------------------- lectura de fichas y anexos
EVALS = [(4, 'Completamente Cubierto'), (3, 'Modificación Menor'), (2, 'Modificación Mayor'), (1, 'Parcialmente Cubierto'), (0, 'No Cubierto')]
EVAL_COLOR = {4: '#1baf7a', 3: '#5fcf9f', 2: '#eda100', 1: '#f0875f', 0: '#e34948'}

def distribucion_items(ruta):
    """{categoría: {va: n}} y total, leídos del anexo de ítems del semáforo (calificación del Banco tal como está en la matriz)."""
    t = m.leer_md(ruta); por_cat = {}; cat = None
    for l in t.split('\n'):
        mm = re.match(r'^### (.+?) — ', l)
        if mm: cat = mm.group(1); por_cat.setdefault(cat, {}); continue
        mm = re.match(r'^\| (E\d+) \| [^|]* \| [^|(]*\((\d)\) \|', l)
        if mm and cat: por_cat[cat][int(mm.group(2))] = por_cat[cat].get(int(mm.group(2)), 0) + 1; continue
        mm = re.match(r'^\d+ ítems? .*calificaciones del Banco: (.+)$', l)   # semáforo sin anexo por ítem: «2 × (4) · 1 × (3)»
        if mm and cat and not por_cat[cat]:
            for n, va in re.findall(r'(\d+) × \((\d)\)', mm.group(1)): por_cat[cat][int(va)] = int(n)
    total = {}
    for d in por_cat.values():
        for k, n in d.items(): total[k] = total.get(k, 0) + n
    return por_cat, total

def leer_ficha(ruta):
    """Secciones de 10_ficha_T5.md: lectura, listas de viñetas y tabla por categoría."""
    if not ruta.exists(): return None
    t = m.leer_md(ruta); secs = {}
    for parte in re.split(r'^## ', t, flags=re.M)[1:]:
        titulo, _, cuerpo = parte.partition('\n'); secs[m._norm(titulo.strip())] = cuerpo.strip()
    def vinetas(nombre):
        b = secs.get(m._norm(nombre), '')
        return [re.sub(r'^\s*[-*]\s+', '', l).strip() for l in b.split('\n') if re.match(r'^\s*[-*]\s+', l)]
    tabla = {}
    for l in secs.get('resumen por categoria', '').split('\n'):
        c = [x.strip() for x in l.strip().strip('|').split('|')] if l.strip().startswith('|') else []
        if len(c) >= 4 and c[0] not in ('Categoría', '') and not c[0].startswith('-'): tabla[c[0]] = (c[2], c[3])
    return {'lectura': secs.get('lectura general', ''), 'fortalezas': vinetas('Fortalezas'), 'debilidades': vinetas('Debilidades'), 'pendientes': vinetas('Pendientes'),
            'contradicciones': vinetas('Contradicciones'), 'sin_sustento': vinetas('Declarado sin sustento'), 'tabla': tabla, 'cabecera': secs.get('cabecera', '')}

def vineta_html(v, n=None):
    """«**título**: texto. Fuente: … Confianza: …» → html con título en negrita y fuente atenuada."""
    v = v.strip(); mm = re.match(r'^\*\*(.+?)\*\*\s*:?\s*(.*)$', v, re.S)
    titulo, resto = (mm.group(1), mm.group(2)) if mm else ('', v)
    partes = re.split(r'\s(?=(?:Fuente|Confianza|Impacto|Ítems?)\s*:)', resto)
    cuerpo = partes[0].strip(); meta = ' · '.join(p.strip().rstrip('.') for p in partes[1:])
    return f'<li>{("<b>" + esc(titulo) + "</b> " if titulo else "")}{m.inline(esc(cuerpo))}' + (f'<span class="fuente">{esc(meta)}</span>' if meta else '') + '</li>'

# ----------------------------------------------------------------------------- presentación
CSS_SLIDES = """
.slide{page-break-after:always;break-after:page;min-height:160mm;display:flex;flex-direction:column;gap:10px;padding-top:4px} .slide:last-of-type{page-break-after:auto;break-after:auto;min-height:0}
.slide h2{margin:.2rem 0 .1rem;font-size:1.6rem} .slide .sub{color:var(--ink-2);font-size:.9rem;margin:0;max-width:78ch}
.slide-kicker{font-family:var(--display);font-size:.68rem;text-transform:uppercase;letter-spacing:.12em;color:var(--accent);font-weight:800;margin:0}
.portada-t5{gap:18px;justify-content:center} .portada-t5 h1{font-size:2.3rem;margin:0;max-width:30ch} .portada-t5 .lead{font-size:.98rem;max-width:80ch;color:var(--ink-2);margin:0}
.rank{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-top:6px} .rk{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px 16px 16px;border-top:7px solid var(--vc);position:relative;min-width:0}
.rk .pos{position:absolute;top:10px;right:12px;font-family:var(--display);font-size:.7rem;font-weight:800;color:var(--ink-3);letter-spacing:.08em} .rk .v{font-family:var(--display);font-size:1.05rem;font-weight:800;line-height:1.15;padding-right:28px} .rk .n{font-family:var(--display);font-size:3rem;font-weight:800;color:var(--lc);line-height:1.05;margin-top:6px} .rk .l{font-size:.78rem;color:var(--ink-2);margin-top:2px} .rk .t{height:8px;background:var(--track);border-radius:4px;margin-top:10px;overflow:hidden} .rk .t i{display:block;height:100%;background:var(--lc)} .rk .sem{font-size:.72rem;color:var(--ink-3);margin-top:8px}
.heat{width:100%;border-collapse:separate;border-spacing:3px} .heat th{font-family:var(--display);font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-3);padding:4px 6px;text-align:center} .heat th:first-child{text-align:left} .heat td{padding:0} .heat td.cat{font-size:.8rem;font-weight:600;padding:0 8px 0 0;white-space:nowrap}
.heat .cell{display:block;text-align:center;border-radius:6px;padding:5px 4px;font-family:var(--mono);font-size:.8rem;font-weight:600;color:#fff} .heat tr.total td.cat{font-family:var(--display);font-weight:800;font-size:.9rem} .heat tr.total .cell{font-size:.95rem;padding:8px 4px;border-radius:8px}
.leyenda-sem{display:flex;gap:16px;align-items:center;font-size:.78rem;color:var(--ink-2);flex-wrap:wrap} .leyenda-sem i{display:inline-block;width:14px;height:14px;border-radius:4px;vertical-align:middle;margin-right:5px}
.vhead2{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;border-top:7px solid var(--vc);padding-top:8px} .vhead2 h2{margin:0} .vhead2 .big{font-family:var(--display);font-size:1.9rem;font-weight:800;color:var(--lc)} .vhead2 .niv{font-size:.95rem;color:var(--ink-2)} .vhead2 .pos{font-family:var(--display);font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);margin-left:auto}
.va-grid{display:grid;grid-template-columns:2fr 5fr;gap:14px;align-items:start} .va-grid>*{min-width:0}
.stack{display:flex;height:22px;border-radius:7px;overflow:hidden;background:var(--track)} .stack i{display:block;height:100%} .stack-leg{display:grid;grid-template-columns:1fr 1fr;gap:3px 10px;font-size:.74rem;margin-top:8px} .stack-leg b{font-family:var(--mono);font-weight:600} .stack-leg s{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px;vertical-align:middle;text-decoration:none}
.coment{background:var(--panel);border:1px solid var(--line);border-left:5px solid var(--vc,var(--accent));border-radius:10px;padding:10px 14px;font-size:.84rem;line-height:1.45} .coment h4{margin:0 0 5px;font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-3)} .coment p{margin:0 0 6px} .coment p:last-child{margin:0}
table.cat-t{width:100%;border-collapse:collapse;font-size:.74rem} table.cat-t th{font-family:var(--display);font-size:.62rem;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-3);text-align:left;padding:3px 6px;border-bottom:2px solid var(--line)} table.cat-t td{padding:3px 6px;border-bottom:1px solid var(--line);vertical-align:top;line-height:1.35} table.cat-t td.c{white-space:nowrap;font-weight:600} table.cat-t .pill{display:inline-block;min-width:44px;text-align:center;border-radius:6px;padding:2px 6px;color:#fff;font-family:var(--mono);font-size:.72rem;font-weight:600} table.cat-t .mini{font-family:var(--mono);font-size:.68rem;color:var(--ink-3);white-space:nowrap} table.cat-t td.txt{color:var(--ink-2)}
.ficha{display:grid;grid-template-columns:1fr 1fr;gap:9px} .ficha>*{min-width:0} .fbox{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:8px 12px;border-top:5px solid var(--bc)} .fbox h4{margin:0 0 6px;font-size:.74rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-3)} .fbox ul{margin:0;padding-left:1rem;font-size:.76rem;line-height:1.4} .fbox li{margin:.18rem 0} .fbox .fuente{display:block;color:var(--ink-3);font-size:.62rem;margin-top:1px} .fbox.wide ul{columns:2;column-gap:20px} .fbox.wide li{break-inside:avoid} .fbox.wide{grid-column:1 / -1}
.cat-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px 22px} .cat-item{font-size:.8rem;line-height:1.42;border-bottom:1px solid var(--line);padding-bottom:7px} .cat-item b{display:block;font-family:var(--display);margin-bottom:2px} .cat-item .dots{float:right;font-size:.72rem;letter-spacing:.04em}
.final{display:grid;grid-template-columns:6fr 6fr;gap:20px;align-items:start} .final>*{min-width:0}
.pend{display:grid;grid-template-columns:repeat(3,1fr);gap:12px} .pend .vbox{background:var(--panel);border:1px solid var(--line);border-top:6px solid var(--vc);border-radius:10px;padding:10px 14px;font-size:.78rem} .pend h4{margin:0 0 6px;font-size:1rem} .pend ul{margin:0;padding-left:1rem} .pend li{margin:.15rem 0}
@media print{html{font-size:13px} table.cat-t{font-size:.67rem} table.cat-t td{padding:2px 5px} .coment{font-size:.8rem} .pend .vbox{font-size:.74rem;padding:8px 12px} .cat-item{font-size:.82rem} .slide{min-height:160mm} .slide.flow{min-height:0;display:block} .slide.flow .ficha{margin-top:10px} .fbox{page-break-inside:auto} .fbox li{page-break-inside:avoid} .slide:first-of-type{min-height:150mm} .slide:last-of-type{min-height:0} .rank{grid-template-columns:repeat(6,1fr)} .va-grid{grid-template-columns:2fr 5fr} .ficha{grid-template-columns:1fr 1fr} .cat-grid{grid-template-columns:1fr 1fr} .pend{grid-template-columns:repeat(3,1fr)} .final{grid-template-columns:6fr 6fr} .fbox,.coment,tr{page-break-inside:avoid}}
"""

def chip(color, pct): bg, _ = NIVEL_COLOR[color]; return f'<span class="cell" style="background:{bg}">{pct if pct is not None else "—"}</span>'

def svg_final(V):
    w, fila, top = 640, 40, 14; h = top + fila * len(V) + 26
    S = [f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Puntaje T5 por vendor"><style>text{{font-family:Source Sans 3,sans-serif}}</style>']
    for x in (0, 25, 50, 70, 85, 100):
        px = 150 + x * 3.3; S.append(f'<line x1="{px}" y1="{top - 4}" x2="{px}" y2="{h - 22}" stroke="#e3e2de" stroke-width="1"/><text x="{px}" y="{h - 8}" font-size="10" text-anchor="middle" fill="#6b6f76">{x}</text>')
    for i, d in enumerate(V):
        y = top + i * fila; bg, _ = NIVEL_COLOR[color_de(d['pct'])]
        S.append(f'<text x="142" y="{y + 20}" font-size="13" font-weight="700" text-anchor="end" fill="#1b1b1b">{esc(m.nombre(d["vendor"]))}</text>')
        S.append(f'<rect x="150" y="{y + 6}" width="{d["pct"] * 3.3:.1f}" height="22" rx="5" fill="{bg}"/>')
        S.append(f'<text x="{150 + d["pct"] * 3.3 + 8:.1f}" y="{y + 21}" font-size="12" font-family="JetBrains Mono,monospace" fill="#1b1b1b">{d["pct"]} · {esc(d["nivel"])}</text>')
    return ''.join(S) + '</svg>'

def stack_html(dist):
    tot = sum(dist.values()) or 1
    barra = ''.join(f'<i style="width:{dist.get(k, 0) / tot * 100:.1f}%;background:{EVAL_COLOR[k]}" title="{n}"></i>' for k, n in EVALS if dist.get(k))
    leg = ''.join(f'<span><s style="background:{EVAL_COLOR[k]}"></s>{esc(n)} ({k}) <b>{dist.get(k, 0)}</b></span>' for k, n in EVALS)
    return f'<div class="stack">{barra}</div><div class="stack-leg">{leg}</div>'

def mini_dist(dist): return ' · '.join(f'{dist.get(k, 0)}' for k, _ in EVALS)

def construir_presentacion(V, base, hoy):
    por_cat, por_vendor, final = leer_comentarios(base)
    cats = []
    for d in V:
        for c in d['cats']:
            if c['cat'] not in cats: cats.append(c['cat'])
    for i, d in enumerate(V):
        d['_i'] = i; d['dist_cat'], d['dist'] = distribucion_items(d['ruta']); d['ficha'] = leer_ficha(d['ruta'].parent / '10_ficha_T5.md')
    orden = sorted(V, key=lambda d: -(d['pct'] or 0)); pos = {d['vendor']: k + 1 for k, d in enumerate(orden)}
    H = [m.cabecera_doc('Presentación T5', hoy, extra_css=CSS_SLIDES, sub='Capacidades de desarrollo (T5) · ').replace('sin ranking ni recomendación', 'ranking por puntaje T5 del Banco')]
    # 1 portada con ranking
    H.append('<section class="slide portada-t5"><p class="slide-kicker">Selección de core bancario · Hoja T5 · Capacidades de desarrollo</p><h1>Resultados de la evaluación de desarrollo de los seis vendors</h1><p class="lead">Ranking por puntaje T5 según la calificación del Banco (media de los ítems ponderada por criticidad), nivel de cumplimiento, categorías en verde, amarillo y rojo, y para cada vendor sus fortalezas, debilidades, pendientes y contradicciones con fuente.</p><div class="rank">'
             + ''.join((lambda n: f'<div class="rk" style="--vc:{m.vcolor(d["_i"])};--lc:{NIVEL_COLOR[color_de(d["pct"])][1]}"><span class="pos">#{k + 1}</span><div class="v">{esc(m.nombre(d["vendor"]))}</div><div class="n">{d["pct"]}</div><div class="l">{esc(d["nivel"])}</div><div class="t"><i style="width:{d["pct"]}%"></i></div><div class="sem">🟢 {n["VERDE"]} · 🟡 {n["AMARILLO"]} · 🔴 {n["ROJO"]} de {len(d["cats"])}</div></div>')({c: sum(1 for x in d['cats'] if x['color'] == c) for c in ('VERDE', 'AMARILLO', 'ROJO')}) for k, d in enumerate(orden)) + '</div>'
             + '<div class="leyenda-sem"><span><i style="background:#1baf7a"></i>Verde ≥ 70 (Cumple; ≥ 85 Cumple plenamente)</span><span><i style="background:#eda100"></i>Amarillo 50–69 (Parcial)</span><span><i style="background:#e34948"></i>Rojo &lt; 50 (No cumple)</span><span>Fuente: hoja T5 de la matriz técnica calificada por el Banco · ' + str(len(cats)) + ' categorías · 78–80 ítems por vendor</span></div></section>')
    # 2 cómo leer
    H.append('<section class="slide"><p class="slide-kicker">Cómo leer</p><h2>Qué mide cada número</h2><div class="grid2"><div class="coment"><h4>Fuente y puntaje</h4><p>La fuente es la calificación del Banco en la hoja T5 de la matriz técnica de cada vendor (0–4 por ítem: Completamente Cubierto 4, Modificación Menor 3, Modificación Mayor 2, Parcialmente Cubierto 1, No Cubierto 0). Nada se recalifica.</p><p>El puntaje de una categoría es la media de las calificaciones de sus ítems ponderada por criticidad (Indispensable 3, Deseable 1, como en el consolidado del Banco), sobre 4 y en escala 0–100. El puntaje T5 es la misma media sobre todos los ítems del vendor.</p></div><div class="coment"><h4>Colores, fichas y comentarios</h4><p>Verde ≥ 70, amarillo 50–69, rojo &lt; 50: son los niveles de cumplimiento oficiales del proceso.</p><p>Las fortalezas, debilidades, pendientes y contradicciones de cada vendor salen de su matriz (respuesta del proveedor y sustento del evaluador) y, cuando existe, de la verificación documental de T5 (veredictos, evidencia con documento y página, contradicciones). Cada punto nombra su ítem y su fuente; nada proviene de información externa.</p></div></div></section>')
    # 3 mapa de calor
    H.append('<section class="slide"><p class="slide-kicker">Categorías × vendors</p><h2>Puntaje por categoría</h2><p class="sub">Cada celda es el puntaje 0–100 de la categoría para ese vendor; el color es su nivel. Última fila: puntaje T5. Vendors en orden de ranking.</p><table class="heat"><thead><tr><th>Categoría</th>' + ''.join(f'<th>#{pos[d["vendor"]]} {esc(m.nombre(d["vendor"]))}</th>' for d in orden) + '</tr></thead><tbody>')
    for cat in cats:
        H.append(f'<tr><td class="cat">{esc(cat)}</td>' + ''.join((lambda c: f'<td>{chip(c["color"], c["pct"])}</td>' if c else '<td><span class="cell" style="background:#c9c9c6">—</span></td>')(next((x for x in d['cats'] if x['cat'] == cat), None)) for d in orden) + '</tr>')
    H.append('<tr class="total"><td class="cat">Puntaje T5</td>' + ''.join(f'<td>{chip(color_de(d["pct"]), d["pct"])}</td>' for d in orden) + '</tr></tbody></table></section>')
    # 4 dos diapositivas por vendor (en orden de ranking)
    for d in orden:
        col = m.vcolor(d['_i']); lc = NIVEL_COLOR[color_de(d['pct'])][1]; n = {k: sum(1 for c in d['cats'] if c['color'] == k) for k in ('VERDE', 'AMARILLO', 'ROJO')}
        f = d['ficha'] or {}; com = por_vendor.get(m.nombre(d['vendor'])) or por_vendor.get(d['vendor']) or ''
        head = f'<div class="vhead2" style="--vc:{col};--lc:{lc}"><h2>{esc(m.nombre(d["vendor"]))}</h2><span class="big">{d["pct"]}</span><span class="niv">{esc(d["nivel"])} · 🟢 {n["VERDE"]} · 🟡 {n["AMARILLO"]} · 🔴 {n["ROJO"]} de {len(d["cats"])} categorías · {sum(d["dist"].values())} ítems</span><span class="pos">Ranking #{pos[d["vendor"]]} de {len(V)}</span></div>'
        filas = ''
        for c in d['cats']:
            dist = d['dist_cat'].get(c['cat'], {}); dem, falta = (f.get('tabla') or {}).get(c['cat'], ('', ''))
            concl = d['conclusiones'].get(c['cat'], '')
            filas += f'<tr><td class="c">{esc(c["cat"])}</td><td><span class="pill" style="background:{NIVEL_COLOR[c["color"]][0]}">{c["pct"]}</span></td><td class="mini">{mini_dist(dist)}</td><td class="txt">{esc(dem) if dem else esc(concl)}</td><td class="txt">{esc(falta) if falta else ""}</td></tr>'
        lectura = f.get('lectura') or com or d['resumen']
        H.append(f'<section class="slide"><p class="slide-kicker">Vendor · resumen general y por categoría</p>{head}<div class="va-grid"><div><div class="coment" style="--vc:{col}"><h4>Calificaciones del Banco ({sum(d["dist"].values())} ítems)</h4>{stack_html(d["dist"])}</div>'
                 + (f'<div class="coment" style="--vc:{col};margin-top:10px"><h4>Lectura general</h4>{m.md_to_html(lectura)}</div>' if lectura else '') + '</div>'
                 + f'<div><table class="cat-t"><thead><tr><th>Categoría</th><th>Puntaje</th><th>4 · 3 · 2 · 1 · 0</th><th>Lo que demuestra</th><th>Lo que falta</th></tr></thead><tbody>{filas}</tbody></table></div></div></section>')
        if f:
            def caja(titulo, items, color, n_max, wide=False):
                its = items[:n_max]
                return f'<div class="fbox{" wide" if wide else ""}" style="--bc:{color}"><h4>{esc(titulo)}' + (f' ({len(items)})' if items else '') + '</h4>' + (f'<ul>{"".join(vineta_html(v) for v in its)}</ul>' if its else '<p class="small">—</p>') + '</div>'
            H.append(f'<section class="slide flow"><p class="slide-kicker">Vendor · fortalezas y debilidades</p>{head}<div class="ficha">'
                     + caja('Fortalezas', f['fortalezas'], '#1baf7a', 8) + caja('Debilidades', f['debilidades'], '#e34948', 8) + '</div></section>')
            H.append(f'<section class="slide flow"><p class="slide-kicker">Vendor · pendientes, contradicciones y declarado sin sustento</p>{head}<div class="ficha">'
                     + caja('Pendientes', f['pendientes'], '#eda100', 10) + caja('Contradicciones', f['contradicciones'], '#4a3aa7', 8)
                     + (caja('Declarado sin sustento', f['sin_sustento'], '#8a8f98', 8, wide=True) if f['sin_sustento'] else '') + '</div></section>')
    # 5 comentarios por categoría
    if any(por_cat.get(c) for c in cats):
        grupos = [cats[i:i + 6] for i in range(0, len(cats), 6)]
        for k, grupo in enumerate(grupos, 1):
            items = ''
            for cat in grupo:
                dots = ' '.join(f'{SIM[c["color"]]}' for d in orden for c in d['cats'] if c['cat'] == cat)
                items += f'<div class="cat-item"><b>{esc(cat)} <span class="dots">{dots}</span></b>{m.inline(esc(por_cat.get(cat, "")))}</div>'
            H.append(f'<section class="slide"><p class="slide-kicker">Comentarios por categoría ({k} de {len(grupos)})</p><h2>Dónde coinciden y dónde se separan los vendors</h2><p class="sub">Los puntos muestran el color de cada vendor en la categoría, en orden de ranking: ' + ' · '.join(f'#{pos[d["vendor"]]} {esc(m.nombre(d["vendor"]))}' for d in orden) + f'.</p><div class="cat-grid">{items}</div></section>')
    # 6 resultado final
    H.append('<section class="slide"><p class="slide-kicker">Resultado final</p><h2>Ranking por puntaje T5</h2><div class="final"><div><div class="panel">' + svg_final(orden) + '</div><table class="score-table" style="margin-top:10px"><thead><tr><th>#</th><th>Vendor</th><th>Puntaje</th><th>Nivel</th><th>🟢</th><th>🟡</th><th>🔴</th><th>Calificaciones 4 · 3 · 2 · 1 · 0</th></tr></thead><tbody>'
             + ''.join((lambda n: f'<tr style="--vc:{m.vcolor(d["_i"])}"><td>{pos[d["vendor"]]}</td><td>{esc(m.nombre(d["vendor"]))}</td><td class="num">{d["pct"]}</td><td>{esc(d["nivel"])}</td><td>{n["VERDE"]}</td><td>{n["AMARILLO"]}</td><td>{n["ROJO"]}</td><td class="small">{mini_dist(d["dist"])}</td></tr>')({k: sum(1 for c in d['cats'] if c['color'] == k) for k in ('VERDE', 'AMARILLO', 'ROJO')}) for d in orden)
             + '</tbody></table></div><div>' + (f'<div class="coment"><h4>Comentario final</h4>{m.md_to_html(final)}</div>' if final else '<div class="coment"><h4>Comentario final</h4><p class="small">Pendiente de redacción.</p></div>') + '</div></div></section>')
    # 7 pendientes
    H.append('<section class="slide"><p class="slide-kicker">Lo pendiente</p><h2>Categorías en rojo y amarillo por vendor</h2><p class="sub">Lo que cada vendor dejó sin cubrir o sin sustento según la calificación del Banco; el detalle por ítem está en el semáforo y la ficha de cada vendor.</p><div class="pend">'
             + ''.join(f'<div class="vbox" style="--vc:{m.vcolor(d["_i"])}"><h4>#{pos[d["vendor"]]} {esc(m.nombre(d["vendor"]))}</h4><ul>' + (''.join(f'<li>{SIM[c["color"]]} {esc(c["cat"])} · {c["pct"]}</li>' for c in sorted([c for c in d['cats'] if c['color'] in ('ROJO', 'AMARILLO')], key=lambda x: x['pct'] or 0)) or '<li>Ninguna categoría en rojo ni amarillo.</li>') + '</ul></div>' for d in orden) + '</div></section>')
    H.append(f'<footer>Presentación generada el {hoy} a partir de los semáforos y fichas T5 de cada vendor (calificación del Banco en la hoja T5; verificación documental cuando existe). Ranking por puntaje T5.</footer></div></body></html>')
    return '\n'.join(H)

def main():
    args = sys.argv[1:]; pdf = '--pdf' in args
    base = Path(args[args.index('--base') + 1]) if '--base' in args else RAIZ / 'vendors'
    if not base.is_absolute(): base = RAIZ / base
    V = cargar(base)
    if not V: sys.exit(f'No encontré ningún 9_semaforo_T5.md bajo {base}. Corre antes scripts/09_semaforo_t5.py por vendor.')
    hoy = datetime.date.today().strftime('%d-%m-%Y')
    if not pdf:
        out, cats = construir_comparativo(V, base, hoy)
        print(f'{out}\n{len(V)} vendors: ' + ', '.join(f'{m.nombre(d["vendor"])} {d["pct"]}' for d in V) + f' · {len(cats)} categorías. Ahora: agente comparador-semaforo-t5 para los comentarios; luego --pdf.')
    else:
        out = base / 'PRESENTACION_T5.html'; out.write_text(construir_presentacion(V, base, hoy), encoding='utf-8'); print(f'HTML: {out}')
        m.a_pdf(out, out.with_suffix('.pdf'))

if __name__ == '__main__':
    main()
