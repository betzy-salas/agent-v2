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
     Con --estilo coe genera PRESENTACION_T5_COE.html/.pdf: diapositivas 16:9 con el diseño del deck corporativo (barra azul,
     numerales naranja, pie «Datos elaborados por BCP para uso Interno»); si existen <base>/assets/logo.png y portada.jpg los usa en la portada.
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

# ----------------------------------------------------------------------------- estrategia de implementación (informes 7_, rúbrica IMPL y COMPARATIVO_IMPLEMENTACION.md ya existentes)
FICHA_IMPL = [('enfoque', 'Enfoque'), ('duración total', 'Duración total'), ('implementador', 'Implementador'), ('roles clave', 'Roles clave y dedicación'), ('migración', 'Migración de datos'),
              ('pruebas', 'Pruebas y PoC'), ('hypercare', 'Hypercare'), ('responsabilidades del banco', 'Responsabilidades del Banco'), ('modalidad comercial', 'Modalidad comercial')]
PILL = {'VERDE': ('#dcebd4', '#276221'), 'AMARILLO': ('#fbe4cc', '#9c5700'), 'ROJO': ('#f5cccc', '#b02a2a')}
def nivel_pct(p):
    """Color por nivel oficial sobre un porcentaje 0–100 (verde ≥ 70, amarillo 50–69, rojo < 50)."""
    return color_de(p) if p is not None else 'SIN CALIFICAR'
def color_0_5(n):
    try: n = float(n)
    except (TypeError, ValueError): return 'SIN CALIFICAR'
    return 'VERDE' if n >= 4 else 'AMARILLO' if n >= 3 else 'ROJO'

def _bloques_vendor_comparativo(body):
    """Sección de un vendor en COMPARATIVO_IMPLEMENTACION.md: {Fortalezas: [...], Debilidades: [...], Lo que deja al Banco: [...], Señales de alerta: [...], Veredicto en una frase: [...]}."""
    out = {}; cur = None
    for l in body.split('\n'):
        s = l.strip()
        if not s: continue
        if re.match(r'^[-*•]\s+', s):
            if cur is not None: out.setdefault(cur, []).append(re.sub(r'^[-*•]\s+', '', s))
        elif len(s) < 60 and not s.endswith('.'): cur = re.sub(r'^#+\s*', '', s).strip(': ')
    return out

def datos_implementacion(V):
    """Datos de implementación por vendor (cargar_vendor de 07: ficha, pros, contras, rúbrica EI/F/I) y generales (comparativo), con fuentes reales."""
    out = {'vendors': {}, 'general': None}; vd = []
    for d in V:
        x = m.cargar_vendor(d['vendor'])
        if x.get('ok'): vd.append(x); out['vendors'][d['vendor']] = x
    comp = RAIZ / 'vendors' / 'COMPARATIVO_IMPLEMENTACION.md'
    if not vd or not comp.exists(): return out
    md = m.leer_md(comp); secs = m.sections(md)
    g = {'titular': next((l.strip() for l in md.split('\n') if l.strip() and not l.startswith('#')), ''), 'resumen': m.first_table(m.find_section(secs, 'Tabla resumen')),
         'ei': m.first_table(m.find_section(secs, 'Tabla criterio')), 'diferencias': [], 'transversal': [], 'por_vendor': {}}
    g['diferencias'] = [re.sub(r'^[-*•]\s+', '', l.strip()) for l in m.find_section(secs, 'Criterios con mayor diferencia').split('\n') if re.match(r'^\s*[-*•]\s+', l)]
    items = []
    for l in m.find_section(secs, 'Comparación transversal', 'Comparacion transversal').split('\n'):
        if not l.strip(): continue
        if re.match(r'^\s*\d+[.)]\s+', l): items.append([re.sub(r'^\s*\d+[.)]\s+', '', l).strip(), []])
        elif items and re.match(r'^\s*[-*•]\s+', l): items[-1][1].append(re.sub(r'^\s*[-*•]\s+', '', l).strip())
        elif items: items[-1][0] += ' ' + l.strip()
    for texto, subs in items:
        reales = m.fuentes_reales(texto, vd)
        fuentes = ' · '.join(f'{v}: {c}' for v, c in reales) if reales else m.fuentes_legibles('; '.join(re.sub(r'^fuentes?\s*:\s*', '', x, flags=re.I).rstrip('.') for x in subs if re.match(r'^fuentes?\s*:', x, flags=re.I)))
        g['transversal'].append((m.nombres_en_texto(texto), fuentes))
    for lvl, t, b in secs:
        if lvl == 2:
            for d in V:
                if m._norm(m.nombre(t.strip())) == m._norm(m.nombre(d['vendor'])): g['por_vendor'][d['vendor']] = _bloques_vendor_comparativo(b)
    out['general'] = g; return out

def ficha_impl_filas(x):
    """Filas (etiqueta, qué propone, fuente, confianza) de la ficha resumen del informe 7_ en el orden de FICHA_IMPL."""
    out = []
    for clave, etiqueta in FICHA_IMPL:
        for k, val in (x.get('ficha') or {}).items():
            if m._norm(clave) in m._norm(k): out.append((etiqueta, val.get('que', ''), val.get('fuente', ''), val.get('conf', ''))); break
    return out

def datos_despliegue(V):
    """Cuadrícula modelos × plataformas por vendor: la misma de «Resumen por vendor: plataformas por modelo» del informe de comparativos
    (scripts/08_comparativos_pdf.py, hoja 4). Reutiliza MODELOS_ORDEN, PLATAFORMAS y marcas_nubes de 08 sobre el informe 8_modelo_despliegue.md
    de cada vendor (tabla «Modelos» cargada por cargar_vendor de 07). Devuelve ([(vendor, índice de color, [(modelo, clase chip, texto chip, {plataforma: estado}, [(otra nube, nombre corto, estado)])])], plataformas)."""
    spec8 = importlib.util.spec_from_file_location('p08', AQUI / '08_comparativos_pdf.py'); p08 = importlib.util.module_from_spec(spec8); spec8.loader.exec_module(p08)
    out = []
    for d in V:
        x = m.cargar_vendor(d['vendor'])
        lines = [l for l in str(x.get('desp_modelos', '')).split('\n') if l.strip().startswith('|')]
        hdr, rows = m.parse_table(lines) if lines else ([], [])
        if not hdr: continue
        col = {m._norm(h)[:6]: i for i, h in enumerate(hdr)}; i_of, i_nu, i_co = col.get('ofreci'), col.get('nubes '), col.get('condic')
        filas = []
        for clave, nombre_m in p08.MODELOS_ORDEN + p08.FILA_DECLARADA:
            r = next((r for r in rows if clave in m._norm(r[0])), None)
            if clave == 'declarad' and not r: continue
            marcas = p08.marcas_nubes(r[i_of], r[i_nu]) if r and i_of is not None and i_nu is not None else {}
            cls, corto = m.chip_modelo(r[i_of], r[i_co] if i_co is not None else '', r[i_nu] if i_nu is not None else '') if r else ('', '—')
            otras = p08.marcas_otras(r[i_of], r[i_nu]) if r and i_of is not None and i_nu is not None else []
            filas.append((nombre_m.split(' / ')[0], cls, corto, marcas, otras))
        out.append((d['vendor'], d.get('_i', 0), filas))
    return out, [pn for pn, _ in p08.PLATAFORMAS_GRID]

LEYENDA_NUBES = ('ofrecida al Banco para ese modelo', 'condicionada o solo compatibilidad declarada', 'la tiene, pero no la ofrece al Banco para ese modelo', 'no la asocia a ese modelo')
LEYENDA_CHIPS = (('si', 'Sí', 'ofrecido al Banco'), ('cond', 'Condicionado', 'con condiciones o solo compatibilidad declarada'), ('tiene', 'Tiene, no ofrece', 'lo tiene en su documentación (otros clientes, regiones o nubes), pero no lo ofrece al Banco'), ('no', 'No', 'excluido, sin evidencia de que lo tenga'), ('x', 'N/E', 'no lo especifica'), ('decl', 'Declaradas', 'fila con las plataformas que el vendor nombra en general, con cita, sin atarlas a un modelo'))
NOTA_NUBES = 'Otras = nubes o herramientas sin columna propia (Kubernetes, EKS/AKS/GKE, CCE, VMware, Alibaba, IBM Cloud…): negrita ofrecida, normal declarada o condicionada, gris no ofrecida. La fila «Nube privada» no lleva columna propia: el modelo ya la implica.'

# ----------------------------------------------------------------------------- estilo CoE (deck corporativo 16:9: barra azul, numerales naranja, pie «Datos elaborados por BCP para uso Interno»)
import base64, mimetypes
CSS_COE = """
@page{size:960pt 540pt;margin:0}
html{font-size:12.5px} body{margin:0;background:#fff;color:#171f2a;font-family:Aptos,"Segoe UI","Source Sans 3",Arial,sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.s{position:relative;width:960pt;min-height:540pt;page-break-after:always;break-after:page;box-sizing:border-box;padding:0;overflow:visible;background:#fff}
.s:last-of-type{page-break-after:auto;break-after:auto}
.bar{background:#003b70;color:#fff;height:46pt;display:flex;align-items:center;justify-content:space-between;padding:0 32pt 0 34pt}
.bar h2{margin:0;font-size:17pt;font-weight:800;letter-spacing:.01em} .bar .r{font-size:8pt;color:#dce8f6}
.body{padding:13pt 34pt 0}
.pie{position:absolute;left:0;right:0;bottom:0;height:28pt;background:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 32pt 0 34pt;font-size:6.8pt;color:#5f6b7a}
.pie .c{color:#5b9bd5;position:absolute;left:0;right:0;text-align:center;bottom:6pt} .pie .n{color:#00529b;font-weight:700;font-size:7.5pt}
.num{display:inline-flex;align-items:center;gap:10pt;font-weight:800;color:#ff6400;letter-spacing:.14em;text-transform:uppercase;font-size:10.5pt}
.num b{display:inline-flex;align-items:center;justify-content:center;width:26pt;height:26pt;border-radius:50%;background:#ff6400;color:#fff;font-size:11pt;letter-spacing:0}
.sec{padding:26pt 42pt 0} .sec h1{margin:12pt 0 4pt;font-size:26pt;color:#00205b;font-weight:800;letter-spacing:-.01em} .sec .sub{margin:0 0 14pt;color:#3d4a5c;font-size:10.5pt}
table.t{width:100%;border-collapse:collapse;font-size:8.6pt} table.t th{background:#003b70;color:#fff;text-align:left;padding:6pt 8pt;font-weight:700;font-size:8.2pt;border:1px solid #fff}
table.t td{padding:4pt 8pt;border:1px solid #e3e6ec;vertical-align:top;line-height:1.35;background:#fff} table.t tr:nth-child(even) td{background:#f6f8fb}
table.t td.k{font-weight:700;background:#e3e8f5} table.t td.mono{font-family:"JetBrains Mono",Consolas,monospace;font-size:8.2pt;white-space:nowrap}
table.dom{font-size:10pt} table.dom th{font-size:11pt;padding:7pt 10pt} table.dom td{padding:3.4pt 10pt;text-align:center;font-family:"JetBrains Mono",Consolas,monospace;font-weight:600;font-size:9.6pt;border:1px solid #fff}
table.dom td.k{text-align:left;font-family:inherit;font-weight:600;font-size:9.4pt;background:#e3e8f5} table.dom tr.total td{background:#c7d1ed;font-weight:700;font-size:10.5pt} table.dom tr.total td.k{background:#003b70;color:#fff;font-size:12pt}
.V,table.t td.V{background:#b8d680!important} .A,table.t td.A{background:#fcc97d!important} .R,table.t td.R{background:#f7786e!important} .pill{display:inline-block;padding:2pt 7pt;border-radius:4pt;font-weight:700;font-size:8pt;white-space:nowrap}
.pV{background:#dcebd4;color:#276221} .pA{background:#fbe4cc;color:#9c5700} .pR{background:#f5cccc;color:#b02a2a}
.tiles{display:grid;grid-template-columns:repeat(5,1fr);gap:16pt;margin:12pt 0 16pt} .tile{border-radius:8pt;padding:12pt 14pt;display:flex;align-items:baseline;gap:12pt;min-height:52pt}
.tile b{font-size:22pt;font-weight:800} .tile span{font-size:8.6pt;font-weight:700;line-height:1.2}
.t4{background:#dcebd4} .t4 *{color:#276221} .t3{background:#e8f1f8} .t3 *{color:#00529b} .t2{background:#fbe4cc} .t2 *{color:#9c5700} .t1{background:#fbe4cc} .t1 *{color:#9c5700} .t0{background:#f5cccc} .t0 *{color:#b02a2a}
h3.az{color:#00529b;font-size:15pt;margin:0 0 4pt;font-weight:800} .lead{font-size:10.2pt;line-height:1.4;margin:0;color:#171f2a}
table.lay{width:100%;border-collapse:separate;border-spacing:14pt 0;margin:0 -14pt;table-layout:fixed} table.lay td{vertical-align:top;padding:0 0 12pt}
.box{border:1px solid #e3e6ec;border-radius:4pt;overflow:hidden} .box h4{margin:0;background:#003b70;color:#fff;font-size:9pt;padding:6pt 10pt;font-weight:700} .box.g h4{background:#276221} .box.r h4{background:#b02a2a} .box.o h4{background:#9c5700} .box.p h4{background:#00529b} .box.gr h4{background:#5f6b7a}
.box ul{margin:0;padding:6pt 10pt 6pt 20pt;font-size:7.7pt;line-height:1.34} .box li{margin:0 0 3.5pt} .box li b{color:#00205b} .box .fuente{display:block;color:#5f6b7a;font-size:6.6pt;margin-top:1pt}
.box.wide{grid-column:1 / -1} .box.wide ul{columns:2;column-gap:22pt} .box.wide li{break-inside:avoid}
.cg{display:grid;grid-template-columns:1fr 1fr;gap:12pt 26pt} .ci{font-size:8.8pt;line-height:1.4;border-bottom:1px solid #e3e6ec;padding-bottom:8pt} .ci b{display:block;color:#00205b;font-size:9.6pt;margin-bottom:2pt} .ci .dots{float:right;font-size:8pt;letter-spacing:.05em}
.div{display:flex;align-items:center;min-height:540pt} .div .arc{position:absolute;left:-150pt;top:-40pt;width:620pt;height:620pt;border-radius:50%;border:30pt solid #eef1f4;box-sizing:border-box} .div img{position:absolute;left:60pt;top:236pt;width:260pt}
.div .nm{position:absolute;left:526pt;top:300pt;color:#0e2841} .div .nm small{display:block;font-size:14pt;font-weight:700} .div .nm big{display:block;font-size:34pt;font-weight:800;line-height:1.1} .div .nm em{display:block;font-style:normal;color:#5f6b7a;font-size:10pt;margin-top:8pt}
.cover{min-height:540pt;background:#1b2a4a;overflow:hidden} .cover img.f{position:absolute;inset:0;width:100%;height:100%;object-fit:cover} .cover .sh{position:absolute;left:-330pt;top:-180pt;width:920pt;height:920pt;border-radius:50%;background:linear-gradient(160deg,#ee6a1f 0%,#d9471f 45%,#7b3a4a 80%,#3b3a6a 100%);opacity:.93}
.cover .tx{position:absolute;left:71pt;top:190pt;color:#fff} .cover .tx h1{margin:0;font-size:32pt;line-height:1.2;font-weight:800} .cover .tx p{margin:6pt 0 0;font-size:21pt;font-style:italic;font-weight:700} .cover .tx .d{position:absolute;top:200pt;font-size:12pt;font-style:normal;font-weight:400;white-space:nowrap}
.cover img.l{position:absolute;right:27pt;bottom:17pt;width:119pt}
.svgbox{border:1px solid #e3e6ec;border-radius:4pt;padding:8pt}
.pend3 .box ul{font-size:8pt} .pend3 h4 span{opacity:.75;font-weight:400}
.nb{border:1px solid #e3e6ec;border-top:3pt solid var(--vc);border-radius:4pt;padding:4pt 7pt 3pt} .nb h4{margin:0 0 2pt;font-size:9.5pt;color:#00205b;letter-spacing:.06em;text-transform:uppercase}
table.nbt{width:100%;border-collapse:collapse;font-size:8.2pt} table.nbt th{font-size:6.2pt;color:#5f6b7a;text-transform:uppercase;letter-spacing:.03em;padding:2pt 1pt;text-align:center;border-bottom:1px solid #e3e6ec;background:#f6f8fb;font-weight:700} table.nbt th:first-child{text-align:left;padding-left:3pt}
table.nbt td{padding:1.6pt 1pt;text-align:center;border-bottom:1px solid #eef1f4;line-height:1.15} table.nbt td:first-child{text-align:left;font-weight:600;white-space:nowrap;padding-left:3pt}
.dot{display:inline-block;width:10pt;height:10pt;border-radius:50%;border:1.5pt solid transparent;vertical-align:middle;box-sizing:border-box} .dot.of{background:#2a78d6;border-color:#2a78d6} .dot.cond{border-color:#2a78d6} .dot.no{border-color:#8a8f98;border-style:dashed} .dot.vacio{background:#e3e6ec;width:5pt;height:5pt;border:0}
.chipm{display:inline-block;padding:1pt 5pt;border-radius:3pt;font-size:6.8pt;font-weight:700;margin-left:4pt;vertical-align:middle;white-space:nowrap} .chipm.si{background:#e8f1f8;color:#00529b} .chipm.no{background:#eef1f4;color:#5f6b7a} .chipm.cond{background:#fbe4cc;color:#9c5700} .chipm.tiene{background:#fff;color:#8a4b00;border:1px dashed #c97a1a;padding:0 4pt} .chipm.x{background:#eef1f4;color:#5f6b7a}
.otg{font-size:4.8pt;line-height:1.1;color:#2a78d6;white-space:nowrap} .otg.of{font-weight:700} .otg.no{color:#8a8f98} table.nbt td.ot{padding-left:1pt;padding-right:1pt;max-width:58pt;white-space:normal;line-height:1.1} .chipm.decl{background:#fff;color:#2a5d9f;border:1px solid #9bb8dc;padding:0 4pt} .nbn{font-size:6pt;color:#3d4a5c;line-height:1.25;margin:2pt 0 0;border-top:1px dashed #e3e6ec;padding-top:2pt} .legn{font-size:7pt;color:#5f6b7a;margin:0 0 4pt;line-height:1.45} .legn .dot{margin:0 3pt 0 6pt;width:11px;height:11px} .legn .chipm{font-size:6.4pt}
.leg{font-size:8pt;color:#5f6b7a;margin-top:8pt} .leg i{display:inline-block;width:10pt;height:10pt;border-radius:2pt;vertical-align:middle;margin:0 4pt 0 10pt}
"""
def _data_uri(p):
    if not p or not p.exists(): return ''
    return f'data:{mimetypes.guess_type(p.name)[0] or "image/png"};base64,' + base64.b64encode(p.read_bytes()).decode()

def _cls(color): return {'VERDE': 'V', 'AMARILLO': 'A', 'ROJO': 'R'}.get(color, '')

def construir_presentacion_coe(V, base, hoy):
    por_cat, por_vendor, final = leer_comentarios(base)
    cats = []
    for d in V:
        for c in d['cats']:
            if c['cat'] not in cats: cats.append(c['cat'])
    for i, d in enumerate(V):
        d['_i'] = i; d['dist_cat'], d['dist'] = distribucion_items(d['ruta']); d['ficha'] = leer_ficha(d['ruta'].parent / '10_ficha_T5.md')
    orden = sorted(V, key=lambda d: -(d['pct'] or 0)); pos = {d['vendor']: k + 1 for k, d in enumerate(orden)}
    logo = _data_uri(base / 'assets' / 'logo.png'); foto = _data_uri(base / 'assets' / 'portada.jpg')
    MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    t = datetime.date.today(); mes = f'{MESES[t.month - 1].capitalize()} {t.year}'
    FUENTE = 'Fuente: Matriz técnica del Banco, hoja T5 · semáforo y ficha T5 de cada vendor'
    n_pag = [0]
    def pie(fuente=FUENTE):
        n_pag[0] += 1
        return f'<div class="pie"><span>{esc(fuente)}</span><span class="c">Datos elaborados por BCP para uso Interno</span><span class="n">{n_pag[0]}</span></div>'
    def bar(titulo, derecha=''): return f'<div class="bar"><h2>{esc(titulo)}</h2><span class="r">{esc(derecha)}</span></div>'
    def sem(d): return {k: sum(1 for c in d['cats'] if c['color'] == k) for k in ('VERDE', 'AMARILLO', 'ROJO')}
    def pill(color, txt): return f'<span class="pill p{_cls(color)}">{esc(txt)}</span>'
    def vineta_coe(v):
        v = v.strip(); mm = re.match(r'^\*\*(.+?)\*\*\s*:?\s*(.*)$', v, re.S)
        titulo, resto = (mm.group(1), mm.group(2)) if mm else ('', v)
        partes = re.split(r'\s(?=(?:Fuente|Confianza|Impacto|Ítems?)\s*:)', resto)
        cuerpo = partes[0].strip(); meta = ' · '.join(p.strip().rstrip('.') for p in partes[1:])
        return f'<li>{("<b>" + esc(titulo) + "</b> " if titulo else "")}{m.inline(esc(cuerpo))}' + (f'<span class="fuente">{esc(meta)}</span>' if meta else '') + '</li>'
    def lay(*celdas, ancho=None):
        tds = ''.join('<td' + (' style="width:%s"' % ancho[i] if ancho else '') + '>' + c + '</td>' for i, c in enumerate(celdas))
        return '<table class="lay"><tr>' + tds + '</tr></table>'
    def box(titulo, items, cls, n_max=None, wide=False):
        its = items[:n_max] if n_max else items
        return f'<div class="box {cls}{" wide" if wide else ""}"><h4>{esc(titulo)}' + (f' ({len(items)})' if items else '') + '</h4>' + (f'<ul>{"".join(vineta_coe(v) for v in its)}</ul>' if its else '<ul><li>—</li></ul>') + '</div>'
    H = [f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Presentación T5 · CoE</title>{m.FONTS}<style>{CSS_COE}</style></head><body>']
    # 0 portada (textos de la portada del deck corporativo; fecha = mes de generación)
    H.append('<section class="s cover">' + (f'<img class="f" src="{foto}" alt="">' if foto else '') + '<div class="sh"></div><div class="tx"><h1>Proyecto Transformación<br>Nuevo Core Cuentas</h1><p>Revisión Técnica Resultados T5</p>'
             + f'<span class="d">{esc(mes)}</span></div>' + (f'<img class="l" src="{logo}" alt="">' if logo else '') + '</section>')
    # 1 ranking
    filas = ''
    for d in orden:
        n = sem(d); c = color_de(d['pct'])
        filas += f'<tr><td class="mono" style="text-align:center;font-weight:700">{pos[d["vendor"]]}</td><td class="k">{esc(m.nombre(d["vendor"]))}</td><td class="mono {_cls(c)}" style="text-align:center;font-size:10pt">{d["pct"]}</td><td class="{_cls(c)}" style="font-weight:700">{esc(d["nivel"])}</td><td style="text-align:center">{n["VERDE"]}</td><td style="text-align:center">{n["AMARILLO"]}</td><td style="text-align:center">{n["ROJO"]}</td><td class="mono">{mini_dist(d["dist"])}</td></tr>'
    H.append('<section class="s"><div class="sec"><span class="num"><b>01</b>Evaluación técnica</span><h1>Ranking T5: capacidades de desarrollo</h1><p class="sub">Puntaje T5 = media de las calificaciones del Banco (0–4 por ítem) ponderada por criticidad (Indispensable 3, Deseable 1), en escala 0–100 · 16 categorías · 80 ítems por vendor · nada se recalifica</p>'
             + '<table class="t dom" style="font-size:9.5pt"><thead><tr><th style="width:5%">#</th><th style="width:22%">Vendor</th><th style="width:11%">Puntaje T5</th><th style="width:18%">Nivel</th><th style="width:7%">🟢</th><th style="width:7%">🟡</th><th style="width:7%">🔴</th><th>Calificaciones 4 · 3 · 2 · 1 · 0</th></tr></thead><tbody>' + filas + '</tbody></table>'
             + '<p class="leg">Nivel por puntaje: <i class="V"></i>Verde ≥ 70 (Cumple; ≥ 85 Cumple plenamente) <i class="A"></i>Amarillo 50–69 (Parcial) <i class="R"></i>Rojo &lt; 50 (No cumple) · 🟢 🟡 🔴 = categorías del vendor en cada color.</p></div>' + pie() + '</section>')
    # 2 categorías × vendors
    filas = ''
    for cat in cats:
        filas += f'<tr><td class="k">{esc(cat)}</td>' + ''.join((lambda c: f'<td class="{_cls(c["color"])}">{c["pct"]}</td>' if c else '<td>—</td>')(next((x for x in d['cats'] if x['cat'] == cat), None)) for d in orden) + '</tr>'
    filas += '<tr class="total"><td class="k">Puntaje T5</td>' + ''.join(f'<td class="{_cls(color_de(d["pct"]))}">{d["pct"]}</td>' for d in orden) + '</tr>'
    H.append('<section class="s"><div class="sec"><span class="num"><b>02</b>Evaluación técnica</span><h1>Puntaje por categoría</h1><p class="sub">Cada celda es el puntaje 0–100 de la categoría para ese vendor; el color es su nivel. Vendors en orden de ranking.</p>'
             + '<table class="t dom" style="font-size:8.4pt"><thead><tr><th>Categoría</th>' + ''.join(f'<th style="text-align:center">#{pos[d["vendor"]]} {esc(m.nombre(d["vendor"]))}</th>' for d in orden) + '</tr></thead><tbody>' + filas + '</tbody></table></div>' + pie() + '</section>')
    # 3 cómo leer
    H.append('<section class="s"><div class="sec"><span class="num"><b>03</b>Cómo leer</span><h1>Qué mide cada número</h1><div style="margin-top:14pt">' + lay('<div class="box"><h4>Fuente y puntaje</h4><ul><li>La fuente es la calificación del Banco en la hoja T5 de la matriz técnica de cada vendor (0–4 por ítem: Completamente Cubierto 4, Modificación Menor 3, Modificación Mayor 2, Parcialmente Cubierto 1, No Cubierto 0). Nada se recalifica.</li><li>El puntaje de una categoría es la media de las calificaciones de sus ítems ponderada por criticidad (Indispensable 3, Deseable 1, como en el consolidado del Banco), sobre 4 y en escala 0–100. El puntaje T5 es la misma media sobre todos los ítems del vendor.</li></ul></div>',
             '<div class="box"><h4>Colores, fichas y comentarios</h4><ul><li>Verde ≥ 70, amarillo 50–69, rojo &lt; 50: son los niveles de cumplimiento oficiales del proceso.</li><li>Las fortalezas, debilidades, pendientes y contradicciones de cada vendor salen de su matriz (respuesta del proveedor y sustento del evaluador) y, cuando existe, de la verificación documental de T5. Cada punto nombra su ítem y su fuente; nada proviene de información externa.</li></ul></div>') + '</div></div>' + pie() + '</section>')
    # 4 vendors en orden de ranking
    for d in orden:
        nom = m.nombre(d['vendor']); n = sem(d); c = color_de(d['pct']); f = d['ficha'] or {}; k = pos[d['vendor']]
        H.append(f'<section class="s div"><div class="arc"></div>' + (f'<img src="{logo}" alt="">' if logo else '') + f'<div class="nm"><small>Vendor #{k} de {len(V)}</small><big>{esc(nom)}</big><em>T5 · {d["pct"]} · {esc(d["nivel"])}</em></div></section>')
        # resumen ejecutivo: lectura general + lo que dice la ficha (fortalezas, debilidades, contradicciones y pendientes), no solo conteos
        tiles = ''.join(f'<div class="tile t{v}"><b>{d["dist"].get(v, 0)}</b><span>{esc(nm)}</span></div>' for v, nm in ((4, 'Completamente cubiertas'), (3, 'Modificación menor'), (2, 'Modificación mayor'), (1, 'Parcialmente cubiertas'), (0, 'No cubiertas')))
        lectura = f.get('lectura') or d['resumen']
        def titulos(items, n_max=8):
            out = []
            for v in items[:n_max]:
                mm = re.match(r'^\*\*(.+?)\*\*', v.strip()); out.append(esc(mm.group(1)) if mm else esc(re.split(r'\s(?=Fuente\s*:)', v)[0])[:160])
            return '<br>'.join(f'• {x}' for x in out) or '—'
        def cuerpo_corto(v):
            v = re.sub(r'^\*\*(.+?)\*\*\s*:?\s*', '', v.strip()); return esc(re.split(r'\s(?=(?:Fuente|Ítems?)\s*:)', v)[0].strip())
        pend = '<br>'.join(f'• {cuerpo_corto(v)}' for v in (f.get('pendientes') or [])[:4]) or '—'
        contr = f.get('contradicciones') or []
        contr_txt = (f'{len(contr)} entre la calificación del Banco y la verificación documental: ' + ', '.join(sorted({c for v in contr for c in codigos(v)}, key=lambda c: int(c[1:]))) + '. Detalle en la hoja de pendientes y contradicciones.') if contr else 'Sin contradicciones registradas en la ficha.'
        H.append(f'<section class="s">{bar("Resumen ejecutivo " + nom.upper(), "T5 | " + d["nivel"] + " | Ranking #" + str(k) + " de " + str(len(V)))}<div class="body"><h3 class="az">Lectura general</h3>{m.md_to_html(lectura).replace("<p>", "<p class=lead>")}<div class="tiles" style="margin:10pt 0 12pt">{tiles}</div>'
                 + f'<table class="t"><thead><tr><th style="width:14%">Resultado T5</th><th style="width:27%">Fortalezas dominantes ({len(f.get("fortalezas") or [])})</th><th style="width:27%">Debilidades dominantes ({len(f.get("debilidades") or [])})</th><th>Pendientes clave ({len(f.get("pendientes") or [])})</th></tr></thead><tbody><tr><td class="{_cls(c)}" style="font-weight:700;font-size:10pt">{d["pct"]} · {esc(d["nivel"])}<div style="font-weight:400;font-size:8pt;margin-top:6pt">🟢 {n["VERDE"]} · 🟡 {n["AMARILLO"]} · 🔴 {n["ROJO"]} de 16 categorías</div><div style="font-weight:400;font-size:7.6pt;margin-top:6pt">Contradicciones: {contr_txt}</div></td><td>{titulos(f.get("fortalezas") or [])}</td><td>{titulos(f.get("debilidades") or [])}</td><td>{pend}</td></tr></tbody></table></div>' + pie() + '</section>')
        # matriz por categoría
        filas = ''
        for x in d['cats']:
            dist = d['dist_cat'].get(x['cat'], {}); dem, falta = (f.get('tabla') or {}).get(x['cat'], ('', ''))
            filas += f'<tr><td class="k">{esc(x["cat"])}</td><td class="mono" style="text-align:center">{x["pct"]}</td><td class="mono">{mini_dist(dist)}</td><td>{esc(dem) or esc(d["conclusiones"].get(x["cat"], ""))}</td><td>{esc(falta)}</td><td class="{_cls(x["color"])}" style="font-weight:700;white-space:nowrap">{esc(x["color"].capitalize())}</td></tr>'
        H.append(f'<section class="s">{bar("Matriz por categoría · " + nom, "Puntaje, calificaciones del Banco y lectura por categoría")}<div class="body"><table class="t" style="font-size:7.3pt"><thead><tr><th style="width:17%">Categoría</th><th style="width:6%">Puntaje</th><th style="width:9%">4 · 3 · 2 · 1 · 0</th><th>Lo que demuestra</th><th>Lo que falta</th><th style="width:7%">Resultado</th></tr></thead><tbody>{filas}</tbody></table></div>' + pie() + '</section>')
        if f:
            H.append(f'<section class="s">{bar("Fortalezas y debilidades · " + nom, "T5 | " + str(d["pct"]) + " · " + d["nivel"])}<div class="body">' + lay(box('Fortalezas', f['fortalezas'], 'g'), box('Debilidades', f['debilidades'], 'r')) + '</div>' + pie() + '</section>')
            H.append(f'<section class="s">{bar("Pendientes, contradicciones y declarado sin sustento · " + nom, "T5 | " + str(d["pct"]) + " · " + d["nivel"])}<div class="body">' + lay(box('Pendientes', f['pendientes'], 'o'), box('Contradicciones', f['contradicciones'], 'p'))
                     + (box('Declarado sin sustento', f['sin_sustento'], 'gr', wide=True) if f['sin_sustento'] else '') + '</div>' + pie() + '</section>')
    # 5 comentarios por categoría
    if any(por_cat.get(c) for c in cats):
        grupos = [cats[i:i + 6] for i in range(0, len(cats), 6)]
        for g, grupo in enumerate(grupos, 1):
            items = ''
            for cat in grupo:
                dots = ' '.join(SIM[c['color']] for d in orden for c in d['cats'] if c['cat'] == cat)
                items += f'<div class="ci"><b>{esc(cat)} <span class="dots">{dots}</span></b>{m.inline(esc(por_cat.get(cat, "")))}</div>'
            H.append(f'<section class="s">{bar("Comentarios por categoría (" + str(g) + " de " + str(len(grupos)) + ")", "Dónde coinciden y dónde se separan los vendors")}<div class="body"><p class="lead" style="font-size:8.6pt;color:#5f6b7a;margin-bottom:10pt">Los puntos muestran el color de cada vendor en la categoría, en orden de ranking: ' + ' · '.join(f'#{pos[d["vendor"]]} {esc(m.nombre(d["vendor"]))}' for d in orden) + f'.</p><div class="cg">{items}</div></div>' + pie() + '</section>')
    # 6 resultado final
    filas = ''.join((lambda n: f'<tr><td class="mono" style="text-align:center;font-weight:700">{pos[d["vendor"]]}</td><td class="k">{esc(m.nombre(d["vendor"]))}</td><td class="mono {_cls(color_de(d["pct"]))}" style="text-align:center">{d["pct"]}</td><td class="{_cls(color_de(d["pct"]))}">{esc(d["nivel"])}</td><td style="text-align:center">{n["VERDE"]}</td><td style="text-align:center">{n["AMARILLO"]}</td><td style="text-align:center">{n["ROJO"]}</td></tr>')(sem(d)) for d in orden)
    H.append(f'<section class="s">{bar("Resultado final", "Ranking por puntaje T5")}<div class="body">' + lay(f'<div class="svgbox">{svg_final(orden)}</div><table class="t" style="margin-top:10pt"><thead><tr><th>#</th><th>Vendor</th><th>Puntaje</th><th>Nivel</th><th>🟢</th><th>🟡</th><th>🔴</th></tr></thead><tbody>{filas}</tbody></table>',
             '<div class="box p"><h4>Comentario final</h4><ul style="list-style:none;padding-left:10pt;font-size:9pt;line-height:1.45"><li>' + (m.inline(esc(final)) if final else 'Pendiente de redacción.') + '</li></ul></div>') + '</div>' + pie() + '</section>')
    # 7 lo pendiente
    cajas = [f'<div class="box"><h4>#{pos[d["vendor"]]} {esc(m.nombre(d["vendor"]))} <span>· categorías en rojo y amarillo</span></h4><ul>' + (''.join(f'<li>{SIM[c["color"]]} {esc(c["cat"])} · {c["pct"]}</li>' for c in sorted([c for c in d['cats'] if c['color'] in ('ROJO', 'AMARILLO')], key=lambda x: x['pct'] or 0)) or '<li>Ninguna categoría en rojo ni amarillo.</li>') + '</ul></div>' for d in orden]
    cajas = ''.join(lay(*cajas[i:i + 3]) for i in range(0, len(cajas), 3))
    H.append(f'<section class="s">{bar("Lo pendiente", "Categorías en rojo y amarillo por vendor")}<div class="body"><p class="lead" style="font-size:9pt;color:#5f6b7a;margin-bottom:10pt">Lo que cada vendor dejó sin cubrir o sin sustento según la calificación del Banco; el detalle por ítem está en el semáforo y la ficha de cada vendor.</p><div class="pend3">{cajas}</div></div>' + pie(f'Presentación generada el {hoy} · ' + FUENTE) + '</section>')
    # 8 estrategia de implementación (general + por vendor), solo si existen los informes de implementación
    IMP = datos_implementacion(V); g = IMP['general']
    if g:
        def pct_td(v):
            p = re.search(r'[\d.]+', v or ''); p = float(p.group(0)) if p else None
            return f'<td class="mono {_cls(nivel_pct(p))}" style="text-align:center;font-weight:700">{esc(v)}</td>'
        hdr, rows = g['resumen']
        if hdr:
            col = {m._norm(h): i for i, h in enumerate(hdr)}
            def ci(*pref): return next((i for h, i in col.items() if any(h.startswith(m._norm(p)) for p in pref)), None)
            iv, ie, idu, ii, iei, if_, ii_, ial = ci('vendor'), ci('enfoque'), ci('duraci'), ci('implementador'), ci('% estrategia', 'ei'), ci('% fabricante'), ci('% implementador'), ci('señales', 'senales')
            filas = ''
            for r in rows:
                r = r + [''] * (len(hdr) - len(r)); v = r[iv] if iv is not None else ''
                filas += f'<tr><td class="k">{esc(m.nombre(v))}</td><td>{esc(r[ie]) if ie is not None else ""}</td><td>{esc(r[idu]) if idu is not None else ""}</td><td>{esc(r[ii]) if ii is not None else ""}</td>' + ''.join(pct_td(r[i]) if i is not None else '<td>—</td>' for i in (iei, if_, ii_)) + f'<td class="mono" style="text-align:center">{esc(r[ial]) if ial is not None else ""}</td></tr>'
            H.append('<section class="s"><div class="sec"><span class="num"><b>04</b>Estrategia de implementación</span><h1>Cómo propone implantar cada vendor</h1><p class="sub">' + esc(m.nombres_en_texto(g['titular'])) + '</p>'
                     + '<table class="t" style="font-size:8.4pt"><thead><tr><th style="width:12%">Vendor</th><th style="width:22%">Enfoque de despliegue</th><th style="width:13%">Duración propuesta</th><th style="width:20%">Implementador</th><th style="width:8%">% Estrategia (EI)</th><th style="width:8%">% Fabricante (F)</th><th style="width:9%">% Implementador (I)</th><th>Señales de alerta</th></tr></thead><tbody>' + filas + '</tbody></table>'
                     + '<p class="leg">Rúbrica corporativa de implementación (0–5 por criterio, ponderada): EI estrategia de implementación · F perfil del fabricante · I perfil del implementador. Color por nivel: <i class="V"></i>≥ 70 <i class="A"></i>50–69 <i class="R"></i>&lt; 50. Fuente: verificación de implementación y comparativo de implementación de cada vendor.</p></div>' + pie('Fuente: rúbrica de implementación (verif/IMPL.md), informe de implementación (7_) y COMPARATIVO_IMPLEMENTACION.md') + '</section>')
        hdr, rows = g['ei']
        if hdr:
            filas = ''
            for r in rows:
                r = r + [''] * (len(hdr) - len(r)); filas += f'<tr><td class="k">{esc(r[0])}</td>' + ''.join((lambda c: f'<td class="{_cls(color_0_5(c.split()[0] if c.split() else None))}"><b class="mono">{esc(c.split()[0]) if c.split() else "—"}</b> {esc(" ".join(c.split()[1:]))}</td>')(c) for c in r[1:]) + '</tr>'
            H.append(f'<section class="s">{bar("Estrategia de implementación · criterio a criterio", "Rúbrica EI-01 a EI-12, puntaje 0–5 con su descriptor")}<div class="body"><table class="t" style="font-size:7.6pt"><thead><tr><th style="width:19%">Criterio EI</th>' + ''.join(f'<th>{esc(m.nombre(h))}</th>' for h in hdr[1:]) + f'</tr></thead><tbody>{filas}</tbody></table>'
                     + ('<div class="box n" style="margin-top:10pt"><h4>Criterios con mayor diferencia y por qué</h4><ul>' + ''.join(f'<li>{esc(m.nombres_en_texto(x))}</li>' for x in g['diferencias']) + '</ul></div>' if g['diferencias'] else '') + '</div>' + pie('Fuente: rúbrica de implementación de cada vendor (verif/IMPL.md) y COMPARATIVO_IMPLEMENTACION.md') + '</section>')
        if g['transversal']:
            H.append(f'<section class="s">{bar("Lo que cambia entre vendors en la implementación", "Comparación transversal con la fuente documental de cada vendor")}<div class="body"><div class="cg">' + ''.join(f'<div class="ci"><b>{k}</b>{esc(t)}<span class="fuente" style="display:block;color:#5f6b7a;font-size:6.8pt;margin-top:3pt">Fuentes: {esc(f)}.</span></div>' for k, (t, f) in enumerate(g['transversal'], 1)) + '</div></div>' + pie('Fuente: informes de implementación (7_), rúbricas (IMPL) y análisis de despliegue (8_) de cada vendor') + '</section>')
        DESP, PLAT = datos_despliegue(orden)
        if DESP:
            cards = []; notas = m.notas_despliegue()
            for vend, i, filas in DESP:
                trs = ''.join(f'<tr><td>{esc(nm)}<span class="chipm {cls or "x"}">{esc(corto)}</span></td>' + ''.join(f'<td><span class="dot {marcas[pn]}"></span></td>' if pn in marcas else '<td><span class="dot vacio"></span></td>' for pn in PLAT) + '<td class="ot">' + (' · '.join(f'<span class="otg {est}">{esc(cp)}</span>' for _, cp, est in otras) or '<span class="dot vacio"></span>') + '</td></tr>' for nm, cls, corto, marcas, otras in filas)
                cards.append(f'<div class="nb" style="--vc:{m.vcolor(i)}"><h4>{esc(m.nombre(vend))}</h4><table class="nbt"><thead><tr><th>Modelo</th>' + ''.join(f'<th>{esc(pn)}</th>' for pn in PLAT) + f'<th>Otras</th></tr></thead><tbody>{trs}</tbody></table>' + (lambda nt: f'<p class="nbn">{m.inline(esc(m.nombres_en_texto(nt)))}</p>' if nt else '')(notas.get(m._norm(vend))) + '</div>')
            leyenda = ('<p class="legn" style="margin-bottom:3pt"><b>Modelo:</b> ' + ' · '.join(f'<span class="chipm {k}" style="margin-left:0">{esc(c)}</span> {esc(t)}' for k, c, t in LEYENDA_CHIPS) + '</p>'
                       '<p class="legn"><b>Nube:</b> ' + ' · '.join(f'<span class="dot {k}"></span> {t}' for k, t in zip(('of', 'cond', 'no', 'vacio'), LEYENDA_NUBES)) + '. ' + esc(NOTA_NUBES) + '</p>')
            H.append(f'<section class="s">{bar("Modelos de despliegue · plataformas por modelo", "Resumen por vendor: una fila por modelo y una columna por nube o plataforma")}<div class="body">'
                     + leyenda + lay(*cards[:3]) + (lay(*cards[3:6]) if len(cards) > 3 else '') + '</div>' + pie('Fuente: análisis de despliegue de cada vendor (8_) · informe de comparativos, hoja 4') + '</section>')
        for d in orden:
            x = IMP['vendors'].get(d['vendor'])
            if not x: continue
            nom = m.nombre(d['vendor']); rs = x.get('resumen') or {}; pv = g['por_vendor'].get(d['vendor'], {})
            tiles = ''.join((lambda p, col: f'<div class="tile" style="background:{PILL[col][0] if col != "SIN CALIFICAR" else "#eef1f4"}"><b style="color:{PILL[col][1] if col != "SIN CALIFICAR" else "#5f6b7a"}">{p if p is not None else "—"}</b><span style="color:{PILL[col][1] if col != "SIN CALIFICAR" else "#5f6b7a"}">{nm}</span></div>')(rs.get(k), nivel_pct(rs.get(k))) for k, nm in (('EI', '% Estrategia de implementación'), ('F', '% Perfil del fabricante'), ('I', '% Perfil del implementador')))
            tiles += f'<div class="tile" style="background:#eef1f4;grid-column:span 2"><span style="color:#171f2a;font-weight:400"><b style="font-size:9pt;color:#00205b">Implementador(es)</b><br>{esc("; ".join(x.get("implementadores") or ["—"]))}</span></div>'
            filas = ''.join(f'<tr><td class="k">{esc(e)}</td><td>{esc(q)}</td><td style="color:#5f6b7a;font-size:6.9pt">{esc(fu)}</td><td class="{_cls({"ALTA": "VERDE", "MEDIA": "AMARILLO", "BAJA": "ROJO"}.get(c.strip().upper(), ""))}" style="text-align:center;font-weight:700">{esc(c)}</td></tr>' for e, q, fu, c in ficha_impl_filas(x))
            H.append(f'<section class="s">{bar("Estrategia de implementación · " + nom, "Ficha resumen del informe de implementación")}<div class="body">' + (f'<p class="lead" style="font-size:9.6pt"><b style="color:#00529b">En una frase.</b> {esc(x.get("titular", ""))}</p>' if x.get('titular') else '')
                     + f'<div class="tiles" style="grid-template-columns:repeat(5,1fr);margin:8pt 0 10pt">{tiles}</div><table class="t" style="font-size:7.8pt"><thead><tr><th style="width:15%">Elemento</th><th style="width:43%">Qué propone</th><th style="width:34%">Fuente</th><th>Confianza</th></tr></thead><tbody>{filas}</tbody></table></div>' + pie('Fuente: informe de implementación (7_) y rúbrica de implementación (verif/IMPL.md) de ' + nom) + '</section>')
            def it_box(items, lead):
                return [f'**{i["afirmacion"]}**: {lead} {i.get("importa", "")} Fuente: {i["fuente"]} · Confianza: {i["confianza"]}' if i.get('importa') else f'**{i["afirmacion"]}**. Fuente: {i["fuente"]} · Confianza: {i["confianza"]}' for i in items]
            abajo = ''
            for titulo, clave, cls in (('Veredicto en una frase', 'Veredicto', 'p'), ('Señales de alerta', 'Señales', 'o'), ('Lo que deja al Banco', 'deja al Banco', 'gr')):
                lst = next((v for k, v in pv.items() if m._norm(clave) in m._norm(k)), [])
                if lst: abajo += box(titulo, [m.nombres_en_texto(z) for z in lst], cls)
            H.append(f'<section class="s">{bar("Pros, contras y veredicto de implementación · " + nom, "Del informe de implementación y del comparativo entre vendors")}<div class="body">' + lay(box('Pros', it_box((x.get('pros_items') or [])[:5], 'Por qué importa:'), 'g'), box('Contras', it_box((x.get('contras_items') or [])[:5], 'Consecuencia:'), 'r'))
                     + (f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12pt">{abajo}</div>' if abajo else '') + '</div>' + pie('Fuente: informe de implementación (7_) de ' + nom + ' y COMPARATIVO_IMPLEMENTACION.md') + '</section>')
    H.append('</body></html>')
    return '\n'.join(H)

def main():
    args = sys.argv[1:]; pdf = '--pdf' in args
    estilo = args[args.index('--estilo') + 1] if '--estilo' in args else ''
    base = Path(args[args.index('--base') + 1]) if '--base' in args else RAIZ / 'vendors'
    if not base.is_absolute(): base = RAIZ / base
    V = cargar(base)
    if not V: sys.exit(f'No encontré ningún 9_semaforo_T5.md bajo {base}. Corre antes scripts/09_semaforo_t5.py por vendor.')
    hoy = datetime.date.today().strftime('%d-%m-%Y')
    if not pdf:
        out, cats = construir_comparativo(V, base, hoy)
        print(f'{out}\n{len(V)} vendors: ' + ', '.join(f'{m.nombre(d["vendor"])} {d["pct"]}' for d in V) + f' · {len(cats)} categorías. Ahora: agente comparador-semaforo-t5 para los comentarios; luego --pdf.')
    else:
        if estilo == 'coe':
            out = base / 'PRESENTACION_T5_COE.html'; out.write_text(construir_presentacion_coe(V, base, hoy), encoding='utf-8')
        else:
            out = base / 'PRESENTACION_T5.html'; out.write_text(construir_presentacion(V, base, hoy), encoding='utf-8')
        print(f'HTML: {out}'); m.a_pdf(out, out.with_suffix('.pdf'))

if __name__ == '__main__':
    main()
