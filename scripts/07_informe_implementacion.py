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
    python scripts/07_informe_implementacion.py --artefacto    # fragmento para publicar como artefacto de claude.ai
    python scripts/07_informe_implementacion.py --ejecutivo --pdf        # resumen ejecutivo: comparativo + una página por vendor
    python scripts/07_informe_implementacion.py --vendor sunline --pdf   # especificación de un vendor (vertical, con los 61 criterios)
    python scripts/07_informe_implementacion.py --todo --pdf             # ejecutivo + una especificación por vendor
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
def leer_md(path):
    t = path.read_text(encoding='utf-8-sig')
    for a, b in (('a¦ü', 'á'), ('e¦ü', 'é'), ('i¦ü', 'í'), ('o¦ü', 'ó'), ('u¦ü', 'ú'), ('A¦ü', 'Á'), ('E¦ü', 'É'), ('O¦ü', 'Ó'), ('n¦ā', 'ñ')): t = t.replace(a, b)
    t = re.sub(r'(?i)b[uú]squedas?\s+en\s+docs/txt(\s+del\s+vendor)?', 'Búsqueda en todos los documentos del vendor', t)
    return t

def cargar_vendor(v):
    d = VENDORS / v; data = {'vendor': v, 'ok': False, 'crit': {'EI': [], 'F': [], 'I': []}, 'resumen': {}, 'ceros': 0, 'declarados': 0, 'implementadores': ['—'], 'tiene_impl': False}
    impl = d / 'verif' / 'IMPL.md'; f7 = d / 'informes' / '7_implementacion_pros_contras.md'
    if not impl.exists() and not f7.exists(): return data
    data['ok'] = True
    if impl.exists():
      data['tiene_impl'] = True; md = leer_md(impl); secs = sections(md); data['impl_secs'] = secs
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
        md7 = leer_md(f7); s7 = sections(md7); data['f7_secs'] = s7
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
        s8 = sections(leer_md(f8)); data['s8'] = s8
        data['desp_modelos'] = find_section(s8, 'Modelos'); data['desp_nubes'] = find_section(s8, 'Nubes')
        data['desp_region'] = find_section(s8, 'Region', 'Región'); data['desp_no'] = find_section(s8, 'No soporta')
        data['desp_contra'] = find_section(s8, 'Contradicciones')
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

def svg_barras_h(items, titulo, maxv=100, fmt=lambda x: f'{x:.1f}', ancho=560, color=None):
    """items: [(etiqueta, valor)] — barras horizontales, una tinta, etiqueta directa."""
    fila, top, izq = 26, 8, 170; alto = top + fila * len(items) + 8; w = ancho - izq - 70
    s = [f'<svg class="chart" viewBox="0 0 {ancho} {alto}" role="img" aria-label="{html.escape(titulo)}">']
    for k, (lab, val) in enumerate(items):
        y = top + k * fila; v = 0 if val is None else val; bw = max(0, w * v / maxv)
        s.append(f'<text x="{izq-8}" y="{y+16}" text-anchor="end" class="lbl">{html.escape(lab[:28])}</text>')
        s.append(f'<rect x="{izq}" y="{y+4}" width="{w}" height="16" class="track"/>')
        if val is not None: s.append(f'<rect x="{izq}" y="{y+4}" width="{bw:.1f}" height="16" rx="3" fill="{color or RAMP[3]}"><title>{html.escape(lab)}: {fmt(val)}</title></rect>')
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
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&family=Source+Sans+3:ital,wght@0,400;0,500;0,600;1,400&family=JetBrains+Mono:wght@400;500&display=swap">'
CSS = """
/* Layout: dashboard de comité. Portada con una tarjeta por vendor, scorecard de una página, gráficos grandes con color por
   vendor, y una sección por vendor compuesta de fichas (no tablas). Las tablas completas viven solo en el anexo. */
:root{
  --bg:#f5f6f8; --bg-2:#eaedf1; --panel:#ffffff; --line:#d6dbe3; --line-2:#b9c1cc;
  --ink:#10151d; --ink-2:#47505d; --ink-3:#7a8392;
  --accent:#1c5cab; --accent-soft:#e2ecf9; --track:#e3e7ed;
  --display:"Manrope","Segoe UI",system-ui,sans-serif;
  --body:"Source Sans 3","Segoe UI",system-ui,sans-serif;
  --mono:"JetBrains Mono",ui-monospace,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){ --bg:#0f1318; --bg-2:#171c23; --panel:#161b22; --line:#2a313b; --line-2:#3a4350; --ink:#eef1f5; --ink-2:#b8c0cc; --ink-3:#84909f; --accent:#6da7ec; --accent-soft:#1a2a40; --track:#262d37; color-scheme:dark } }
:root[data-theme="dark"]{ --bg:#0f1318; --bg-2:#171c23; --panel:#161b22; --line:#2a313b; --line-2:#3a4350; --ink:#eef1f5; --ink-2:#b8c0cc; --ink-3:#84909f; --accent:#6da7ec; --accent-soft:#1a2a40; --track:#262d37; color-scheme:dark }
*{box-sizing:border-box} html{font-size:15px}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--body);line-height:1.45;font-variant-numeric:tabular-nums}
.wrap{max-width:1180px;margin:0 auto;padding-block:0 64px;padding-inline:clamp(16px,4vw,40px)}
h1,h2,h3,h4{font-family:var(--display);text-wrap:balance;letter-spacing:-.01em}
h1{font-size:clamp(2rem,4.6vw,2.9rem);line-height:1.05;margin:0;font-weight:800}
h2{font-size:1.65rem;line-height:1.15;margin:2.4rem 0 .8rem;font-weight:800;page-break-after:avoid}
h3{font-size:1.15rem;margin:1.6rem 0 .5rem;font-weight:700;page-break-after:avoid}
h4{font-size:.78rem;margin:1.1rem 0 .4rem;color:var(--ink-3);text-transform:uppercase;letter-spacing:.1em;font-weight:700}
p{margin:.3rem 0 .7rem;max-width:76ch} .small{font-size:.82rem;color:var(--ink-2);max-width:86ch} .fuente{color:var(--ink-3);font-size:.76rem;line-height:1.35}
.kicker{font-family:var(--display);letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-size:.74rem;font-weight:700}
.eyebrow{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;padding:14px 0 10px;border-bottom:1px solid var(--line);margin-bottom:12px}
.eyebrow .meta{margin:0;font-size:.82rem;color:var(--ink-3)}
header.portada{padding-block:28px 24px;display:grid;gap:18px;page-break-after:always}
.portada .lead{font-size:1rem;color:var(--ink-2);max-width:78ch;margin:0}
.vcards{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px;margin-top:6px}
.vcard{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:0 0 12px;overflow:hidden;min-width:0;page-break-inside:avoid;display:flex;flex-direction:column;gap:10px}
.vcard .band{height:8px;background:var(--vc)} .vcard .body{padding:0 16px;display:flex;flex-direction:column;gap:10px}
.vcard .name{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap} .vcard .name b{font-family:var(--display);font-size:1.2rem;font-weight:800}
.vcard .name .tag{font-size:.74rem;color:var(--ink-3)} .vcard .tit{font-size:.88rem;color:var(--ink-2);margin:0;line-height:1.35}
.facts{display:grid;grid-template-columns:1fr 1fr;gap:6px 14px;font-size:.82rem} .facts div{min-width:0} .facts .k{color:var(--ink-3);font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;font-family:var(--display);font-weight:700} .facts .v{color:var(--ink);line-height:1.3}
.mini{display:grid;gap:5px} .mini .row{display:grid;grid-template-columns:92px 1fr 46px;align-items:center;gap:8px;font-size:.78rem} .mini .lab{color:var(--ink-2)} .mini .bar{height:9px;background:var(--track);border-radius:4px;overflow:hidden} .mini .bar i{display:block;height:100%;background:var(--vc);border-radius:4px} .mini .num{font-family:var(--mono);text-align:right;font-size:.78rem}
.chips{display:flex;gap:6px;flex-wrap:wrap} .chip{display:inline-flex;align-items:center;gap:6px;min-height:22px;border-radius:5px;padding:0 8px;font-size:.74rem;font-weight:700;font-family:var(--display);background:var(--bg-2);color:var(--ink-2);border:1px solid var(--line);letter-spacing:.02em;white-space:nowrap}
.chip.si{background:var(--accent-soft);color:var(--accent);border-color:transparent} .chip.no{color:var(--ink-3)} .chip.cond{border-color:var(--line-2)}
.chip.sc{min-width:28px;justify-content:center;font-family:var(--mono);border:0}
.toc{margin-top:4px} .toc ol{columns:3;column-gap:28px;padding-left:1.1rem;margin:0;font-size:.88rem} .toc li{margin:.1rem 0;break-inside:avoid} .toc a{color:var(--ink);text-decoration:none} .toc a:hover,.toc a:focus-visible{color:var(--accent);outline:none}
@media(max-width:760px){.toc ol{columns:1}}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(124px,1fr));gap:10px;margin:.6rem 0 1.2rem}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px 16px;min-width:0} .kpi .n{font-family:var(--mono);font-size:1.9rem;font-weight:500;color:var(--accent);line-height:1} .kpi.v .n{color:var(--vc)}
.kpi .l{font-size:.76rem;color:var(--ink-2);margin-top:6px;line-height:1.3}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px;min-width:0;page-break-inside:avoid}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:18px} .grid2>*{min-width:0}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px} .grid3>*{min-width:0}
.chart{width:100%;height:auto;display:block;margin:.3rem 0 .6rem;max-width:100%} .chart .lbl{font-size:12px;fill:var(--ink-2);font-family:var(--body)} .chart .lbl.b{font-weight:700;fill:var(--ink);font-family:var(--display)}
.chart .val{font-size:12px;fill:var(--ink);font-weight:500;font-family:var(--mono)} .chart .cell{font-size:12px;font-weight:600;font-family:var(--mono)} .chart .track{fill:var(--track)} .chart .grid{stroke:var(--line);stroke-width:1} .chart .axis{font-size:11px;fill:var(--ink-3);font-family:var(--mono)}
.legend{display:flex;gap:12px;flex-wrap:wrap;font-size:.8rem;color:var(--ink-2);margin:.2rem 0 .6rem} .legend span{display:inline-flex;align-items:center;gap:6px} .legend i{width:12px;height:12px;border-radius:3px;display:inline-block}
.score-table{width:100%;border-collapse:separate;border-spacing:0 6px;font-size:.86rem} .score-table th{text-align:left;font-family:var(--display);font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-3);padding:0 10px 2px;font-weight:700}
.score-table td{background:var(--panel);padding:10px;border-top:1px solid var(--line);border-bottom:1px solid var(--line);vertical-align:middle;min-width:0} .score-table td:first-child{border-left:6px solid var(--vc);border-radius:8px 0 0 8px;font-family:var(--display);font-weight:800} .score-table td:last-child{border-right:1px solid var(--line);border-radius:0 8px 8px 0}
.inl{display:grid;grid-template-columns:36px 1fr;align-items:center;gap:6px;white-space:nowrap} .inl .num{text-align:left} .score-table .pct{width:110px;min-width:110px;max-width:120px} .score-table td+td{border-left:1px solid var(--line)} .score-table td.txt{font-size:.74rem;line-height:1.35} .inl .bar{height:10px;background:var(--track);border-radius:4px;overflow:hidden} .inl .bar i{display:block;height:100%;background:var(--vc);border-radius:4px} .inl .num{font-family:var(--mono);font-size:.8rem;text-align:right}
.cards{list-style:none;padding:0;margin:0;counter-reset:c;display:grid;gap:8px} .cards li{counter-increment:c;min-width:0} .card{background:var(--panel);border:1px solid var(--line);border-left:5px solid var(--vc,var(--accent));border-radius:8px;padding:10px 12px;page-break-inside:avoid}
.cards.contras .card{border-left-color:var(--line-2)} .card-h{display:flex;gap:8px;align-items:flex-start} .card-h .chip{flex:none;height:20px;font-size:.66rem} .card-t{font-weight:600;font-size:.9rem;min-width:0;line-height:1.35} .card-t::before{content:counter(c) " ";color:var(--ink-3);font-family:var(--mono);font-weight:500}
.ficha{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px} .ficha .f{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px 12px;min-width:0;page-break-inside:avoid} .ficha .k{font-family:var(--display);font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-3);font-weight:700;display:flex;justify-content:space-between;gap:8px} .ficha .v{font-size:.88rem;margin:4px 0 6px;line-height:1.35}
.vendor{page-break-before:always} .vhead{display:flex;align-items:center;gap:14px;flex-wrap:wrap;padding:10px 0 6px;border-top:6px solid var(--vc);margin-top:1.6rem} .vhead h2{margin:0;border:0;padding:0} .vhead .tag{font-size:.8rem;color:var(--ink-3)}
.nota{background:var(--accent-soft);border-left:4px solid var(--vc,var(--accent));padding:12px 16px;border-radius:0 8px 8px 0;margin:.8rem 0 1rem;font-size:.95rem;max-width:none}
.desp{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px} .desp .d{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px 12px;min-width:0;page-break-inside:avoid;display:grid;gap:4px} .desp .d .top{display:flex;justify-content:space-between;gap:8px;align-items:center;flex-wrap:wrap} .desp .d .m{font-family:var(--display);font-weight:800} .desp .d .t{font-size:.84rem;color:var(--ink-2)}
.tbl-wrap{overflow-x:auto;margin:.6rem 0 1.2rem;min-width:0} table{border-collapse:collapse;width:100%;font-size:.82rem}
th{text-align:left;background:var(--bg-2);color:var(--ink-2);font-family:var(--display);font-weight:700;font-size:.74rem;letter-spacing:.04em;text-transform:uppercase;padding:8px 10px;border-bottom:2px solid var(--line-2);vertical-align:bottom}
td{padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
.pill{display:inline-block;padding:1px 8px;border-radius:4px;font-size:.72rem;font-weight:700;background:var(--bg-2);color:var(--ink-2);border:1px solid var(--line);font-family:var(--display);white-space:nowrap}
.pill.doc{border-color:var(--accent);color:var(--accent)} .pill.dec{border-color:var(--line-2)} .pill.no{color:var(--ink-3)}
.score{display:inline-block;min-width:26px;text-align:center;border-radius:4px;padding:1px 6px;font-weight:600;font-size:.8rem;font-family:var(--mono)}
ol,ul{padding-left:1.25rem} li{margin:.2rem 0;max-width:86ch} .compact li{font-size:.9rem}
blockquote{margin:.6rem 0;padding:.2rem 0 .2rem 14px;border-left:3px solid var(--line-2);color:var(--ink-2)}
code{font-family:var(--mono);font-size:.85em;background:var(--bg-2);padding:1px 4px;border-radius:3px}
footer{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--line);color:var(--ink-2);font-size:.82rem}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@page{size:A4 landscape;margin:12mm 12mm 14mm}
@media print{html{font-size:10.5px} h1{font-size:2rem} header.portada{gap:10px;padding-block:10px 6px} .portada .lead{font-size:.85rem;max-width:none} .eyebrow{padding:8px 0 6px} .vcards{gap:10px} .vcard .body{gap:6px;padding:0 12px} .vcard .band{height:6px} .vcard .tit{font-size:.78rem;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden} .facts .v{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden} .toc{margin-top:0} .toc ol{font-size:.78rem} .facts{font-size:.76rem} .mini .row{grid-template-columns:80px 1fr 40px} .kpis{grid-template-columns:repeat(7,1fr)} :root{--bg:#fff;--panel:#fff} .wrap{max-width:none;padding-inline:0} .vcards{grid-template-columns:repeat(3,1fr)} .grid2{grid-template-columns:1fr 1fr} .ficha{grid-template-columns:repeat(3,1fr)} .desp{grid-template-columns:repeat(2,1fr)} .toc ol{columns:3} tr,td,th,.card,.kpi,.panel,.vcard,.f,.d{page-break-inside:avoid} .chart{page-break-inside:avoid} *{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""

# ----------------------------------------------------------------------------- identidad por vendor
VENDOR_PAL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948']   # orden validado (dataviz)
VENDOR_INK = ['#ffffff', '#ffffff', '#0b0b0b', '#0b0b0b', '#0b0b0b', '#ffffff', '#ffffff', '#ffffff']
NOMBRES_VENDOR = {'fis': 'FIS', 'infosys': 'Infosys', 'pismo': 'Pismo', 'sunline': 'Sunline', 'temenos': 'Temenos', 'tm': 'Thought Machine', 'tought-machine': 'Thought Machine', 'thought-machine': 'Thought Machine'}
def nombre(v): return NOMBRES_VENDOR.get(v.lower(), v.replace('-', ' ').title())
def nombres_en_texto(texto):
    """Pone el nombre real del vendor donde el comparativo usa la carpeta (sunline, tought-machine…)."""
    for slug, real in sorted(NOMBRES_VENDOR.items(), key=lambda kv: -len(kv[0])):
        texto = re.sub(r'(?<![\w-])' + re.escape(slug) + r'(?![\w-])', real, texto, flags=re.IGNORECASE)
    return texto

def primera_cita(fuente):
    """Primera cita documental de una cadena «Doc p.x; Doc2 p.y» (sin la cita literal entre comillas)."""
    f = re.split(r'\s*;\s*', str(fuente or '').strip())[0]
    f = re.sub(r'\s*[-–—]\s*["“].*$', '', f).strip().rstrip('.')
    return f

def ficha_fuente(d, *claves):
    f = d.get('ficha', {})
    for k, val in f.items():
        if any(_norm(c) in _norm(k) for c in claves): return val.get('fuente', '')
    return ''

TEMAS_TRANSVERSAL = [
    (('hypercare', 'estabilizacion'), 'ficha', ('hypercare',)),
    (('despliegue', 'saas', 'paas', 'nube'), 'despliegue', ()),
    (('evidencia de implementador', 'porcentaje i', 'perfil del implementador'), 'rubrica_i', ()),
    (('migracion', 'integracion', 'carga al banco'), 'ficha', ('migración', 'migracion')),
    (('plazo', 'duracion', 'cronograma', 'meses'), 'ficha', ('duración', 'duracion')),
    (('modelo de implementacion', 'fabricante', 'implementador', 'terceros'), 'ficha', ('implementador',)),
]

def fuentes_reales(texto, vendors_data):
    """Para un punto del comparativo, devuelve [(vendor, cita documental)] tomadas de los informes de cada vendor."""
    t = _norm(texto)
    for claves, tipo, campos in TEMAS_TRANSVERSAL:
        if any(c in t for c in claves):
            out = []
            for d in vendors_data:
                cita = ''
                if tipo == 'ficha': cita = primera_cita(ficha_fuente(d, *campos))
                elif tipo == 'rubrica_i':
                    filas = d['crit']['I']
                    fila = next((c for c in filas if _norm(c.get('respaldo')) != 'no encontrado'), filas[0] if filas else None)
                    cita = primera_cita(fila['evidencia']) if fila else ''
                elif tipo == 'despliegue':
                    lineas = [l for l in str(d.get('desp_modelos', '')).split('\n') if l.strip().startswith('|')]
                    hdr, rows = parse_table(lineas) if lineas else ([], [])
                    if hdr:
                        ifu = next((i for i, h in enumerate(hdr) if _norm(h).startswith('fuente')), None)
                        if ifu is not None:
                            for r in rows:
                                if _norm(r[0]) in ('saas', 'paas') and len(r) > ifu and r[ifu].strip(): cita = primera_cita(r[ifu]); break
                out.append((nombre(d['vendor']), cita or 'sin cita documental en su informe'))
            return out
    return []

def transversal_html(md, vendors_data=None):
    """Lista numerada del comparativo transversal: cada punto con su línea «Fuentes» atenuada debajo."""
    items = []
    for l in md.split('\n'):
        if not l.strip(): continue
        if re.match(r'^\s*\d+[.)]\s+', l): items.append([re.sub(r'^\s*\d+[.)]\s+', '', l).strip(), []])
        elif items and re.match(r'^\s*[-*•]\s+', l): items[-1][1].append(re.sub(r'^\s*[-*•]\s+', '', l).strip())
        elif items: items[-1][0] += ' ' + l.strip()
    out = []
    for texto, subs in items:
        fuentes = [re.sub(r'^fuentes?\s*:\s*', '', x, flags=re.IGNORECASE).rstrip('.') for x in subs if re.match(r'^fuentes?\s*:', x, flags=re.IGNORECASE)]
        otros = [x for x in subs if not re.match(r'^fuentes?\s*:', x, flags=re.IGNORECASE)]
        cuerpo = inline(nombres_en_texto(texto)) + ''.join(f' {inline(nombres_en_texto(x))}' for x in otros)
        reales = fuentes_reales(texto, vendors_data or [])
        if reales: cuerpo += '<span class="fuente">Fuentes: ' + ' · '.join(f'<b>{html.escape(v)}</b>: {html.escape(c)}' for v, c in reales) + '.</span>'
        elif fuentes: cuerpo += f'<span class="fuente">Fuentes: {inline(fuentes_legibles("; ".join(fuentes)))}.</span>'
        out.append(f'<li>{cuerpo}</li>')
    return '<ol class="trans">' + ''.join(out) + '</ol>'

def fuentes_legibles(texto):
    """Sustituye nombres de archivos .md por descripciones con el nombre real del vendor."""
    def nom(v): return nombre(v.strip())
    texto = re.sub(r'(?:vendors/)?(?:[\w-]+/)*7_implementacion_pros_contras_([\w-]+)\.md', lambda m: f'informe de implementación de {nom(m.group(1))}', texto)
    texto = re.sub(r'(?:vendors/)?(?:[\w-]+/)*8_modelo_despliegue_([\w-]+)\.md', lambda m: f'análisis de despliegue de {nom(m.group(1))}', texto)
    texto = re.sub(r'(?:vendors/)?(?:[\w-]+/)*IMPL_([\w-]+)\.md', lambda m: f'rúbrica de implementación de {nom(m.group(1))}', texto)
    texto = re.sub(r'vendors/([\w-]+)/verif/IMPL\.md', lambda m: f'rúbrica de implementación de {nom(m.group(1))}', texto)
    texto = re.sub(r'vendors/([\w-]+)/informes/7_implementacion_pros_contras\.md', lambda m: f'informe de implementación de {nom(m.group(1))}', texto)
    texto = re.sub(r'vendors/([\w-]+)/informes/8_modelo_despliegue\.md', lambda m: f'análisis de despliegue de {nom(m.group(1))}', texto)
    return texto

def recorta(t, n):
    t = (t or '').strip()
    if len(t) <= n: return t
    c = t[:n].rsplit(' ', 1)[0]
    return c.rstrip(' ,;:') + '…'
def vcolor(i): return VENDOR_PAL[i % len(VENDOR_PAL)]

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

def chip_modelo(txt):
    t = (txt or '').strip(); tl = _norm(t)
    cls = 'si' if tl.startswith('si') or tl.startswith('sí') else 'no' if tl.startswith('no (') or tl == 'no' or tl.startswith('no ') and 'especific' not in tl else 'cond' if 'condicion' in tl else ''
    corto = re.split(r'[(:;]', t)[0].strip()[:18] or '—'
    return cls, corto

def svg_barras_vendor(vendors_data, key, maxv=100, ancho=720):
    """Barras horizontales, una por vendor, color por vendor, etiqueta directa."""
    fila, top, izq = 30, 10, 150; alto = top + fila * len(vendors_data) + 24; w = ancho - izq - 70
    s = [f'<svg class="chart" viewBox="0 0 {ancho} {alto}" role="img" aria-label="Porcentaje por vendor">']
    for g in (0, 25, 50, 75, 100):
        x = izq + w * g / maxv; s.append(f'<line x1="{x:.1f}" y1="{top-4}" x2="{x:.1f}" y2="{alto-18}" class="grid"/><text x="{x:.1f}" y="{alto-4}" text-anchor="middle" class="axis">{g}%</text>')
    for k, d in enumerate(vendors_data):
        y = top + k * fila; v = d['resumen'].get(key); col = vcolor(d['_i'])
        s.append(f'<text x="{izq-10}" y="{y+16}" text-anchor="end" class="lbl b">{html.escape(nombre(d["vendor"]))}</text>')
        if v is None: s.append(f'<text x="{izq+6}" y="{y+16}" class="lbl">sin rúbrica</text>'); continue
        bw = w * v / maxv
        s.append(f'<rect x="{izq}" y="{y+4}" width="{bw:.1f}" height="18" rx="4" fill="{col}"><title>{html.escape(nombre(d["vendor"]))}: {v:.1f}%</title></rect>')
        s.append(f'<text x="{izq+bw+8:.1f}" y="{y+17}" class="val">{v:.1f}%</text>')
    s.append('</svg>'); return '\n'.join(s)

def svg_puntos_criterios(vendors_data, ei_cods, ei_names, ancho=1000):
    """Dot plot: fila por criterio EI, un punto por vendor (color por vendor) sobre la escala 0–5, con etiqueta del puntaje."""
    fila, top, izq = 34, 30, 330; w = ancho - izq - 40; alto = top + fila * len(ei_cods) + 20
    s = [f'<svg class="chart" viewBox="0 0 {ancho} {alto}" role="img" aria-label="Puntaje por criterio y vendor">']
    for g in range(6):
        x = izq + w * g / 5; s.append(f'<line x1="{x:.1f}" y1="{top-6}" x2="{x:.1f}" y2="{alto-16}" class="grid"/><text x="{x:.1f}" y="{top-12}" text-anchor="middle" class="axis">{g}</text>')
    for i, cod in enumerate(ei_cods):
        y = top + i * fila + 16
        s.append(f'<text x="{izq-12}" y="{y+4}" text-anchor="end" class="lbl">{html.escape(cod)} {html.escape(ei_names[cod][:40])}</text>')
        s.append(f'<line x1="{izq}" y1="{y}" x2="{izq+w}" y2="{y}" class="grid"/>')
        # agrupar vendors por puntaje para desplazar los que coinciden
        grupos = {}
        for d in vendors_data:
            p = next((c['puntaje'] for c in d['crit']['EI'] if c['codigo'] == cod), None)
            if p is not None: grupos.setdefault(p, []).append(d)
        for p, ds in grupos.items():
            x = izq + w * p / 5; n = len(ds)
            for j, d in enumerate(ds):
                off = (j - (n - 1) / 2) * 13
                s.append(f'<circle cx="{x+off:.1f}" cy="{y}" r="7" fill="{vcolor(d["_i"])}" stroke="var(--panel)" stroke-width="2"><title>{html.escape(nombre(d["vendor"]))} · {html.escape(cod)}: {p}</title></circle>')
    s.append('</svg>'); return '\n'.join(s)

def legend_vendors(vendors_data):
    return '<div class="legend">' + ''.join(f'<span><i style="background:{vcolor(d["_i"])}"></i>{html.escape(nombre(d["vendor"]))}</span>' for d in vendors_data) + '</div>'

def svg_confianza(vendors_data, clave, titulo, ancho=640):
    fila, top, izq = 30, 8, 150; alto = top + fila * len(vendors_data) + 8; w = ancho - izq - 44
    maxn = max((sum(conteo_conf(d.get(clave, [])).values()) for d in vendors_data), default=1) or 1
    sv = [f'<svg class="chart" viewBox="0 0 {ancho} {alto}" role="img" aria-label="{html.escape(titulo)}">']
    for k, d in enumerate(vendors_data):
        y = top + k * fila; c = conteo_conf(d.get(clave, [])); x = izq
        sv.append(f'<text x="{izq-10}" y="{y+18}" text-anchor="end" class="lbl b">{html.escape(nombre(d["vendor"]))}</text>')
        for lvl in ('ALTA', 'MEDIA', 'BAJA'):
            n = c[lvl]
            if not n: continue
            bw = w * n / maxn
            sv.append(f'<rect x="{x:.1f}" y="{y+5}" width="{max(bw-2,1):.1f}" height="18" rx="4" fill="{CONF_COL[lvl]}"><title>{html.escape(nombre(d["vendor"]))}: {n} {lvl}</title></rect>')
            if bw > 16: sv.append(f'<text x="{x+bw/2-1:.1f}" y="{y+18}" text-anchor="middle" class="cell" fill="{CONF_INK[lvl]}">{n}</text>')
            x += bw
        sv.append(f'<text x="{x+6:.1f}" y="{y+18}" class="val">{sum(c.values())}</text>')
    sv.append('</svg>'); return '\n'.join(sv)

def tarjetas(items, tipo):
    if not items: return '<p class="small">Sin datos.</p>'
    out = [f'<ol class="cards {tipo}">']
    for it in items:
        conf = it.get('confianza') or ''
        chip = f'<span class="chip" style="background:{CONF_COL.get(conf, "#e8e7e3")};color:{CONF_INK.get(conf, "#52514e")}">{conf or "s/c"}</span>' if conf else ''
        if it.get('fuente') or it.get('importa'):
            out.append(f'<li><div class="card"><div class="card-h">{chip}<span class="card-t">{inline(it["afirmacion"])}</span></div>' + (f'<div class="fuente">Fuente: {inline(it["fuente"])}</div>' if it.get('fuente') else '') + (f'<div class="small">{inline(it["importa"])}</div>' if it.get('importa') else '') + '</div></li>')
        else:
            out.append(f'<li><div class="card"><div class="card-h">{chip}<span class="card-t">{inline(it["texto"])}</span></div></div></li>')
    out.append('</ol>'); return '\n'.join(out)

def ficha_cards(d):
    f = d.get('ficha', {})
    if not f: return ''
    out = ['<div class="ficha">']
    for k, val in f.items():
        out.append(f'<div class="f"><div class="k"><span>{html.escape(k.capitalize())}</span><span>{html.escape(val["conf"])}</span></div><div class="v">{inline(val["que"])}</div><div class="fuente">{inline(val["fuente"])}</div></div>')
    out.append('</div>'); return '\n'.join(out)

def despliegue_cards(d):
    """Tarjetas por modelo con condición, nubes, quién opera, fuente y confianza, desde la tabla «Modelos» del informe 8."""
    body = d.get('desp_modelos', '')
    if not body: return ''
    hdr, rows = first_table(body)
    if not hdr: return md_to_html(body)
    def ix(*p):
        for q in p:
            for i, c in enumerate(hdr):
                if _norm(c).startswith(_norm(q)): return i
        return None
    iM, iO, iC, iN, iQ, iF, iCf = ix('Modelo'), ix('Ofrecido'), ix('Condici'), ix('Nubes'), ix('Quien', 'Quién'), ix('Fuente'), ix('Confianza')
    out = ['<div class="desp">']
    for r in rows:
        r = r + [''] * (len(hdr) - len(r)); g = lambda i: r[i] if i is not None else ''
        cls, corto = chip_modelo(g(iO))
        out.append(f'<div class="d"><div class="top"><span class="m">{inline(g(iM))}</span><span class="chip {cls}">{html.escape(corto)}</span>' + (f'<span class="chip">{html.escape(g(iCf))}</span>' if g(iCf) else '') + '</div>'
                   + (f'<div class="t"><b>Condición:</b> {inline(g(iC))}</div>' if g(iC) and g(iC) != '—' else '')
                   + (f'<div class="t"><b>Nubes:</b> {inline(g(iN))}</div>' if g(iN) else '') + (f'<div class="t"><b>Opera:</b> {inline(g(iQ))}</div>' if g(iQ) else '')
                   + (f'<div class="fuente">Fuente: {inline(g(iF))}</div>' if g(iF) else '') + '</div>')
    out.append('</div>'); return '\n'.join(out)

def vendor_card(d):
    col = vcolor(d['_i']); cp, cc = conteo_conf(d.get('pros_items', [])), conteo_conf(d.get('contras_items', []))
    modelos = d.get('modelos', {}); chips = []
    for k, v in modelos.items():
        if re.match(r'^(SaaS|PaaS|On-?prem)', k, re.I):
            cls, corto = chip_modelo(v); chips.append(f'<span class="chip {cls}">{html.escape(k.split(" ")[0])}: {html.escape(corto)}</span>')
    mini = ''.join(f'<div class="row"><span class="lab">{lab}</span><span class="bar"><i style="width:{d["resumen"].get(k):.0f}%"></i></span><span class="num">{d["resumen"].get(k):.0f}%</span></div>' if d['resumen'].get(k) is not None else '' for k, lab in (('EI', 'Estrategia'), ('F', 'Fabricante'), ('I', 'Implementador')))
    return (f'<article class="vcard" style="--vc:{col}"><div class="band"></div><div class="body">'
            f'<div class="name"><b>{html.escape(nombre(d["vendor"]))}</b><span class="tag">{html.escape(recorta(ficha_get(d, "implementador"), 60))}</span></div>'
            f'<p class="tit">{inline(recorta(d.get("titular") or "", 170))}</p>'
            f'<div class="facts"><div><div class="k">Enfoque</div><div class="v">{inline(recorta(ficha_get(d, "enfoque"), 105))}</div></div><div><div class="k">Duración</div><div class="v">{inline(recorta(ficha_get(d, "duración", "duracion"), 90))}</div></div></div>'
            + (f'<div class="mini">{mini}</div>' if mini else '')
            + f'<div class="chips"><span class="chip si">{len(d.get("pros_items", []))} pros · {cp["ALTA"]} alta</span><span class="chip no">{len(d.get("contras_items", []))} contras · {cc["ALTA"]} alta</span>{"".join(chips)}</div>'
            '</div></article>')

def construir(vendors_data, comparativo_md, hoy, artefacto=False, ejecutivo=False):
    V = [d for d in vendors_data if d['ok']]; faltan = [d['vendor'] for d in vendors_data if not d['ok']]
    for i, d in enumerate(V): d['_i'] = i
    con_impl = [d for d in V if d['tiene_impl']]
    titulo = 'Estrategias de implementación'
    H = []
    if artefacto: H.append(f'<title>{titulo}</title>{FONTS}<style>{CSS}</style><div class="wrap">')
    else: H.append(f'<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{titulo}</title>{FONTS}<style>{CSS}</style></head><body><div class="wrap">')
    # ---------- portada: tarjetas por vendor
    H.append(f'<div class="eyebrow"><span class="kicker">Selección de core bancario · Evaluación técnica</span><p class="meta">Generado el {hoy} · {len(V)} vendors · sin ranking ni recomendación</p></div>')
    H.append('<header class="portada"><h1>Estrategias de implementación: comparativo de vendors</h1>')
    H.append('<p class="lead">Qué propone cada vendor para implantar el core, con qué equipo y en cuánto tiempo, y qué tan respaldado está por sus documentos. Las cifras de rúbrica salen de la rúbrica corporativa de implementación (61 criterios, escala 0 a 5); los pros y contras llevan fuente y nivel de confianza.' + (f' Sin verificación de implementación: {", ".join(faltan)}.' if faltan else '') + '</p>')
    H.append('<div class="vcards">' + ''.join(vendor_card(d) for d in V) + '</div>')
    H.append('<nav class="toc" aria-label="Contenido"><h4>Contenido</h4><ol><li><a href="#scorecard">Scorecard comparativo</a></li><li><a href="#graficos">Rúbrica y criterios</a></li><li><a href="#confianza">Pros y contras por confianza</a></li>' + ''.join(f'<li><a href="#v-{d["vendor"]}">{html.escape(nombre(d["vendor"]))}</a></li>' for d in V) + '<li><a href="#metodo">Metodología</a></li>' + ('<li><a href="#anexo">Anexo: 61 criterios por vendor</a></li>' if con_impl else '') + '</ol></nav></header>')
    # ---------- scorecard
    H.append('<h2 id="scorecard">Scorecard comparativo</h2><p class="small">Una fila por vendor. Las barras son el porcentaje de la rúbrica por bloque (Σ peso × puntaje / Σ peso × 5). «A» = pros o contras con confianza alta. El modelo de despliegue resume el análisis de despliegue de cada vendor; su evidencia está en la sección del vendor.</p>')
    H.append('<div class="tbl-wrap"><table class="score-table"><thead><tr><th>Vendor</th><th>Enfoque</th><th>Duración</th><th>Implementador</th><th class="pct">Estrategia</th><th class="pct">Fabricante</th><th class="pct">Implementador (rúbrica)</th><th>En 0</th><th>Pros A/total</th><th>Contras A/total</th><th>SaaS</th><th>PaaS</th></tr></thead><tbody>')
    for d in V:
        cp, cc = conteo_conf(d.get('pros_items', [])), conteo_conf(d.get('contras_items', []))
        def inl(k):
            v = d['resumen'].get(k)
            return f'<div class="inl"><span class="num">{v:.0f}%</span><span class="bar"><i style="width:{v:.0f}%"></i></span></div>' if v is not None else '<span class="small">—</span>'
        def mchip(nombre_modelo):
            for k, v in d.get('modelos', {}).items():
                if _norm(k).startswith(_norm(nombre_modelo)):
                    cls, corto = chip_modelo(v); return f'<span class="chip {cls}">{html.escape(corto)}</span>'
            return '<span class="small">—</span>'
        H.append(f'<tr style="--vc:{vcolor(d["_i"])}"><td>{html.escape(nombre(d["vendor"]))}</td><td class="txt">{inline(ficha_get(d, "enfoque"))}</td><td class="txt">{inline(ficha_get(d, "duración", "duracion"))}</td><td class="txt">{inline(ficha_get(d, "implementador"))}</td><td class="pct">{inl("EI")}</td><td class="pct">{inl("F")}</td><td class="pct">{inl("I")}</td><td class="num">{d["ceros"] if d["tiene_impl"] else "—"}</td><td>{cp["ALTA"]}/{len(d.get("pros_items", []))}</td><td>{cc["ALTA"]}/{len(d.get("contras_items", []))}</td><td>{mchip("SaaS")}</td><td>{mchip("PaaS")}</td></tr>')
    H.append('</tbody></table></div>')
    if comparativo_md:
        cs = sections(comparativo_md); trans = find_section(cs, 'transversal')
        if trans.strip(): H.append('<div class="panel"><h3 style="margin-top:0">Lo que cambia entre vendors</h3><p class="small">Diferencias que importan para la decisión, tomadas del comparativo de implementación. Debajo de cada punto, el documento de cada vendor donde está el dato (nombre oficial y página u hoja), tomado de su informe de implementación.</p><div class="compact cols2">' + transversal_html(trans, V) + '</div></div>')
    # ---------- rúbrica y criterios
    if con_impl:
        H.append('<h2 id="graficos">Rúbrica corporativa: puntaje por bloque y por criterio</h2>' + legend_vendors(V))
        H.append('<div class="grid3">' + ''.join(f'<div class="panel"><h4 style="margin-top:0">{nom}</h4>' + svg_barras_vendor(V, k) + '</div>' for k, nom in (('EI', 'Estrategia de implementación'), ('F', 'Perfil del fabricante'), ('I', 'Perfil del implementador'))) + '</div>')
        H.append('<p class="small">Los 0 % en «Perfil del implementador» corresponden a vendors que implementan directamente y no diligenciaron la hoja de implementadores: los 25 criterios del bloque quedaron en «0 — No informa».</p>')
        ei_cods = []; ei_names = {}
        for d in con_impl:
            for c in d['crit']['EI']:
                if c['codigo'] not in ei_names: ei_cods.append(c['codigo']); ei_names[c['codigo']] = c['criterio']
        if ei_cods:
            matriz = [[next((c['puntaje'] for c in d['crit']['EI'] if c['codigo'] == cod), None) for d in con_impl] for cod in ei_cods]
            if ejecutivo:
                H.append('<div class="panel"><h3 style="margin-top:0">Los 12 criterios de estrategia de implementación, vendor a vendor</h3><p class="small">Cada celda es la nota (0 a 5) que obtuvo el vendor en ese criterio de la rúbrica del Banco. 5 es el nivel máximo del criterio; 0 significa que la propuesta no lo presenta. El color acompaña a la nota: más oscuro, más alto.</p>' + leyenda_escala() + svg_heatmap([f'{c} {ei_names[c]}' for c in ei_cods], [nombre(d['vendor']) for d in con_impl], matriz) + '</div>')
            else:
                H.append('<div class="panel"><h3 style="margin-top:0">Los 12 criterios de estrategia, vendor a vendor</h3><p class="small">Cada punto es el puntaje de un vendor en ese criterio (0 a 5). Los puntos que coinciden se separan ligeramente.</p>' + legend_vendors(con_impl) + svg_puntos_criterios(con_impl, ei_cods, ei_names) + '</div>')
    # ---------- confianza
    H.append('<h2 id="confianza"' + (' class="salto"' if ejecutivo else '') + '>Pros y contras de cada vendor: cuántos y qué tan respaldados están</h2>')
    if ejecutivo: H.append('<p>Para cada vendor se identificaron hasta 10 pros (lo que su propuesta de implementación hace bien) y hasta 10 contras (brechas o riesgos). Cada uno se clasificó según qué tan respaldado está por los documentos del vendor: <strong>ALTA</strong>, hay una cifra, fecha o compromiso explícito con cita; <strong>MEDIA</strong>, está descrito pero sin cifra ni compromiso; <strong>BAJA</strong>, es una afirmación genérica o solo declarada. Las barras muestran cuántos pros y contras tiene cada vendor y de qué confianza. Un vendor con muchos pros de confianza BAJA promete más de lo que documenta.</p>')
    H.append(leyenda_conf())
    H.append('<div class="grid2"><div class="panel"><h4 style="margin-top:0">Pros</h4>' + svg_confianza(V, 'pros_items', 'Pros por confianza') + '</div><div class="panel"><h4 style="margin-top:0">Contras</h4>' + svg_confianza(V, 'contras_items', 'Contras por confianza') + '</div></div>')
    H.append('<p class="small">Confianza ALTA: cifra, fecha o compromiso explícito en un documento del vendor. MEDIA: descrito sin cifra. BAJA: afirmación genérica o solo declarada. Más pros no significa mejor propuesta: importa la confianza y el contenido de cada uno.</p>')
    # ---------- por vendor
    for n, d in enumerate(V, 1):
        col = vcolor(d['_i']); cp, cc = conteo_conf(d.get('pros_items', [])), conteo_conf(d.get('contras_items', []))
        H.append(f'<section class="vendor" id="v-{d["vendor"]}" style="--vc:{col}"><div class="vhead"><h2>{html.escape(nombre(d["vendor"]))}</h2><span class="tag">{html.escape(recorta(ficha_get(d, "implementador"), 90))}</span></div>')
        if d.get('titular'): H.append(f'<div class="nota">{inline(d["titular"])}</div>')
        H.append('<div class="kpis">' + ''.join(f'<div class="kpi v"><div class="n">{d["resumen"].get(k):.0f}%</div><div class="l">{lab}</div></div>' if d['resumen'].get(k) is not None else '' for k, lab in (('EI', 'rúbrica · estrategia'), ('F', 'rúbrica · fabricante'), ('I', 'rúbrica · implementador')))
                 + (f'<div class="kpi"><div class="n">{d["ceros"]}</div><div class="l">criterios en 0</div></div><div class="kpi"><div class="n">{d["declarados"]}</div><div class="l">solo declarados</div></div>' if d['tiene_impl'] else '')
                 + f'<div class="kpi"><div class="n">{len(d.get("pros_items", []))}</div><div class="l">pros · {cp["ALTA"]} con confianza alta</div></div><div class="kpi"><div class="n">{len(d.get("contras_items", []))}</div><div class="l">contras · {cc["ALTA"]} con confianza alta</div></div></div>')
        if d.get('ficha'): H.append('<h3>Ficha de la propuesta de implementación</h3>' + ficha_cards(d))
        if d['tiene_impl'] and d['crit']['EI']:
            H.append('<h3>Estrategia de implementación: puntaje por criterio</h3>' + svg_barras_h([(f'{c["codigo"]} {c["criterio"]}', c['puntaje']) for c in d['crit']['EI']], 'Puntaje EI', maxv=5, fmt=lambda x: f'{x:.0f} / 5', color=col))
        if d.get('pros_items') or d.get('contras_items'): H.append('<div class="grid2"><div><h3>Pros</h3>' + tarjetas(d.get('pros_items', []), 'pros') + '</div><div><h3>Contras</h3>' + tarjetas(d.get('contras_items', []), 'contras') + '</div></div>')
        if d.get('desp_modelos'):
            H.append('<h3>Modelo de despliegue y nubes</h3><p class="small">Cada tarjeta trae la fuente verificable (documento, página u hoja y fila, sección) y la confianza registradas en el análisis de despliegue.</p>' + despliegue_cards(d))
            if d.get('desp_nubes'): H.append('<h4>Nubes</h4>' + md_to_html(d['desp_nubes']))
            if d.get('desp_no', '').strip(): H.append('<h4>No soporta o no ofrece</h4><div class="compact">' + md_to_html(d['desp_no']) + '</div>')
        H.append('<div class="grid2">')
        for titulo_s, clave in (('Riesgos de ejecución', 'riesgos'), ('Lo que el Banco asume', 'asume'), ('Señales de alerta', 'alertas7'), ('Contradicciones', 'contradicciones'), ('Preguntas pendientes al vendor', 'preguntas7')):
            if d.get(clave, '').strip(): H.append(f'<div class="panel"><h3 style="margin-top:0">{titulo_s}</h3><div class="compact">' + md_to_html(d[clave]) + '</div></div>')
        H.append('</div></section>')
    # ---------- metodología
    H.append('<h2 id="metodo">Metodología y fuentes</h2><div class="grid2"><div class="panel"><h3 style="margin-top:0">Cómo se analizó</h3><p class="small">Para cada vendor se leyó directamente su propuesta de implementación (propuesta técnica y anexos): metodología y fases, cronograma, equipo e implementador, gobierno, migración, pruebas, transición, supuestos y responsabilidades del Banco. Cada pro y contra lleva su fuente y un nivel de confianza: ALTA si hay cifra, fecha o compromiso explícito; MEDIA si está descrito sin cifra; BAJA si es una afirmación genérica o solo declarada. Cada vendor se analizó de forma aislada; la comparación solo agrega lo verificado por vendor.</p></div>')
    H.append('<div class="panel"><h3 style="margin-top:0">La rúbrica</h3><p class="small">Rúbrica corporativa de implementación del Banco: 12 criterios de estrategia, 24 de perfil del fabricante y 25 de perfil del implementador, con peso relativo y escala de 0 a 5 con descriptor textual por nivel. El puntaje de cada criterio es el descriptor que mejor describe lo que los documentos del vendor demuestran, con cita. Las respuestas del anexo de perfiles son declaraciones: sin otro documento que las respalde quedan como «solo declarado» y no superan la mitad del máximo. Las sesiones de referenciación no se incluyen. Archivos de origen: <code>verif/IMPL.md</code>, <code>informes/7_implementacion_pros_contras.md</code>, <code>informes/8_modelo_despliegue.md</code>. Documento generado por <code>scripts/07_informe_implementacion.py</code> sin añadir texto propio.</p></div></div>')
    # ---------- anexo
    if con_impl: H.append('<h2 id="anexo">Anexo: los 61 criterios por vendor</h2>' + leyenda_escala())
    for d in con_impl:
        H.append(f'<h3 class="vendor" style="--vc:{vcolor(d["_i"])}">{html.escape(nombre(d["vendor"]))} — Estrategia de implementación (EI)</h3>' + tabla_criterios(d['crit']['EI']))
        H.append(f'<h3>{html.escape(nombre(d["vendor"]))} — Perfil del fabricante (F)</h3>' + tabla_criterios(d['crit']['F'], con_resp=True))
        H.append(f'<h3>{html.escape(nombre(d["vendor"]))} — Perfil del implementador (I)</h3>' + tabla_criterios(d['crit']['I'], con_impl=True, con_resp=True))
    H.append(f'<footer>Informe generado el {hoy}. Escala y pesos: rúbrica corporativa de implementación del Banco. Sin ranking ni recomendación.</footer></div>' + ('' if artefacto else '</body></html>'))
    return '\n'.join(H)

# ----------------------------------------------------------------------------- versiones: ejecutivo (1 página por vendor) y especificación por vendor
CSS_EXTRA = """
.onepage{page-break-before:always;display:grid;gap:10px}
.onepage .vhead{margin-top:.4rem;padding:6px 0 4px} .onepage .nota{margin:0;font-size:.9rem;padding:9px 14px}
.onepage .kpis{margin:0;gap:8px} .onepage .kpi{padding:9px 12px} .onepage .kpi .n{font-size:1.5rem}
.op-grid{display:grid;grid-template-columns:5fr 7fr;gap:14px;align-items:start} .op-grid>*{min-width:0}
@media(max-width:800px){.op-grid{grid-template-columns:1fr}}
.op-grid h3{margin:.2rem 0 .4rem;font-size:1rem}
.ficha.compact{grid-template-columns:1fr 1fr;gap:8px} .ficha.compact .f{padding:8px 10px} .ficha.compact .v{font-size:.82rem;margin:3px 0 4px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden} .ficha.compact .fuente{display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden}
.cards.compact{gap:6px} .cards.compact .card{padding:7px 10px} .cards.compact .card-t{font-size:.84rem} .cards.compact .small{display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden} .cards.compact .fuente{display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden}
.op-bottom{display:grid;grid-template-columns:7fr 5fr;gap:14px;align-items:start} .op-bottom>*{min-width:0} @media(max-width:800px){.op-bottom{grid-template-columns:1fr}}
.desp-row{display:grid;gap:6px} .desp-row .r{display:grid;grid-template-columns:150px 1fr;gap:8px;align-items:start;font-size:.8rem;border-bottom:1px solid var(--line);padding:4px 0} .desp-row .r:last-child{border:0} .desp-row .m{display:flex;gap:6px;align-items:center;font-family:var(--display);font-weight:700} .desp-row .fuente{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.alertas li{font-size:.84rem;margin:.15rem 0}
.cols2{columns:2;column-gap:28px} .cols2 li,.cols2 p{break-inside:avoid;page-break-inside:avoid} .cols2>ol,.cols2>ul{margin:0} @media(max-width:800px){.cols2{columns:1}}
ol.trans{padding-left:1.2rem;font-size:.9rem;columns:2;column-gap:28px;-webkit-columns:2} .cols2:has(ol.trans){columns:auto} ol.trans li{margin:0 0 .55rem} ol.trans .fuente{display:block;font-size:.74rem;color:var(--ink-3);margin-top:2px;line-height:1.35} ol.trans .fuente b{color:var(--ink-2);font-weight:600}
h2.salto{page-break-before:always;break-before:page}
@media print{ol.trans{font-size:.82rem} ol.trans .fuente{font-size:.68rem}}
.op-pie{font-size:.74rem;color:var(--ink-3);margin:0}
table.compacta{font-size:.78rem} table.compacta td{padding:6px 8px} table.compacta .crit{font-weight:600} table.compacta .ev{display:block;color:var(--ink-3);font-size:.74rem;margin-top:3px} table.compacta .ju{display:block;margin-top:3px}
@media print{.onepage{page-break-inside:avoid;gap:7px} .onepage .vhead{margin-top:0;border-top-width:5px} .onepage .nota{font-size:.82rem;padding:7px 12px} .onepage .kpis{gap:6px} .onepage .kpi{padding:7px 10px} .onepage .kpi .n{font-size:1.3rem} .onepage .kpi .l{font-size:.68rem}
 .op-grid{grid-template-columns:5fr 7fr;gap:10px} .op-grid h3,.op-bottom h3{font-size:.9rem;margin:.1rem 0 .3rem} .op-bottom{grid-template-columns:7fr 5fr;gap:10px}
 .ficha.compact{grid-template-columns:1fr 1fr;gap:6px} .ficha.compact .f{padding:6px 9px} .ficha.compact .v{font-size:.76rem;-webkit-line-clamp:2} .ficha.compact .fuente{font-size:.66rem}
 .cards.compact{gap:5px} .cards.compact .card{padding:6px 9px} .cards.compact .card-t{font-size:.78rem} .cards.compact .small,.cards.compact .fuente{font-size:.66rem}
 .desp-row .r{padding:3px 0;font-size:.74rem;grid-template-columns:130px 1fr} .desp-row .fuente{-webkit-line-clamp:1;font-size:.66rem} .desp-row .small{font-size:.74rem;display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden}
 .alertas li{font-size:.76rem;margin:.1rem 0} .op-pie{font-size:.66rem}
 .score-table td.small{font-size:.74rem} .score-table td.small>*{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}
"""
CSS_PORTRAIT = "@page{size:A4 portrait;margin:14mm 13mm 16mm} @media print{.vcards{grid-template-columns:repeat(2,1fr)} .grid2{grid-template-columns:1fr 1fr} .ficha{grid-template-columns:repeat(2,1fr)} .desp{grid-template-columns:1fr} .kpis{grid-template-columns:repeat(4,1fr)} html{font-size:10.5px}}"

def top_items(items, n=3):
    rank = {'ALTA': 0, 'MEDIA': 1, 'BAJA': 2, '': 3}
    return sorted(items, key=lambda it: (rank.get(it.get('confianza', ''), 3),))[:n] if items else []

def ficha_cards_compact(d, claves):
    f = d.get('ficha', {}); out = ['<div class="ficha compact">']
    for clave in claves:
        for k, val in f.items():
            if _norm(clave) in _norm(k):
                out.append(f'<div class="f"><div class="k"><span>{html.escape(k.capitalize())}</span><span>{html.escape(val["conf"])}</span></div><div class="v">{inline(val["que"])}</div><div class="fuente">{inline(val["fuente"])}</div></div>'); break
    out.append('</div>'); return '\n'.join(out)

def despliegue_filas(d):
    body = d.get('desp_modelos', '')
    if not body: return '<p class="small">Sin análisis de despliegue.</p>'
    hdr, rows = first_table(body)
    if not hdr: return md_to_html(body)
    def ix(*p):
        for q in p:
            for i, c in enumerate(hdr):
                if _norm(c).startswith(_norm(q)): return i
        return None
    iM, iO, iN, iF = ix('Modelo'), ix('Ofrecido'), ix('Nubes'), ix('Fuente')
    out = ['<div class="desp-row">']
    for r in rows:
        r = r + [''] * (len(hdr) - len(r)); g = lambda i: r[i] if i is not None else ''
        cls, corto = chip_modelo(g(iO))
        out.append(f'<div class="r"><div class="m"><span class="chip {cls}">{html.escape(corto)}</span>{inline(recorta(g(iM), 26))}</div><div><div class="small">{inline(recorta(g(iN), 90))}</div><div class="fuente">{inline(g(iF))}</div></div></div>')
    out.append('</div>'); return '\n'.join(out)

def lista_items(body, n):
    items = [re.sub(r'^\s*([-*•]|\d+[.)])\s+', '', l) for l in body.split('\n') if re.match(r'^\s*([-*•]|\d+[.)])\s+', l)]
    return items[:n]

def vendor_onepage(d):
    col = vcolor(d['_i']); cp, cc = conteo_conf(d.get('pros_items', [])), conteo_conf(d.get('contras_items', []))
    H = [f'<section class="vendor onepage" id="v-{d["vendor"]}" style="--vc:{col}"><div class="vhead"><h2>{html.escape(nombre(d["vendor"]))}</h2><span class="tag">{html.escape(recorta(ficha_get(d, "implementador"), 90))}</span></div>']
    if d.get('titular'): H.append(f'<div class="nota">{inline(d["titular"])}</div>')
    H.append('<div class="kpis">' + ''.join(f'<div class="kpi v"><div class="n">{d["resumen"].get(k):.0f}%</div><div class="l">{lab}</div></div>' if d['resumen'].get(k) is not None else '' for k, lab in (('EI', 'rúbrica · estrategia'), ('F', 'rúbrica · fabricante'), ('I', 'rúbrica · implementador')))
             + (f'<div class="kpi"><div class="n">{d["ceros"]}</div><div class="l">criterios en 0</div></div>' if d['tiene_impl'] else '')
             + f'<div class="kpi"><div class="n">{len(d.get("pros_items", []))}</div><div class="l">pros · {cp["ALTA"]} alta</div></div><div class="kpi"><div class="n">{len(d.get("contras_items", []))}</div><div class="l">contras · {cc["ALTA"]} alta</div></div></div>')
    H.append('<div class="op-grid"><div><h3>Lo que propone</h3>' + ficha_cards_compact(d, ['enfoque', 'duración', 'implementador', 'migraci', 'hypercare', 'modalidad']) + '</div>')
    H.append('<div><div class="grid2" style="gap:12px"><div><h3>Pros destacados</h3>' + tarjetas(top_items(d.get('pros_items', [])), 'pros compact') + '</div><div><h3>Contras destacados</h3>' + tarjetas(top_items(d.get('contras_items', [])), 'contras compact') + '</div></div></div></div>')
    alertas = lista_items(d.get('alertas7', ''), 3)
    H.append('<div class="op-bottom"><div><h3>Modelo de despliegue</h3>' + despliegue_filas(d) + '</div><div><h3>Señales de alerta</h3>' + ('<ul class="alertas">' + ''.join(f'<li>{inline(a)}</li>' for a in alertas) + '</ul>' if alertas else '<p class="small">Sin señales registradas.</p>') + '</div></div>')
    H.append(f'<p class="op-pie">Esta página muestra los 3 pros y 3 contras con mayor respaldo documental. El informe completo de {html.escape(nombre(d["vendor"]))}, con sus 10 pros, 10 contras, riesgos, preguntas al vendor y los 61 criterios de la rúbrica, es el documento «Especificación de implementación: {html.escape(nombre(d["vendor"]))}».</p></section>')
    return '\n'.join(H)

def tabla_criterios_compacta(items, con_impl=False):
    out = ['<div class="tbl-wrap"><table class="compacta"><thead><tr><th>Código</th>' + ('<th>Implementador</th>' if con_impl else '') + '<th>Criterio · evidencia · justificación</th><th>Peso</th><th>Puntaje</th><th>Respaldo</th></tr></thead><tbody>']
    for c in items:
        out.append('<tr><td>' + html.escape(c['codigo']) + '</td>' + (f'<td>{html.escape(recorta(c["implementador"], 28))}</td>' if con_impl else '') + f'<td><span class="crit">{inline(c["criterio"])}</span>' + (f'<span class="ev">{inline(c["evidencia"])}</span>' if c['evidencia'] else '') + (f'<span class="ju">{inline(c["justificacion"])}</span>' if c['justificacion'] else '') + f'</td><td>{html.escape(c["peso"])}</td><td>{score_html(c["puntaje"], recorta(c["descriptor"], 60))}</td><td>{badge_respaldo(c["respaldo"])}</td></tr>')
    out.append('</tbody></table></div>'); return '\n'.join(out)

def cabecera_doc(titulo, hoy, extra_css='', artefacto=False, sub=''):
    if artefacto: return f'<title>{titulo}</title>{FONTS}<style>{CSS}{CSS_EXTRA}{extra_css}</style><div class="wrap">'
    return f'<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{titulo}</title>{FONTS}<style>{CSS}{CSS_EXTRA}{extra_css}</style></head><body><div class="wrap"><div class="eyebrow"><span class="kicker">Selección de core bancario · Evaluación técnica</span><p class="meta">{sub}Generado el {hoy} · sin ranking ni recomendación</p></div>'

def pie_doc(hoy, artefacto=False):
    return f'<footer>Informe generado el {hoy}. Escala y pesos: rúbrica corporativa de implementación del Banco. Sin ranking ni recomendación.</footer></div>' + ('' if artefacto else '</body></html>')

def construir_ejecutivo(vendors_data, comparativo_md, hoy, artefacto=False):
    V = [d for d in vendors_data if d['ok']]; faltan = [d['vendor'] for d in vendors_data if not d['ok']]
    for i, d in enumerate(V): d['_i'] = i
    con_impl = [d for d in V if d['tiene_impl']]
    H = [cabecera_doc('Estrategias de implementación · Resumen ejecutivo', hoy, artefacto=artefacto, sub=f'{len(V)} vendors · ')]
    H.append('<header class="portada"><h1>Estrategias de implementación: resumen ejecutivo</h1>')
    H.append('<p class="lead">Qué propone cada vendor para implantar el core, con qué equipo y en cuánto tiempo, y qué tan respaldado está por sus documentos. Una página por vendor; el detalle completo está en la especificación de cada uno.' + (f' Sin verificación de implementación: {", ".join(faltan)}.' if faltan else '') + '</p>')
    H.append('<div class="vcards">' + ''.join(vendor_card(d) for d in V) + '</div>')
    H.append('<nav class="toc" aria-label="Contenido"><h4>Contenido</h4><ol><li><a href="#scorecard">Scorecard comparativo</a></li><li><a href="#graficos">Rúbrica y criterios</a></li><li><a href="#confianza">Pros y contras por confianza</a></li>' + ''.join(f'<li><a href="#v-{d["vendor"]}">{html.escape(nombre(d["vendor"]))}</a></li>' for d in V) + '<li><a href="#metodo">Metodología</a></li></ol></nav></header>')
    # scorecard + gráficos + confianza: reutiliza el cuerpo del documento completo hasta antes de las secciones por vendor
    completo = construir(vendors_data, comparativo_md, hoy, artefacto=True, ejecutivo=True)
    ini = completo.index('<h2 id="scorecard">'); fin = completo.index('<section class="vendor"')
    H.append(completo[ini:fin])
    for d in V: H.append(vendor_onepage(d))
    H.append('<h2 id="metodo">Metodología</h2><div class="grid2"><div class="panel"><p class="small">Cada vendor se analizó de forma aislada a partir de su propuesta técnica y anexos (metodología, cronograma, equipo, gobierno, migración, pruebas, transición, supuestos y responsabilidades del Banco). Cada pro y contra lleva fuente y nivel de confianza: ALTA si hay cifra, fecha o compromiso explícito; MEDIA si está descrito sin cifra; BAJA si es una afirmación genérica o solo declarada.</p></div><div class="panel"><p class="small">La rúbrica corporativa de implementación tiene 61 criterios (12 de estrategia, 24 de fabricante, 25 de implementador) con escala 0 a 5 y descriptor por nivel; el porcentaje por bloque es Σ(peso × puntaje) / Σ(peso × 5). Lo que solo declara el anexo de perfiles sin otro documento que lo respalde queda como «solo declarado» y no supera la mitad del máximo. Las sesiones de referenciación no se incluyen.</p></div></div>')
    H.append(pie_doc(hoy, artefacto)); return '\n'.join(H)

def construir_vendor(d, hoy, idx=0, artefacto=False):
    d['_i'] = idx; col = vcolor(idx); cp, cc = conteo_conf(d.get('pros_items', [])), conteo_conf(d.get('contras_items', []))
    H = [cabecera_doc(f'Implementación · {nombre(d["vendor"])}', hoy, extra_css=CSS_PORTRAIT, artefacto=artefacto, sub=f'Especificación de {html.escape(nombre(d["vendor"]))} · ')]
    H.append(f'<section style="--vc:{col}"><div class="vhead"><h1 style="font-size:2rem">{html.escape(nombre(d["vendor"]))}: propuesta de implementación</h1><span class="tag">{html.escape(recorta(ficha_get(d, "implementador"), 90))}</span></div>')
    if d.get('titular'): H.append(f'<div class="nota">{inline(d["titular"])}</div>')
    H.append('<div class="kpis">' + ''.join(f'<div class="kpi v"><div class="n">{d["resumen"].get(k):.0f}%</div><div class="l">{lab}</div></div>' if d['resumen'].get(k) is not None else '' for k, lab in (('EI', 'rúbrica · estrategia'), ('F', 'rúbrica · fabricante'), ('I', 'rúbrica · implementador')))
             + (f'<div class="kpi"><div class="n">{d["ceros"]}</div><div class="l">criterios en 0</div></div><div class="kpi"><div class="n">{d["declarados"]}</div><div class="l">solo declarados</div></div>' if d['tiene_impl'] else '')
             + f'<div class="kpi"><div class="n">{len(d.get("pros_items", []))}</div><div class="l">pros · {cp["ALTA"]} alta</div></div><div class="kpi"><div class="n">{len(d.get("contras_items", []))}</div><div class="l">contras · {cc["ALTA"]} alta</div></div></div>')
    H.append('<nav class="toc" aria-label="Contenido"><h4>Contenido</h4><ol><li><a href="#ficha">Ficha de la propuesta</a></li><li><a href="#rubrica">Rúbrica: estrategia por criterio</a></li><li><a href="#pros">Pros y contras</a></li><li><a href="#desp">Modelo de despliegue y nubes</a></li><li><a href="#riesgos">Riesgos, responsabilidades, alertas y preguntas</a></li>' + ('<li><a href="#anexo">Los 61 criterios de la rúbrica</a></li>' if d['tiene_impl'] else '') + '</ol></nav>')
    if d.get('ficha'): H.append('<h2 id="ficha">Ficha de la propuesta de implementación</h2>' + ficha_cards(d))
    if d['tiene_impl'] and d['crit']['EI']: H.append('<h2 id="rubrica">Rúbrica: estrategia de implementación por criterio</h2>' + svg_barras_h([(f'{c["codigo"]} {c["criterio"]}', c['puntaje']) for c in d['crit']['EI']], 'Puntaje EI', maxv=5, fmt=lambda x: f'{x:.0f} / 5', color=col))
    if d.get('pros_items') or d.get('contras_items'): H.append('<h2 id="pros">Pros y contras</h2>' + leyenda_conf() + '<div class="grid2"><div><h3>Pros</h3>' + tarjetas(d.get('pros_items', []), 'pros') + '</div><div><h3>Contras</h3>' + tarjetas(d.get('contras_items', []), 'contras') + '</div></div>')
    if d.get('desp_modelos'):
        H.append('<h2 id="desp">Modelo de despliegue y nubes</h2><p class="small">Cada tarjeta trae la fuente verificable (documento, página u hoja y fila, sección) y la confianza registradas en el análisis de despliegue.</p>' + despliegue_cards(d))
        if d.get('desp_nubes'): H.append('<h3>Nubes</h3>' + md_to_html(d['desp_nubes']))
        if d.get('desp_region', '').strip(): H.append('<h3>Región y residencia de datos</h3>' + md_to_html(d['desp_region']))
        if d.get('desp_no', '').strip(): H.append('<h3>No soporta o no ofrece</h3><div class="compact">' + md_to_html(d['desp_no']) + '</div>')
        if d.get('desp_contra', '').strip(): H.append('<h3>Contradicciones sobre despliegue</h3><div class="compact">' + md_to_html(d['desp_contra']) + '</div>')
    H.append('<h2 id="riesgos">Riesgos, responsabilidades, alertas y preguntas</h2><div class="grid2">')
    for titulo_s, clave in (('Riesgos de ejecución', 'riesgos'), ('Lo que el Banco asume', 'asume'), ('Señales de alerta', 'alertas7'), ('Contradicciones de la rúbrica', 'contradicciones'), ('Hallazgos de la rúbrica', 'hallazgos'), ('Preguntas pendientes al vendor', 'preguntas7')):
        if d.get(clave, '').strip(): H.append(f'<div class="panel"><h3 style="margin-top:0">{titulo_s}</h3><div class="compact">' + md_to_html(d[clave]) + '</div></div>')
    H.append('</div>')
    if d['tiene_impl']:
        H.append('<h2 id="anexo">Los 61 criterios de la rúbrica corporativa</h2>' + leyenda_escala())
        H.append('<h3>Estrategia de implementación (EI)</h3>' + tabla_criterios_compacta(d['crit']['EI']))
        H.append('<h3>Perfil del fabricante (F)</h3>' + tabla_criterios_compacta(d['crit']['F']))
        H.append('<h3>Perfil del implementador (I)</h3>' + tabla_criterios_compacta(d['crit']['I'], con_impl=True))
    H.append('</section>' + pie_doc(hoy, artefacto)); return '\n'.join(H)

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
    args = [a for a in sys.argv[1:]]; pdf = '--pdf' in args; artefacto = '--artefacto' in args
    salida = None
    if '--salida' in args: salida = Path(args[args.index('--salida') + 1]); args.remove('--salida'); args.remove(str(salida))
    modo_ejecutivo = '--ejecutivo' in args; modo_todo = '--todo' in args
    solo_vendor = args[args.index('--vendor') + 1] if '--vendor' in args else None
    if solo_vendor: args.remove('--vendor'); args.remove(solo_vendor)
    vendors = [a for a in args if not a.startswith('--')]
    if not vendors: vendors = sorted(p.name for p in VENDORS.iterdir() if p.is_dir() and ((p / 'verif' / 'IMPL.md').exists() or (p / 'informes' / '7_implementacion_pros_contras.md').exists()))
    if not vendors: sys.exit("Ningún vendor tiene verif/IMPL.md ni informes/7_implementacion_pros_contras.md. Ejecuta antes la verificación o el informe de implementación.")
    data = [cargar_vendor(v) for v in vendors]
    comp = VENDORS / 'COMPARATIVO_IMPLEMENTACION.md'; comp_md = comp.read_text(encoding='utf-8') if comp.exists() else ''
    hoy = datetime.date.today().strftime('%d-%m-%Y'); salidas = []
    ext = '.artefacto.html' if artefacto else '.html'
    if modo_ejecutivo or modo_todo:
        out = salida or (VENDORS / f'INFORME_IMPLEMENTACION_EJECUTIVO{ext}'); out.write_text(construir_ejecutivo(data, comp_md, hoy, artefacto=artefacto), encoding='utf-8'); salidas.append(out)
    if solo_vendor or modo_todo:
        for i, d in enumerate(data):
            if not d['ok'] or (solo_vendor and d['vendor'] != solo_vendor): continue
            out = VENDORS / f'INFORME_IMPLEMENTACION_{d["vendor"]}{ext}'; out.write_text(construir_vendor(d, hoy, idx=i, artefacto=artefacto), encoding='utf-8'); salidas.append(out)
    if not (modo_ejecutivo or modo_todo or solo_vendor):
        out = salida or (VENDORS / f'INFORME_IMPLEMENTACION{ext}'); out.write_text(construir(data, comp_md, hoy, artefacto=artefacto), encoding='utf-8'); salidas.append(out)
    for out in salidas:
        print(f'HTML: {out}')
        if pdf and not artefacto: a_pdf(out, out.with_suffix('.pdf'))
    print(f'({len(data)} vendors: {", ".join(d["vendor"] + ("" if d["ok"] else " [sin datos]") for d in data)})')

if __name__ == '__main__':
    main()
