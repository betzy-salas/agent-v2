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
        mm = re.match(r'^\| \*\*(.+?)\*\* \((\d+) ítems?\) \| (🟢|🟡|🔴|⚪) \*\*(\w[\w ]*?)\*\* · ([\d.]+|—) \| (.*?) \|\s*$', l)
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
         f'- Vendors comparados ({len(V)}, orden alfabético, sin ranking): ' + ', '.join(m.nombre(d['vendor']) for d in V) + '.',
         f'- Fuente por vendor: su archivo 9_semaforo_T5.md (puntajes y colores copiados tal cual; calificación del Banco en la hoja T5). Fecha: {hoy}.',
         '- Niveles: 🟢 ≥ 70 · 🟡 50–69 · 🔴 < 50 (niveles de cumplimiento oficiales). Puntaje T5 = media de las calificaciones 0–4 sobre 4, en 0–100.',
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

# ----------------------------------------------------------------------------- presentación
CSS_SLIDES = """
.slide{page-break-after:always;break-after:page;min-height:160mm;display:flex;flex-direction:column;gap:12px;padding-top:6px}
.slide:last-child{page-break-after:auto} .slide h2{margin:.2rem 0 .2rem;font-size:1.7rem} .slide .sub{color:var(--ink-2);font-size:.92rem;margin:0;max-width:70ch}
.slide-kicker{font-family:var(--display);font-size:.7rem;text-transform:uppercase;letter-spacing:.12em;color:var(--accent);font-weight:800;margin:0}
.portada-t5{justify-content:center;gap:18px} .portada-t5 h1{font-size:2.8rem;margin:0} .portada-t5 .lead{font-size:1.05rem;max-width:72ch;color:var(--ink-2)}
.kpis-t5{display:grid;grid-template-columns:repeat(6,1fr);gap:10px} .kpi-t5{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 14px;border-top:6px solid var(--vc)} .kpi-t5 .v{font-family:var(--display);font-size:1.25rem;font-weight:800} .kpi-t5 .n{font-family:var(--display);font-size:1.9rem;font-weight:800;color:var(--lc);line-height:1.1} .kpi-t5 .l{font-size:.76rem;color:var(--ink-3)}
.heat{width:100%;border-collapse:separate;border-spacing:3px} .heat th{font-family:var(--display);font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-3);padding:4px 6px;text-align:center} .heat th:first-child{text-align:left} .heat td{padding:0} .heat td.cat{font-size:.8rem;font-weight:600;padding:0 8px 0 0;white-space:nowrap}
.heat .cell{display:block;text-align:center;border-radius:6px;padding:5px 4px;font-family:var(--mono);font-size:.8rem;font-weight:600;color:#fff} .heat tr.total td.cat{font-family:var(--display);font-weight:800;font-size:.9rem} .heat tr.total .cell{font-size:.95rem;padding:8px 4px;border-radius:8px}
.leyenda-sem{display:flex;gap:16px;align-items:center;font-size:.78rem;color:var(--ink-2)} .leyenda-sem i{display:inline-block;width:14px;height:14px;border-radius:4px;vertical-align:middle;margin-right:5px}
.vslide{display:grid;grid-template-columns:5fr 7fr;gap:18px;align-items:start} .vslide>*{min-width:0}
.bars{display:grid;gap:5px} .bars .r{display:grid;grid-template-columns:150px 1fr 44px;gap:8px;align-items:center;font-size:.76rem} .bars .r .t{height:12px;background:var(--track);border-radius:4px;overflow:hidden} .bars .r .t i{display:block;height:100%;border-radius:4px} .bars .r .n{font-family:var(--mono);text-align:right}
.coment{background:var(--panel);border:1px solid var(--line);border-left:5px solid var(--vc,var(--accent));border-radius:10px;padding:12px 16px;font-size:.9rem;line-height:1.5} .coment h4{margin:0 0 6px;font-size:.78rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-3)} .coment p{margin:0 0 8px} .coment p:last-child{margin:0}
.cat-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px 22px} .cat-item{font-size:.82rem;line-height:1.45;border-bottom:1px solid var(--line);padding-bottom:8px} .cat-item b{display:block;font-family:var(--display);margin-bottom:2px} .cat-item .dots{float:right;font-size:.74rem;letter-spacing:.04em}
.final{display:grid;grid-template-columns:6fr 6fr;gap:20px;align-items:start} .final>*{min-width:0}
.pend{display:grid;grid-template-columns:repeat(3,1fr);gap:12px} .pend .vbox{background:var(--panel);border:1px solid var(--line);border-top:6px solid var(--vc);border-radius:10px;padding:10px 14px;font-size:.8rem} .pend h4{margin:0 0 6px;font-size:1rem} .pend ul{margin:0;padding-left:1rem} .pend li{margin:.15rem 0} .pend .clamp2{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:.7rem;color:var(--ink-3)}
@media print{html{font-size:10.5px} .slide{min-height:160mm} .slide:first-of-type{min-height:150mm} .kpis-t5{grid-template-columns:repeat(6,1fr)} .vslide{grid-template-columns:5fr 7fr} .cat-grid{grid-template-columns:1fr 1fr} .pend{grid-template-columns:repeat(3,1fr)} .final{grid-template-columns:6fr 6fr}}
"""

def chip(color, pct, big=False):
    bg, _ = NIVEL_COLOR[color]; return f'<span class="cell" style="background:{bg}">{pct if pct is not None else "—"}</span>'

def svg_final(V):
    """Barras horizontales del puntaje T5 por vendor, color por nivel; etiquetas directas."""
    w, fila, top = 560, 40, 14; h = top + fila * len(V) + 26
    S = [f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Puntaje T5 por vendor"><style>text{{font-family:Source Sans 3,sans-serif}}</style>']
    for x in (0, 25, 50, 70, 85, 100):
        px = 150 + x * 3.8; S.append(f'<line x1="{px}" y1="{top - 4}" x2="{px}" y2="{h - 22}" stroke="#e3e2de" stroke-width="1"/><text x="{px}" y="{h - 8}" font-size="10" text-anchor="middle" fill="#6b6f76">{x}</text>')
    for i, d in enumerate(V):
        y = top + i * fila; bg, _ = NIVEL_COLOR[color_de(d['pct'])]
        S.append(f'<text x="142" y="{y + 20}" font-size="13" font-weight="700" text-anchor="end" fill="#1b1b1b">{esc(m.nombre(d["vendor"]))}</text>')
        S.append(f'<rect x="150" y="{y + 6}" width="{d["pct"] * 3.8:.1f}" height="22" rx="5" fill="{bg}"/>')
        S.append(f'<text x="{150 + d["pct"] * 3.8 + 8:.1f}" y="{y + 21}" font-size="12" font-family="JetBrains Mono,monospace" fill="#1b1b1b">{d["pct"]} · {esc(d["nivel"])}</text>')
    return ''.join(S) + '</svg>'

def construir_presentacion(V, base, hoy):
    por_cat, por_vendor, final = leer_comentarios(base)
    cats = []
    for d in V:
        for c in d['cats']:
            if c['cat'] not in cats: cats.append(c['cat'])
    for i, d in enumerate(V): d['_i'] = i
    H = [m.cabecera_doc('Presentación T5', hoy, extra_css=CSS_SLIDES, sub='Capacidades de desarrollo (T5) · ')]
    # 1 portada
    H.append('<section class="slide portada-t5"><p class="slide-kicker">Selección de core bancario · Hoja T5</p><h1>Capacidades de desarrollo: resultados por categoría y por vendor</h1><p class="lead">Puntaje de cada una de las categorías de la hoja T5 para los seis vendors, según la calificación del Banco, con el resultado final de la dimensión y comentarios por categoría y por vendor. Sin ranking: los vendors aparecen en orden alfabético.</p><div class="kpis-t5">'
             + ''.join(f'<div class="kpi-t5" style="--vc:{m.vcolor(d["_i"])};--lc:{NIVEL_COLOR[color_de(d["pct"])][1]}"><div class="v">{esc(m.nombre(d["vendor"]))}</div><div class="n">{d["pct"]}</div><div class="l">{esc(d["nivel"])}</div></div>' for d in V) + '</div></section>')
    # 2 cómo leer
    H.append('<section class="slide"><p class="slide-kicker">Cómo leer</p><h2>Qué mide cada número</h2><div class="grid2"><div class="coment"><h4>Fuente y puntaje</h4><p>La fuente es la calificación del Banco en la hoja T5 de la matriz técnica de cada vendor (escala 0–4 por ítem: Completamente Cubierto 4, Modificación Menor 3, Modificación Mayor 2, Parcialmente Cubierto 1, No Cubierto 0). Nada se recalifica.</p><p>El puntaje de una categoría es la media de las calificaciones de sus ítems sobre 4, en escala 0–100. El puntaje T5 del vendor es la misma media sobre todos sus ítems.</p></div><div class="coment"><h4>Colores y niveles</h4><p><span class="leyenda-sem"><span><i style="background:#1baf7a"></i>Verde ≥ 70: cumple o cumple plenamente (≥ 85)</span></span><span class="leyenda-sem"><span><i style="background:#eda100"></i>Amarillo 50–69: parcial</span></span><span class="leyenda-sem"><span><i style="background:#e34948"></i>Rojo &lt; 50: no cumple</span></span></p><p>Son los niveles de cumplimiento oficiales del proceso. Las ' + str(len(cats)) + ' categorías son las de la hoja T5; los comentarios se escriben solo a partir de lo que dicen la matriz y los semáforos de cada vendor, sin añadir información externa.</p></div></div></section>')
    # 3 mapa de calor
    H.append('<section class="slide"><p class="slide-kicker">Categorías × vendors</p><h2>Puntaje por categoría</h2><p class="sub">Cada celda es el puntaje 0–100 de la categoría para ese vendor; el color es su nivel. La última fila es el puntaje T5 del vendor.</p><table class="heat"><thead><tr><th>Categoría</th>' + ''.join(f'<th>{esc(m.nombre(d["vendor"]))}</th>' for d in V) + '</tr></thead><tbody>')
    for cat in cats:
        H.append(f'<tr><td class="cat">{esc(cat)}</td>' + ''.join((lambda c: f'<td>{chip(c["color"], c["pct"])}</td>' if c else '<td><span class="cell" style="background:#c9c9c6">—</span></td>')(next((x for x in d['cats'] if x['cat'] == cat), None)) for d in V) + '</tr>')
    H.append('<tr class="total"><td class="cat">Puntaje T5</td>' + ''.join(f'<td>{chip(color_de(d["pct"]), d["pct"])}</td>' for d in V) + '</tr></tbody></table><div class="leyenda-sem"><span><i style="background:#1baf7a"></i>≥ 70</span><span><i style="background:#eda100"></i>50–69</span><span><i style="background:#e34948"></i>&lt; 50</span></div></section>')
    # 4 una diapositiva por vendor
    for d in V:
        col = m.vcolor(d['_i']); n = {k: sum(1 for c in d['cats'] if c['color'] == k) for k in ('VERDE', 'AMARILLO', 'ROJO')}
        barras = ''.join(f'<div class="r"><span>{esc(c["cat"])}</span><span class="t"><i style="width:{c["pct"] or 0}%;background:{NIVEL_COLOR[c["color"]][0]}"></i></span><span class="n">{c["pct"]}</span></div>' for c in sorted(d['cats'], key=lambda x: -(x['pct'] or 0)))
        com = por_vendor.get(m.nombre(d['vendor'])) or por_vendor.get(d['vendor']) or ''
        H.append(f'<section class="slide"><p class="slide-kicker">Vendor</p><h2 style="border-top:6px solid {col};padding-top:8px">{esc(m.nombre(d["vendor"]))} · {d["pct"]} / 100 · {esc(d["nivel"])}</h2><p class="sub">{n["VERDE"]} categorías en verde · {n["AMARILLO"]} en amarillo · {n["ROJO"]} en rojo · {d["items"] or "—"} ítems calificados.</p><div class="vslide"><div><div class="bars">{barras}</div></div><div>'
                 + (f'<div class="coment" style="--vc:{col}"><h4>Comentario</h4>' + m.md_to_html(com) + '</div>' if com else '')
                 + (f'<div class="coment" style="--vc:{col};margin-top:10px"><h4>Resumen del semáforo</h4>' + m.md_to_html(d["resumen"]) + '</div>' if d['resumen'] else '')
                 + (f'<p class="small" style="margin-top:8px">Indispensables calificados 1 o 0: {esc(d["indispensables"])}.</p>' if d['indispensables'] and d['indispensables'] != 'ninguno' else '') + '</div></div></section>')
    # 5 comentarios por categoría (dos diapositivas)
    if any(por_cat.get(c) for c in cats):
        mitad = (len(cats) + 1) // 2
        for k, grupo in enumerate((cats[:mitad], cats[mitad:]), 1):
            items = ''
            for cat in grupo:
                dots = ' '.join(f'{SIM[c["color"]]}' for d in V for c in d['cats'] if c['cat'] == cat)
                items += f'<div class="cat-item"><b>{esc(cat)} <span class="dots">{dots}</span></b>{m.inline(esc(por_cat.get(cat, "")))}</div>'
            H.append(f'<section class="slide"><p class="slide-kicker">Comentarios por categoría ({k} de 2)</p><h2>Dónde coinciden y dónde se separan los vendors</h2><p class="sub">Los puntos muestran el color de cada vendor en la categoría, en el orden de la tabla: ' + ' · '.join(esc(m.nombre(d["vendor"])) for d in V) + f'.</p><div class="cat-grid">{items}</div></section>')
    # 6 resultado final
    H.append('<section class="slide"><p class="slide-kicker">Resultado final</p><h2>Puntaje T5 de cada vendor</h2><div class="final"><div><div class="panel">' + svg_final(V) + '</div><table class="score-table" style="margin-top:10px"><thead><tr><th>Vendor</th><th>Puntaje</th><th>Nivel</th><th>🟢</th><th>🟡</th><th>🔴</th><th>Calificaciones (4 · 3 · 2 · 1 · 0)</th></tr></thead><tbody>'
             + ''.join((lambda n: f'<tr style="--vc:{m.vcolor(d["_i"])}"><td>{esc(m.nombre(d["vendor"]))}</td><td class="num">{d["pct"]}</td><td>{esc(d["nivel"])}</td><td>{n["VERDE"]}</td><td>{n["AMARILLO"]}</td><td>{n["ROJO"]}</td><td class="small">{esc(dist_corta(d["distribucion"]))}</td></tr>')({k: sum(1 for c in d['cats'] if c['color'] == k) for k in ('VERDE', 'AMARILLO', 'ROJO')}) for d in V)
             + '</tbody></table></div><div>' + (f'<div class="coment"><h4>Comentario final</h4>{m.md_to_html(final)}</div>' if final else '<div class="coment"><h4>Comentario final</h4><p class="small">Pendiente: lo redacta el agente comparador-semaforo-t5.</p></div>') + '</div></div></section>')
    # 7 pendientes
    H.append('<section class="slide"><p class="slide-kicker">Lo pendiente</p><h2>Categorías en rojo y amarillo por vendor</h2><p class="sub">Lo que cada vendor dejó sin cubrir o sin sustento según la calificación del Banco; el detalle por ítem está en el semáforo de cada vendor.</p><div class="pend">'
             + ''.join(f'<div class="vbox" style="--vc:{m.vcolor(d["_i"])}"><h4>{esc(m.nombre(d["vendor"]))}</h4><ul>' + (''.join(f'<li>{SIM[c["color"]]} {esc(c["cat"])} · {c["pct"]}' + '</li>' for c in sorted([c for c in d['cats'] if c['color'] in ('ROJO', 'AMARILLO')], key=lambda x: x['pct'] or 0)) or '<li>Ninguna categoría en rojo ni amarillo.</li>') + '</ul></div>' for d in V) + '</div></section>')
    H.append(f'<footer>Presentación generada el {hoy} a partir de los semáforos T5 de cada vendor (calificación del Banco en la hoja T5). Sin ranking ni recomendación.</footer></div></body></html>')
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
