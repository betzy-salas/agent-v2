#!/usr/bin/env python3
"""F5 · Documento final de estrategias de implementación: vendors/INFORME_IMPLEMENTACION.html (+ .pdf con --pdf)

Lee, por vendor, verif/IMPL.md (rúbrica puntuada), informes/7_implementacion_pros_contras.md (ficha, pros y contras),
informes/8_modelo_despliegue.md (si existe) y, si existe, vendors/COMPARATIVO_IMPLEMENTACION.md (lectura comparativa
redactada por el agente). No inventa texto: todo lo narrativo se copia de esos archivos.

Uso:
    python scripts/07_informe_implementacion.py                 # todos los vendors con verif/IMPL.md
    python scripts/07_informe_implementacion.py sunline acme    # solo esos
    python scripts/07_informe_implementacion.py --pdf           # además genera el PDF con Edge/Chrome sin cabeza
    python scripts/07_informe_implementacion.py --salida ruta.html
"""
import re, sys, html, datetime, subprocess, shutil, platform, statistics, unicodedata
def _norm(x): return ''.join(c for c in unicodedata.normalize('NFKD', str(x or '')) if not unicodedata.combining(c)).lower().strip()
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _comun import VENDORS, RAIZ

# ----------------------------------------------------------------------------- utilidades markdown
def split_cells(line):
    return [c.strip() for c in re.split(r'(?<!\\)\|', line.strip().strip('|'))]

def parse_table(lines):
    """Lista de líneas de tabla md → (cabecera, filas)."""
    rows = [split_cells(l) for l in lines if l.strip().startswith('|')]
    rows = [r for r in rows if not all(re.fullmatch(r':?-{2,}:?', c) for c in r)]
    if not rows: return [], []
    return rows[0], rows[1:]

SECCIONES_CONOCIDAS = r'(Titular|Cabecera|Ficha|Pros\b|Contras\b|Riesgos|Lo que el Banco asume|Incoherencias|Señales|Preguntas|Modelos|Nubes|Región|No soporta|Contradicciones|Tabla|Resumen|Hallazgos|Comparaci|Lectura|Diferencias)'
def sections(md):
    """Divide un markdown por encabezados (#, ##, ###). Tolera informes sin «#»: trata como encabezado una línea corta
    numerada («3. Ficha resumen») con un título de sección conocido, y la primera línea como titular."""
    md = md.replace('\r\n', '\n').replace('\r', '\n')
    sin_almohadillas = not re.search(r'^#{1,4}\s', md, re.M)
    out, cur, buf, primera = [], (0, ''), [], True
    for l in md.split('\n'):
        m = re.match(r'^(#{1,4})\s+(.*)$', l)
        if not m and sin_almohadillas:
            if primera and l.strip():
                primera = False; m = re.match(r'^()(.*)$', l.strip()); lvl = 1
            else:
                mm = re.match(r'^\s*\d{1,2}[.)]\s+((?:' + SECCIONES_CONOCIDAS[1:-1] + r').{0,60})$', l.strip(), re.I)
                if mm: m = re.match(r'^()(.*)$', l.strip()); lvl = 2
        if m:
            nivel = len(m.group(1)) if m.group(1) else lvl
            out.append((cur[0], cur[1], '\n'.join(buf))); cur = (nivel, m.group(2).strip()); buf = []
        else: buf.append(l)
        if l.strip(): primera = False
    out.append((cur[0], cur[1], '\n'.join(buf)))
    return out

def find_section(secs, *claves):
    for lvl, t, body in secs:
        tl = _norm(t)
        if any(_norm(k) in tl for k in claves): return body
    return ''

def first_table(body):
    lines = body.split('\n'); i = 0
    while i < len(lines) and not lines[i].strip().startswith('|'): i += 1
    j = i
    while j < len(lines) and lines[j].strip().startswith('|'): j += 1
    return parse_table(lines[i:j]) if i < len(lines) else ([], [])

def inline(md):
    s = html.escape(md, quote=False)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    return s

def md_to_html(md, max_heading=4):
    """Conversor mínimo: encabezados, párrafos, listas, tablas, negrita, cursiva, código."""
    out, lines, i = [], md.split('\n'), 0
    while i < len(lines):
        l = lines[i]
        if not l.strip(): i += 1; continue
        m = re.match(r'^(#{1,6})\s+(.*)$', l)
        if m:
            lvl = min(len(m.group(1)) + 1, 6); out.append(f'<h{lvl}>{inline(m.group(2))}</h{lvl}>'); i += 1; continue
        if l.strip().startswith('|'):
            j = i
            while j < len(lines) and lines[j].strip().startswith('|'): j += 1
            hdr, rows = parse_table(lines[i:j])
            if hdr:
                out.append('<div class="tbl-wrap"><table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in hdr) + '</tr></thead><tbody>')
                for r in rows:
                    r = r + [''] * (len(hdr) - len(r))
                    out.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r[:len(hdr)]) + '</tr>')
                out.append('</tbody></table></div>')
            i = j; continue
        if re.match(r'^\s*([-*•]|\d+[.)])\s+', l):
            ordered = bool(re.match(r'^\s*\d+[.)]\s+', l)); tag = 'ol' if ordered else 'ul'; items = []
            while i < len(lines) and (re.match(r'^\s*([-*•]|\d+[.)])\s+', lines[i]) or (lines[i].startswith('  ') and lines[i].strip() and items)):
                if re.match(r'^\s*([-*•]|\d+[.)])\s+', lines[i]): items.append(re.sub(r'^\s*([-*•]|\d+[.)])\s+', '', lines[i]))
                else: items[-1] += ' ' + lines[i].strip()
                i += 1
            out.append(f'<{tag}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + f'</{tag}>'); continue
        if l.strip().startswith('>'):
            out.append(f'<blockquote>{inline(l.strip()[1:].strip())}</blockquote>'); i += 1; continue
        # párrafo
        j = i; par = []
        while j < len(lines) and lines[j].strip() and not lines[j].strip().startswith(('|', '#', '>')) and not re.match(r'^\s*([-*•]|\d+[.)])\s+', lines[j]):
            par.append(lines[j].strip()); j += 1
        out.append(f'<p>{inline(" ".join(par))}</p>'); i = j
    return '\n'.join(out)

num = lambda s: (lambda m: int(m.group()) if m else None)(re.search(r'\d', s or ''))
pct = lambda s: (lambda m: float(m.group(1)) if m else None)(re.search(r'(\d+(?:[.,]\d+)?)\s*%?', (s or '').replace(',', '.')))

# ----------------------------------------------------------------------------- carga por vendor
def cargar_vendor(v):
    d = VENDORS / v; data = {'vendor': v, 'ok': False, 'crit': {'EI': [], 'F': [], 'I': []}, 'resumen': {}, 'ceros': 0, 'declarados': 0, 'implementadores': ['—'], 'tiene_impl': False}
    impl = d / 'verif' / 'IMPL.md'; f7 = d / 'informes' / '7_implementacion_pros_contras.md'
    if not impl.exists() and not f7.exists(): return data
    data['ok'] = True
    if impl.exists():
      data['tiene_impl'] = True; md = impl.read_text(encoding='utf-8-sig'); secs = sections(md); data['impl_secs'] = secs
      def tabla(clave):
          hdr, rows = first_table(find_section(secs, clave)); return hdr, rows
      def idx(hdr, *pref):
          for p in pref:
              for i, c in enumerate(hdr):
                  if _norm(c).startswith(_norm(p)): return i
          return None
      crit = {'EI': [], 'F': [], 'I': []}
      for bloque, clave in (('EI', 'Tabla EI'), ('F', 'Tabla F'), ('I', 'Tabla I')):
          hdr, rows = tabla(clave)
          if not hdr: continue
          iC, iCr, iP, iPu, iR, iE, iJ = idx(hdr, 'Código'), idx(hdr, 'Criterio'), idx(hdr, 'Peso'), idx(hdr, 'Puntaje'), idx(hdr, 'Respaldo'), idx(hdr, 'Evidencia'), idx(hdr, 'Justificación')
          iImp = idx(hdr, 'Implementador'); iResp = idx(hdr, 'Respuesta')
          for r in rows:
              r = r + [''] * (len(hdr) - len(r))
              if iC is None or not re.match(r'^(EI|F|I)-\d', r[iC]): continue
              pu = r[iPu] if iPu is not None else ''
              crit[bloque].append({'codigo': r[iC], 'criterio': r[iCr] if iCr is not None else '', 'peso': r[iP] if iP is not None else '',
                                   'puntaje': num(pu) if 'informativo' not in pu.lower() else None, 'descriptor': re.sub(r'^\s*\d+(\.\d+)?\s*[—\-–]\s*', '', pu).strip(),
                                   'respaldo': r[iR] if iR is not None else '', 'evidencia': r[iE] if iE is not None else '', 'justificacion': r[iJ] if iJ is not None else '',
                                   'implementador': r[iImp] if iImp is not None else '', 'respuesta': r[iResp] if iResp is not None else ''})
      data['crit'] = crit
      # resumen por bloque (porcentajes) — se lee, y si falta se calcula
      hdr, rows = tabla('Resumen por bloque'); resumen = {}
      for r in rows:
          if not r: continue
          b = r[0].strip().upper()
          bn = _norm(b).upper(); key = 'EI' if 'ESTRATEGIA' in bn or bn.startswith('EI') else 'F' if 'FABRICANTE' in bn or bn == 'F' else 'I' if 'IMPLEMENTADOR' in bn or bn == 'I' else None
          if key:
              p = next((pct(c) for c in r[1:] if pct(c) is not None and '%' in c), None)
              if p is None:
                  cand = [pct(c) for c in r[1:] if pct(c) is not None and 0 <= pct(c) <= 100]
                  p = cand[1] if len(cand) > 1 else (cand[0] if cand else None)
              resumen[key] = p
      for key in ('EI', 'F', 'I'):
          if resumen.get(key) is None:
              items = [c for c in crit[key] if c['puntaje'] is not None and pct(c['peso']) is not None]
              if items:
                  w = sum(pct(c['peso']) for c in items); resumen[key] = round(sum(pct(c['peso']) * c['puntaje'] for c in items) / (5 * w) * 100, 1) if w else None
      data['resumen'] = resumen
      data['ceros'] = sum(1 for b in crit.values() for c in b if c['puntaje'] == 0)
      data['declarados'] = sum(1 for b in crit.values() for c in b if 'solo declarado' in c['respaldo'].lower())
      data['hallazgos'] = find_section(secs, 'Hallazgos'); data['contradicciones'] = find_section(secs, 'Contradicciones')
      data['alertas'] = find_section(secs, 'Señales'); data['preguntas_impl'] = find_section(secs, 'Preguntas')
      data['implementadores'] = sorted({c['implementador'] for c in crit['I'] if c['implementador']}) or ['—']
    # informe 7
    f7 = d / 'informes' / '7_implementacion_pros_contras.md'
    if f7.exists():
        md7 = f7.read_text(encoding='utf-8-sig'); s7 = sections(md7); data['f7_secs'] = s7
        h1 = next(((t, b) for lvl, t, b in s7 if lvl == 1), ('', ''))
        tit = h1[0] if h1[0] and not re.match(r'^\d*[.)]?\s*Titular', h1[0], re.I) else (find_section(s7, 'Titular') or h1[1])
        data['titular'] = re.sub(r'^\d{1,2}[.)]\s+', '', re.sub(r'^\*\*|\*\*$', '', tit.strip().split('\n')[0].strip()))
        data['pros_items'] = parse_items(find_section(s7, 'Pros')); data['contras_items'] = parse_items(find_section(s7, 'Contras'))
        hdr, rows = first_table(find_section(s7, 'Ficha')); ficha = {}
        for r in rows:
            if len(r) >= 2: ficha[r[0].strip().lower()] = {'que': r[1], 'fuente': r[2] if len(r) > 2 else '', 'conf': r[3] if len(r) > 3 else ''}
        data['ficha'] = ficha
        data['pros'] = find_section(s7, 'Pros'); data['contras'] = find_section(s7, 'Contras')
        data['riesgos'] = find_section(s7, 'Riesgos'); data['asume'] = find_section(s7, 'asume')
        data['alertas7'] = find_section(s7, 'Incoherencias', 'señales'); data['preguntas7'] = find_section(s7, 'Preguntas')
    # informe 8
    f8 = d / 'informes' / '8_modelo_despliegue.md'
    if f8.exists():
        s8 = sections(f8.read_text(encoding='utf-8-sig'))
        hdr, rows = first_table(find_section(s8, 'Modelos')); modelos = {}
        for r in rows:
            if len(r) >= 2: modelos[r[0].strip()] = r[1]
        data['modelos'] = modelos
        hdr, rows = first_table(find_section(s8, 'Nubes')); data['nubes'] = [(r[0], r[1] if len(r) > 1 else '', r[2] if len(r) > 2 else '') for r in rows if r]
    return data

def parse_items(body):
    """Lista numerada «afirmación; fuente: …; confianza: X; importa porque …» → dicts. Si no encaja, texto plano."""
    items = []
    for l in body.split('\n'):
        m = re.match(r'^\s*(?:\d+[.)]|[-*•])\s+(.*)$', l)
        if not m: continue
        t = m.group(1).strip()
        conf = (re.search(r'confianza\s*:\s*\**\s*(ALTA|MEDIA|BAJA)', t, re.I) or [None, None])[1]
        fuente = re.search(r'fuente\s*:\s*(.*?)(?:[;.]\s*confianza\s*:|$)', t, re.I)
        importa = re.search(r'(?:por qué importa|importa(?:\s+porque)?|consecuencia(?:\s+para el banco)?|impacto)\s*:?\s*(.*)$', t, re.I)
        afirm = re.split(r'[;.]\s*fuente\s*:', t, flags=re.I)[0].strip().rstrip(';.')
        if importa and fuente and importa.start() < fuente.start(): importa = None
        items.append({'texto': t, 'afirmacion': afirm, 'fuente': fuente.group(1).strip() if fuente else '', 'confianza': conf.upper() if conf else '', 'importa': importa.group(1).strip() if importa else ''})
    return items

def ficha_get(d, *claves):
    f = d.get('ficha', {})
    for k, val in f.items():
        if any(_norm(c) in _norm(k) for c in claves): return val['que']
    return '—'

# ----------------------------------------------------------------------------- gráficos SVG (una sola tinta, sequential azul)
RAMP = ['#e8e7e3', '#86b6ef', '#5598e7', '#2a78d6', '#1c5cab', '#0d366b']   # 0 = gris neutro (no presentado); 1..5 = rampa azul ordinal validada
INK_ON = ['#52514e', '#0b0b0b', '#0b0b0b', '#ffffff', '#ffffff', '#ffffff']
def color_puntaje(p): return RAMP[max(0, min(5, int(p)))] if p is not None else '#e8e7e3'

def svg_barras_h(items, titulo, maxv=100, fmt=lambda x: f'{x:.1f}', ancho=560):
    """items: [(etiqueta, valor)] — barras horizontales, una tinta, etiqueta directa."""
    fila, top, izq = 26, 8, 170; alto = top + fila * len(items) + 8; w = ancho - izq - 70
    s = [f'<svg class="chart" viewBox="0 0 {ancho} {alto}" role="img" aria-label="{html.escape(titulo)}">']
    for k, (lab, val) in enumerate(items):
        y = top + k * fila; v = 0 if val is None else val; bw = max(0, w * v / maxv)
        s.append(f'<text x="{izq-8}" y="{y+16}" text-anchor="end" class="lbl">{html.escape(lab[:28])}</text>')
        s.append(f'<rect x="{izq}" y="{y+4}" width="{w}" height="16" class="track"/>')
        if val is not None: s.append(f'<rect x="{izq}" y="{y+4}" width="{bw:.1f}" height="16" rx="3" fill="{RAMP[3]}"><title>{html.escape(lab)}: {fmt(val)}</title></rect>')
        s.append(f'<text x="{izq+bw+6:.1f}" y="{y+16}" class="val">{fmt(val) if val is not None else "sin dato"}</text>')
    s.append('</svg>'); return '\n'.join(s)

def svg_heatmap(filas, cols, matriz, ancho=None):
    """filas: etiquetas de criterios; cols: vendors; matriz[i][j] = puntaje o None."""
    cw, rh, izq, top = 92, 30, 300, 36; ancho = ancho or izq + cw * len(cols) + 10; alto = top + rh * len(filas) + 8
    s = [f'<svg class="chart" viewBox="0 0 {ancho} {alto}" role="img" aria-label="Mapa de calor: criterios por vendor">']
    for j, c in enumerate(cols): s.append(f'<text x="{izq + j*cw + cw/2}" y="22" text-anchor="middle" class="lbl b">{html.escape(c[:12])}</text>')
    for i, f in enumerate(filas):
        y = top + i * rh
        s.append(f'<text x="{izq-8}" y="{y+19}" text-anchor="end" class="lbl">{html.escape(f[:44])}</text>')
        for j in range(len(cols)):
            p = matriz[i][j]; x = izq + j * cw
            s.append(f'<rect x="{x+1}" y="{y+1}" width="{cw-2}" height="{rh-2}" rx="3" fill="{color_puntaje(p)}"><title>{html.escape(cols[j])} · {html.escape(f)}: {p if p is not None else "sin dato"}</title></rect>')
            s.append(f'<text x="{x+cw/2}" y="{y+19}" text-anchor="middle" class="cell" fill="{INK_ON[int(p)] if p is not None else "#52514e"}">{p if p is not None else "–"}</text>')
    s.append('</svg>'); return '\n'.join(s)

CONF_COL = {'BAJA': '#86b6ef', 'MEDIA': '#2a78d6', 'ALTA': '#0d366b'}
CONF_INK = {'BAJA': '#0b0b0b', 'MEDIA': '#ffffff', 'ALTA': '#ffffff'}
def conteo_conf(items):
    return {k: sum(1 for it in items if it.get('confianza') == k) for k in ('ALTA', 'MEDIA', 'BAJA')}

def svg_confianza(vendors_data, clave, titulo, ancho=560):
    """Barras segmentadas por vendor: nº de pros (o contras) por nivel de confianza, con separador de 2px."""
    fila, top, izq = 28, 8, 110; alto = top + fila * len(vendors_data) + 8; w = ancho - izq - 40
    maxn = max((sum(conteo_conf(d.get(clave, [])).values()) for d in vendors_data), default=1) or 1
    sv = [f'<svg class="chart" viewBox="0 0 {ancho} {alto}" role="img" aria-label="{html.escape(titulo)}">']
    for k, d in enumerate(vendors_data):
        y = top + k * fila; c = conteo_conf(d.get(clave, [])); x = izq
        sv.append(f'<text x="{izq-8}" y="{y+17}" text-anchor="end" class="lbl b">{html.escape(d["vendor"][:14])}</text>')
        for lvl in ('ALTA', 'MEDIA', 'BAJA'):
            n = c[lvl]
            if not n: continue
            bw = w * n / maxn
            sv.append(f'<rect x="{x:.1f}" y="{y+4}" width="{max(bw-2,1):.1f}" height="18" rx="3" fill="{CONF_COL[lvl]}"><title>{html.escape(d["vendor"])}: {n} {lvl}</title></rect>')
            if bw > 16: sv.append(f'<text x="{x+bw/2-1:.1f}" y="{y+17}" text-anchor="middle" class="cell" fill="{CONF_INK[lvl]}">{n}</text>')
            x += bw
        sv.append(f'<text x="{x+6:.1f}" y="{y+17}" class="val">{sum(c.values())}</text>')
    sv.append('</svg>'); return '\n'.join(sv)

def leyenda_conf():
    return '<div class="leyenda">' + ''.join(f'<span class="chip" style="background:{CONF_COL[k]};color:{CONF_INK[k]};width:auto;padding:0 8px">{k}</span>' for k in ('ALTA', 'MEDIA', 'BAJA')) + '<span class="lbl-leyenda">confianza: ALTA = compromiso explícito con cita · MEDIA = descrito sin cifra · BAJA = solo declarado o genérico</span></div>'

def tarjetas(items, tipo):
    if not items: return '<p class="small">Sin datos.</p>'
    out = [f'<ol class="cards {tipo}">']
    for it in items:
        conf = it.get('confianza') or ''
        chip = f'<span class="chip" style="background:{CONF_COL.get(conf, "#e8e7e3")};color:{CONF_INK.get(conf, "#52514e")};width:auto;padding:0 8px">{conf or "s/c"}</span>' if conf else ''
        if it.get('fuente') or it.get('importa'):
            out.append(f'<li><div class="card"><div class="card-h">{chip}<span class="card-t">{inline(it["afirmacion"])}</span></div>' + (f'<div class="fuente">Fuente: {inline(it["fuente"])}</div>' if it.get('fuente') else '') + (f'<div class="small">{inline(it["importa"])}</div>' if it.get('importa') else '') + '</div></li>')
        else:
            out.append(f'<li><div class="card"><div class="card-h">{chip}<span class="card-t">{inline(it["texto"])}</span></div></div></li>')
    out.append('</ol>'); return '\n'.join(out)

def leyenda_escala():
    return '<div class="leyenda">' + ''.join(f'<span class="chip" style="background:{RAMP[i]};color:{INK_ON[i]}">{i}</span>' for i in range(6)) + '<span class="lbl-leyenda">puntaje de la rúbrica: 0 = no presentado (gris) · 1 a 5 = de menor a mayor</span></div>'

# ----------------------------------------------------------------------------- HTML
CSS = """
:root{--ink:#0b0b0b;--ink2:#52514e;--ink3:#8a8984;--line:#e3e2dd;--surface:#fcfcfb;--panel:#f4f3ef;--accent:#1c5cab;--accent2:#2a78d6;--track:#ebeae6;}
*{box-sizing:border-box} html{font-size:15px}
body{margin:0;background:var(--surface);color:var(--ink);font-family:"Segoe UI",Inter,Roboto,"Helvetica Neue",Arial,sans-serif;line-height:1.45}
.wrap{max-width:1120px;margin:0 auto;padding:0 32px 64px}
header.portada{min-height:92vh;display:flex;flex-direction:column;justify-content:center;border-bottom:1px solid var(--line);page-break-after:always}
.kicker{letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-size:.8rem;font-weight:600}
h1{font-size:2.6rem;line-height:1.1;margin:.4rem 0 1rem;font-weight:700}
h2{font-size:1.6rem;margin:2.6rem 0 .8rem;padding-top:.6rem;border-top:3px solid var(--accent);page-break-after:avoid}
h3{font-size:1.2rem;margin:1.8rem 0 .5rem;color:var(--ink);page-break-after:avoid}
h4{font-size:1rem;margin:1.2rem 0 .3rem;color:var(--ink2)} h5,h6{font-size:.95rem;margin:1rem 0 .2rem;color:var(--ink2)}
p{margin:.4rem 0 .8rem} .meta{color:var(--ink2);font-size:.9rem}
.tbl-wrap{overflow-x:auto;margin:.6rem 0 1.2rem} table{border-collapse:collapse;width:100%;font-size:.86rem}
th{text-align:left;background:var(--panel);color:var(--ink2);font-weight:600;padding:8px 10px;border-bottom:2px solid var(--line);vertical-align:bottom}
td{padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top} tbody tr:nth-child(even) td{background:#faf9f6}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:1rem 0 1.4rem}
.kpi{background:var(--panel);border-radius:10px;padding:14px 16px} .kpi .n{font-size:1.9rem;font-weight:700;color:var(--accent);line-height:1}
.kpi .l{font-size:.8rem;color:var(--ink2);margin-top:4px}
.chart{width:100%;height:auto;display:block;margin:.4rem 0 1rem} .chart .lbl{font-size:12px;fill:var(--ink2)} .chart .lbl.b{font-weight:600;fill:var(--ink)}
.chart .val{font-size:12px;fill:var(--ink);font-weight:600} .chart .cell{font-size:12px;font-weight:600} .chart .track{fill:var(--track)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:24px} @media(max-width:800px){.grid2{grid-template-columns:1fr}}
.leyenda{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin:-.4rem 0 1rem} .chip{display:inline-block;width:28px;height:22px;border-radius:5px;text-align:center;font-size:.8rem;line-height:22px;font-weight:600}
.lbl-leyenda{font-size:.8rem;color:var(--ink2);margin-left:6px}
.pill{display:inline-block;padding:2px 8px;border-radius:999px;font-size:.75rem;font-weight:600;background:var(--panel);color:var(--ink2);border:1px solid var(--line)}
.pill.doc{border-color:#1c5cab;color:#1c5cab} .pill.dec{border-color:#8a8984} .pill.no{border-color:#b3b2ad;color:#8a8984}
.score{display:inline-block;min-width:26px;text-align:center;border-radius:5px;padding:1px 6px;font-weight:700;font-size:.8rem}
.vendor{page-break-before:always}
.cards{list-style:none;padding:0;margin:0;counter-reset:c} .cards li{counter-increment:c;margin:0 0 8px} .card{background:var(--panel);border-radius:8px;padding:9px 12px;border-left:4px solid var(--accent2);page-break-inside:avoid}
.cards.contras .card{border-left-color:#8a8984} .card-h{display:flex;gap:8px;align-items:flex-start} .card-h .chip{flex:none;height:20px;line-height:20px;font-size:.7rem} .card-t{font-weight:600;font-size:.9rem} .card-t::before{content:counter(c) '. ';color:var(--ink3);font-weight:600} .nota{background:var(--panel);border-left:4px solid var(--accent);padding:10px 14px;border-radius:6px;margin:1rem 0;font-size:.9rem}
.toc ol{columns:2;gap:32px} .toc li{margin:.15rem 0} .toc a{color:var(--ink);text-decoration:none} .toc a:hover{text-decoration:underline}
.small{font-size:.82rem;color:var(--ink2)} .fuente{color:var(--ink3);font-size:.78rem}
blockquote{margin:.6rem 0;padding:.2rem 0 .2rem 14px;border-left:3px solid var(--line);color:var(--ink2)}
code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.85em;background:var(--panel);padding:1px 4px;border-radius:4px}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--line);color:var(--ink2);font-size:.82rem}
@page{size:A4;margin:16mm 14mm 18mm}
@media print{html{font-size:11.5px} body{background:#fff} .wrap{max-width:none;padding:0} header.portada{min-height:auto;padding:40mm 0} h2{margin-top:1.6rem} .tbl-wrap{overflow:visible} table{font-size:.8rem} tr,td,th{page-break-inside:avoid} .chart{page-break-inside:avoid} *{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""

def badge_respaldo(r):
    rl = (r or '').lower(); cls = 'doc' if 'document' in rl else 'dec' if 'declar' in rl else 'no' if 'no encontr' in rl else ''
    return f'<span class="pill {cls}">{html.escape(r or "—")}</span>'

def score_html(p, desc=''):
    if p is None: return '<span class="pill">informativo</span>'
    return f'<span class="score" style="background:{color_puntaje(p)};color:{INK_ON[int(p)]}">{p}</span> <span class="small">{html.escape(desc)}</span>'

def tabla_criterios(items, con_impl=False, con_resp=False):
    h = ['Código', 'Criterio', 'Peso'] + (['Implementador'] if con_impl else []) + (['Respuesta del vendor'] if con_resp else []) + ['Puntaje', 'Respaldo', 'Evidencia', 'Justificación']
    out = ['<div class="tbl-wrap"><table><thead><tr>' + ''.join(f'<th>{c}</th>' for c in h) + '</tr></thead><tbody>']
    for c in items:
        cells = [html.escape(c['codigo']), inline(c['criterio']), html.escape(c['peso'])] + ([html.escape(c['implementador'])] if con_impl else []) + ([inline(c['respuesta'])] if con_resp else []) + [score_html(c['puntaje'], c['descriptor']), badge_respaldo(c['respaldo']), f'<span class="fuente">{inline(c["evidencia"])}</span>', inline(c['justificacion'])]
        out.append('<tr>' + ''.join(f'<td>{x}</td>' for x in cells) + '</tr>')
    out.append('</tbody></table></div>'); return '\n'.join(out)

def construir(vendors_data, comparativo_md, hoy):
    V = [d for d in vendors_data if d['ok']]; faltan = [d['vendor'] for d in vendors_data if not d['ok']]
    nombres = [d['vendor'] for d in V]
    H = []
    H.append(f'<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Estrategias de implementación — comparativo de vendors</title><style>{CSS}</style></head><body><div class="wrap">')
    # portada
    rangos = [d['resumen'].get('EI') for d in V if d['resumen'].get('EI') is not None]
    H.append('<header class="portada"><div class="kicker">Selección de core bancario · Evaluación técnica</div>')
    H.append('<h1>Estrategias de implementación<br>Informe comparativo de vendors</h1>')
    H.append(f'<p class="meta">Vendors incluidos: {", ".join(nombres)}. Generado el {hoy} a partir de los informes de implementación por vendor (ficha, pros y contras con fuente y nivel de confianza) y, cuando existe, de la rúbrica corporativa de implementación puntuada (61 criterios, escala 0–5). Sin ranking ni recomendación: el documento expone lo verificado, con su fuente.</p>')
    if faltan: H.append(f'<p class="meta">Sin verificación de implementación (no incluidos en cifras): {", ".join(faltan)}.</p>')
    con_impl = [d for d in V if d['tiene_impl']]
    tot_pros = sum(len(d.get('pros_items', [])) for d in V); tot_contras = sum(len(d.get('contras_items', [])) for d in V)
    alta_pros = sum(conteo_conf(d.get('pros_items', []))['ALTA'] for d in V)
    H.append('<div class="kpis">' + f'<div class="kpi"><div class="n">{len(V)}</div><div class="l">vendors comparados</div></div>'
             + f'<div class="kpi"><div class="n">{tot_pros}</div><div class="l">pros identificados ({alta_pros} con confianza alta)</div></div>'
             + f'<div class="kpi"><div class="n">{tot_contras}</div><div class="l">contras identificados</div></div>'
             + (f'<div class="kpi"><div class="n">{len(con_impl)}/{len(V)}</div><div class="l">vendors con rúbrica puntuada (61 criterios)</div></div>' if con_impl else '')
             + (f'<div class="kpi"><div class="n">{min(rangos):.0f}–{max(rangos):.0f}%</div><div class="l">rango del bloque Estrategia</div></div>' if rangos else '') + '</div>')
    H.append('<nav class="toc"><ol>' + '<li><a href="#resumen">Resumen comparativo</a></li><li><a href="#graficos">Lectura gráfica</a></li>' + ''.join(f'<li><a href="#v-{d["vendor"]}">{html.escape(d["vendor"])}</a></li>' for d in V) + '<li><a href="#metodo">Metodología y fuentes</a></li>' + ('<li><a href="#anexo">Anexo: criterios completos</a></li>' if con_impl else '') + '</ol></nav></header>')
    # resumen comparativo
    H.append('<h2 id="resumen">1. Resumen comparativo</h2>')
    if comparativo_md:
        cs = sections(comparativo_md); tit = find_section(cs, 'Titular') or ''
        trans = find_section(cs, 'transversal')
        if tit.strip(): H.append(f'<div class="nota">{inline(tit.strip().split(chr(10))[0])}</div>')
        if trans.strip(): H.append('<h3>Lectura comparativa</h3>' + md_to_html(trans))
    cols = ['Vendor', 'Enfoque', 'Duración total', 'Implementador', 'Migración', 'Hypercare', 'Modalidad comercial', 'Pros (A/M/B)', 'Contras (A/M/B)'] + (['% EI', '% F', '% I'] if con_impl else []) + (['Modelo de despliegue'] if any(d.get('modelos') for d in V) else [])
    H.append('<h3>Tabla comparativa por vendor</h3><div class="tbl-wrap"><table><thead><tr>' + ''.join(f'<th>{c}</th>' for c in cols) + '</tr></thead><tbody>')
    for d in V:
        modelos = d.get('modelos', {}); mod = '; '.join(f'{k}: {v.split("(")[0].strip()}' for k, v in modelos.items() if re.match(r'^(SaaS|PaaS)', k, re.I)) or '—'
        cp, cc = conteo_conf(d.get('pros_items', [])), conteo_conf(d.get('contras_items', []))
        celdas = [f'<strong>{html.escape(d["vendor"])}</strong>', inline(ficha_get(d, 'enfoque')), inline(ficha_get(d, 'duración', 'duracion')), inline(ficha_get(d, 'implementador')), inline(ficha_get(d, 'migraci')), inline(ficha_get(d, 'hypercare')), inline(ficha_get(d, 'modalidad')),
                  f'{cp["ALTA"]} / {cp["MEDIA"]} / {cp["BAJA"]}', f'{cc["ALTA"]} / {cc["MEDIA"]} / {cc["BAJA"]}']
        if con_impl: celdas += [f'{d["resumen"].get(k):.1f}%' if d['resumen'].get(k) is not None else '—' for k in ('EI', 'F', 'I')]
        if any(x.get('modelos') for x in V): celdas.append(inline(mod))
        H.append('<tr>' + ''.join(f'<td>{x}</td>' for x in celdas) + '</tr>')
    H.append('</tbody></table></div><p class="small">Textos tomados de la ficha de cada informe de implementación. Pros y contras contados por nivel de confianza (A = alta, M = media, B = baja).' + (' Porcentajes = Σ(peso × puntaje) / Σ(peso × 5) de cada bloque de la rúbrica; informativos excluidos.' if con_impl else '') + '</p>')
    # ficha comparada elemento a elemento
    elementos = []
    for d in V:
        for k in d.get('ficha', {}).keys():
            if k not in elementos: elementos.append(k)
    if elementos:
        H.append('<h3>Ficha comparada, elemento a elemento</h3><div class="tbl-wrap"><table><thead><tr><th>Elemento</th>' + ''.join(f'<th>{html.escape(d["vendor"])}</th>' for d in V) + '</tr></thead><tbody>')
        for k in elementos:
            H.append(f'<tr><td><strong>{html.escape(k.capitalize())}</strong></td>' + ''.join(f'<td>{inline(d.get("ficha", {}).get(k, {"que": "—"})["que"])}</td>' for d in V) + '</tr>')
        H.append('</tbody></table></div>')
    # gráficos
    H.append('<h2 id="graficos">2. Lectura gráfica</h2>')
    H.append('<h3>Pros y contras por nivel de confianza</h3>' + leyenda_conf() + '<div class="grid2"><div><h4>Pros</h4>' + svg_confianza(V, 'pros_items', 'Pros por confianza') + '</div><div><h4>Contras</h4>' + svg_confianza(V, 'contras_items', 'Contras por confianza') + '</div></div>')
    H.append('<p class="small">Un pro con confianza ALTA está respaldado por una cifra, fecha o compromiso explícito en un documento del vendor; uno con confianza BAJA es una afirmación genérica o solo declarada. Más pros no significa mejor propuesta: importa la confianza y el contenido de cada uno, en las secciones por vendor.</p>')
    if con_impl:
        H.append('<h3>Rúbrica corporativa: puntaje por bloque</h3><div class="grid2">')
        for k, nom in (('EI', 'Estrategia de implementación'), ('F', 'Perfil del fabricante'), ('I', 'Perfil del implementador')):
            H.append(f'<div><h4>{nom}</h4>' + svg_barras_h([(d['vendor'], d['resumen'].get(k)) for d in con_impl], f'% {nom} por vendor', fmt=lambda x: f'{x:.1f}%') + '</div>')
        H.append('</div>')
        ei_cods = []; ei_names = {}
        for d in con_impl:
            for c in d['crit']['EI']:
                if c['codigo'] not in ei_names: ei_cods.append(c['codigo']); ei_names[c['codigo']] = c['criterio']
        if ei_cods:
            matriz = [[next((c['puntaje'] for c in d['crit']['EI'] if c['codigo'] == cod), None) for d in con_impl] for cod in ei_cods]
            H.append('<h3>Mapa de calor: los 12 criterios de estrategia por vendor</h3>' + leyenda_escala() + svg_heatmap([f'{c} {ei_names[c]}' for c in ei_cods], [d['vendor'] for d in con_impl], matriz))
            H.append('<p class="small">Cada celda muestra el puntaje; el color refuerza la lectura pero el número es la fuente. Las tablas completas, con descriptor, respaldo y evidencia, están en el anexo.</p>')
    # por vendor
    for n, d in enumerate(V, 1):
        H.append(f'<section class="vendor" id="v-{d["vendor"]}"><h2>{n+2}. {html.escape(d["vendor"])}</h2>')
        if d.get('titular'): H.append(f'<div class="nota">{inline(d["titular"])}</div>')
        cp, cc = conteo_conf(d.get('pros_items', [])), conteo_conf(d.get('contras_items', []))
        H.append('<div class="kpis">' + f'<div class="kpi"><div class="n">{len(d.get("pros_items", []))}</div><div class="l">pros · {cp["ALTA"]} con confianza alta</div></div><div class="kpi"><div class="n">{len(d.get("contras_items", []))}</div><div class="l">contras · {cc["ALTA"]} con confianza alta</div></div>'
                 + ''.join(f'<div class="kpi"><div class="n">{d["resumen"].get(k):.0f}%</div><div class="l">{lab}</div></div>' if d['resumen'].get(k) is not None else '' for k, lab in (('EI', 'rúbrica · Estrategia'), ('F', 'rúbrica · Fabricante'), ('I', 'rúbrica · Implementador')))
                 + (f'<div class="kpi"><div class="n">{d["ceros"]}</div><div class="l">criterios en 0</div></div>' if d['tiene_impl'] else '') + '</div>')
        if d.get('ficha'):
            H.append('<h3>Ficha de la propuesta de implementación</h3><div class="tbl-wrap"><table><thead><tr><th>Elemento</th><th>Qué propone</th><th>Fuente</th><th>Confianza</th></tr></thead><tbody>')
            for k, val in d['ficha'].items(): H.append(f'<tr><td><strong>{html.escape(k.capitalize())}</strong></td><td>{inline(val["que"])}</td><td class="fuente">{inline(val["fuente"])}</td><td>{html.escape(val["conf"])}</td></tr>')
            H.append('</tbody></table></div>')
        if d['tiene_impl'] and d['crit']['EI']: H.append('<h3>Rúbrica corporativa: estrategia de implementación, puntaje por criterio</h3>' + svg_barras_h([(f'{c["codigo"]} {c["criterio"]}', c['puntaje']) for c in d['crit']['EI']], 'Puntaje EI', maxv=5, fmt=lambda x: f'{x:.0f} / 5'))
        if d.get('pros_items') or d.get('contras_items'): H.append('<div class="grid2"><div><h3>Pros</h3>' + tarjetas(d.get('pros_items', []), 'pros') + '</div><div><h3>Contras</h3>' + tarjetas(d.get('contras_items', []), 'contras') + '</div></div>')
        for titulo, clave in (('Riesgos de ejecución', 'riesgos'), ('Lo que el Banco asume', 'asume'), ('Incoherencias y señales de alerta', 'alertas7'), ('Contradicciones de la rúbrica', 'contradicciones'), ('Señales de alerta de la rúbrica', 'alertas'), ('Preguntas pendientes al vendor', 'preguntas7')):
            if d.get(clave, '').strip(): H.append(f'<h3>{titulo}</h3>' + md_to_html(d[clave]))
        if d.get('modelos'):
            H.append('<h3>Modelo de despliegue</h3><div class="tbl-wrap"><table><thead><tr><th>Modelo</th><th>Ofrecido</th></tr></thead><tbody>' + ''.join(f'<tr><td>{html.escape(k)}</td><td>{inline(v)}</td></tr>' for k, v in d['modelos'].items()) + '</tbody></table></div>')
        H.append('</section>')
    # metodología
    H.append('<h2 id="metodo">Metodología y fuentes</h2><p>Para cada vendor se analizó su propuesta de implementación leyendo directamente sus documentos (propuesta técnica y anexos): metodología y fases, cronograma, equipo e implementador, gobierno, migración, pruebas, transición, supuestos y responsabilidades del Banco. Cada pro y contra lleva su fuente (documento y página) y un nivel de confianza: ALTA si hay cifra, fecha o compromiso explícito; MEDIA si está descrito sin cifra; BAJA si es una afirmación genérica o solo declarada.</p>' + ('<p>Cuando existe, se añade la rúbrica corporativa de implementación del Banco: 12 criterios de estrategia de implementación, 24 de perfil del fabricante y 25 de perfil del implementador, cada uno con peso relativo y una escala de 0 a 5 cuyos niveles tienen un descriptor textual. El puntaje de cada criterio es el descriptor que mejor describe lo que los documentos del vendor demuestran, con la cita exacta (documento, página o fila, sección). Las respuestas del vendor en su anexo de perfiles se tratan como declaraciones: si ningún otro documento las respalda, el criterio queda como «Solo declarado» y no supera la mitad del puntaje máximo. Las sesiones de referenciación no forman parte de este documento por ser entrevistas. </p>' if con_impl else '') + '<p>Cada vendor se analizó de forma aislada, con sus propios documentos; la comparación solo agrega lo verificado por vendor.</p>')
    H.append('<p>Archivos de origen por vendor: <code>verif/IMPL.md</code> (rúbrica puntuada), <code>informes/7_implementacion_pros_contras.md</code> (ficha, pros y contras), <code>informes/8_modelo_despliegue.md</code> (modelo de despliegue, cuando existe). Este documento fue generado por <code>scripts/07_informe_implementacion.py</code> sin añadir texto propio.</p>')
    # anexo
    if con_impl: H.append('<h2 id="anexo">Anexo: criterios completos por vendor (rúbrica corporativa)</h2>' + leyenda_escala())
    for d in con_impl:
        H.append(f'<h3 class="vendor">{html.escape(d["vendor"])} — Estrategia de implementación (EI)</h3>' + tabla_criterios(d['crit']['EI']))
        H.append(f'<h3>{html.escape(d["vendor"])} — Perfil del fabricante (F)</h3>' + tabla_criterios(d['crit']['F'], con_resp=True))
        H.append(f'<h3>{html.escape(d["vendor"])} — Perfil del implementador (I)</h3>' + tabla_criterios(d['crit']['I'], con_impl=True, con_resp=True))
    H.append(f'<footer>Informe generado el {hoy}. Escala y pesos: rúbrica corporativa de implementación del Banco. Sin ranking ni recomendación.</footer></div></body></html>')
    return '\n'.join(H)

# ----------------------------------------------------------------------------- PDF
def a_pdf(html_path: Path, pdf_path: Path):
    cands = []
    if platform.system() == 'Windows':
        cands += [r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
                  r'C:\Program Files\Google\Chrome\Application\chrome.exe', r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe']
    elif platform.system() == 'Darwin':
        cands += ['/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Chromium.app/Contents/MacOS/Chromium']
    cands += [shutil.which(x) for x in ('msedge', 'microsoft-edge', 'google-chrome', 'chromium', 'chromium-browser', 'chrome') if shutil.which(x)]
    exe = next((c for c in cands if c and Path(c).exists()), None)
    if not exe:
        print("No encontré Edge ni Chrome para generar el PDF. Abre el HTML en el navegador y usa Imprimir → Guardar como PDF."); return False
    cmd = [exe, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', f'--print-to-pdf={pdf_path}', html_path.resolve().as_uri()]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if pdf_path.exists() and pdf_path.stat().st_size > 1000: print(f'PDF: {pdf_path}'); return True
    r2 = subprocess.run([exe, '--headless', '--disable-gpu', '--no-pdf-header-footer', f'--print-to-pdf={pdf_path}', html_path.resolve().as_uri()], capture_output=True, text=True, timeout=180)
    ok = pdf_path.exists() and pdf_path.stat().st_size > 1000
    print(f'PDF: {pdf_path}' if ok else f'No se pudo generar el PDF con {exe}. Abre el HTML e imprime a PDF.'); return ok

def main():
    args = [a for a in sys.argv[1:]]; pdf = '--pdf' in args; salida = None
    if '--salida' in args: salida = Path(args[args.index('--salida') + 1]); args.remove('--salida'); args.remove(str(salida))
    vendors = [a for a in args if not a.startswith('--')]
    if not vendors: vendors = sorted(p.name for p in VENDORS.iterdir() if p.is_dir() and ((p / 'verif' / 'IMPL.md').exists() or (p / 'informes' / '7_implementacion_pros_contras.md').exists()))
    if not vendors: sys.exit("Ningún vendor tiene verif/IMPL.md ni informes/7_implementacion_pros_contras.md. Ejecuta antes la verificación o el informe de implementación.")
    data = [cargar_vendor(v) for v in vendors]
    comp = VENDORS / 'COMPARATIVO_IMPLEMENTACION.md'; comp_md = comp.read_text(encoding='utf-8') if comp.exists() else ''
    hoy = datetime.date.today().strftime('%d-%m-%Y')
    out = salida or (VENDORS / 'INFORME_IMPLEMENTACION.html'); out.write_text(construir(data, comp_md, hoy), encoding='utf-8')
    print(f'HTML: {out}  ({len(data)} vendors: {", ".join(d["vendor"] + ("" if d["ok"] else " [sin IMPL]") for d in data)})')
    if pdf: a_pdf(out, out.with_suffix('.pdf'))

if __name__ == '__main__':
    main()
