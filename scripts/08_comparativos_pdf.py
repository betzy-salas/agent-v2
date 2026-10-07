#!/usr/bin/env python3
"""Informe HTML/PDF de los comparativos entre vendors: despliegue, implementación y matriz técnica (T1–T8).

Lee vendors/COMPARATIVO_DESPLIEGUE.md, vendors/COMPARATIVO_IMPLEMENTACION.md y vendors/COMPARATIVO.md (los que existan)
y genera vendors/INFORME_COMPARATIVOS.html (+ .pdf con --pdf). Reutiliza el sistema de diseño y los lectores de
07_informe_implementacion.py. No añade texto propio: solo reorganiza y da formato a lo ya escrito por los agentes.
Las fuentes de la comparación transversal se toman de los documentos citados por cada vendor (ficha, rúbrica, despliegue).

Uso:  python scripts/08_comparativos_pdf.py [--pdf] [--salida ruta.html]
"""
import datetime, html, importlib.util, re, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('informe07', AQUI / '07_informe_implementacion.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
VENDORS = m.VENDORS

CSS_COMP = """
.comp table{font-size:.74rem;border-collapse:separate;border-spacing:0;width:100%} .comp th{font-family:var(--display);font-size:.66rem;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-3);text-align:left;padding:6px 8px;border-bottom:2px solid var(--line);vertical-align:bottom}
.comp td{padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top;line-height:1.35} .comp td:first-child{font-family:var(--display);font-weight:800;white-space:nowrap;border-left:5px solid var(--vc,transparent);padding-left:8px}
.comp td.c,.comp th.c{text-align:center} .comp td.n{font-family:var(--mono);text-align:right;white-space:nowrap}
.cell{display:inline-block;min-width:26px;padding:2px 8px;line-height:1.25;border-radius:6px;font-family:var(--mono);font-size:.74rem;text-align:center;color:#fff;font-weight:600}
.cell.gris{background:var(--track);color:var(--ink-2)} .cell .d{display:block;font-family:var(--body);font-size:.64rem;font-weight:400;opacity:.92;white-space:normal}
.nube{display:inline-block;padding:3px 9px;border-radius:999px;font-size:.7rem;font-weight:600;border:1px solid var(--line)} .nube.of{background:#2a78d6;color:#fff;border-color:#2a78d6} .nube.ref{color:var(--ink-2);border-style:dashed} .nube.ne{color:var(--ink-3);background:var(--track);border-color:transparent}
.vgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px} .vgrid>*{min-width:0} .vbox{background:var(--panel);border:1px solid var(--line);border-top:5px solid var(--vc);border-radius:10px;padding:12px 14px;page-break-inside:avoid} .vbox h4{margin:0 0 6px;font-size:1rem} .vbox ul{margin:0;padding-left:1.1rem;font-size:.82rem} .vbox li{margin:.2rem 0} .vbox .k{font-family:var(--display);font-size:.66rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-3);margin:.6rem 0 .2rem;font-weight:700}
.vbox .fuente{display:block;color:var(--ink-3);font-size:.7rem} .comp td .nubes{margin-top:4px;font-size:.78rem;line-height:1.3} .comp td .fuente{display:block;color:var(--ink-3);font-size:.64rem;margin-top:3px;line-height:1.25}
.titular{font-size:1.05rem;line-height:1.45;background:var(--panel);border-left:5px solid var(--accent);padding:10px 14px;border-radius:0 8px 8px 0;margin:0 0 1rem}
.seccion{page-break-before:always} .sec-eye{font-family:var(--display);font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:var(--accent);font-weight:800;margin:0 0 .2rem}
.portada-cards{display:grid;grid-template-columns:repeat(3,1fr);gap:14px} .pc{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px;min-width:0} .pc .num{font-family:var(--display);font-size:2rem;font-weight:800;color:var(--accent);line-height:1} .pc h3{margin:.4rem 0 .3rem;font-size:1.05rem} .pc p{margin:0;font-size:.84rem;color:var(--ink-2)} .pc .meta{font-size:.72rem;color:var(--ink-3);margin-top:.5rem}
.compact ol,.compact ul{font-size:.86rem} .nota-fuente{font-size:.78rem;color:var(--ink-3);background:var(--panel);border:1px dashed var(--line);border-radius:8px;padding:8px 12px}
@media print{html{font-size:10px} .comp table{font-size:.7rem} .cell{padding:1px 7px} .cell .d{font-size:.58rem} .comp td,.comp th{padding:4px 6px} .vgrid{grid-template-columns:repeat(3,1fr)} .portada-cards{grid-template-columns:repeat(3,1fr)} .seccion{page-break-before:always} .vbox,.pc,tr{page-break-inside:avoid}}
"""

def esc(t): return html.escape(str(t or ''))
def limpia(t):
    """Nombres reales de vendor y descripciones legibles para las referencias a archivos de trabajo."""
    t = re.sub(r'vendors/([\w-]+)/informes/8_modelo_despliegue\.md', lambda x: f'análisis de despliegue de {m.nombre(x.group(1))}', t)
    t = m.fuentes_legibles(t); t = re.sub(r'`([^`]*)`', r'\1', t)
    return m.nombres_en_texto(t)
def tabla_de(body):
    hdr, rows = m.first_table(body); return hdr, [[limpia(c) for c in r] for r in rows]
def vidx(nombre_vendor):
    orden = ['FIS', 'Infosys', 'Pismo', 'Sunline', 'Temenos', 'Thought Machine']
    n = m.nombres_en_texto(nombre_vendor).strip()
    return orden.index(n) if n in orden else 7
def vc(nombre_vendor): return m.vcolor(vidx(nombre_vendor))
def chip(txt):
    cls, corto = m.chip_modelo(txt); t = (txt or '').strip()
    resto = t[len(corto):].strip(' ():;') if t.lower().startswith(corto.lower()) else ''
    return f'<span class="chip {cls}">{esc(corto)}</span>' + (f'<span class="small"> {esc(resto)}</span>' if resto else '')
def nube(txt):
    t = m._norm(txt)
    cls = 'of' if t.startswith('ofrecida') else 'ne' if t in ('n/e', 'ne', '—', '-', '') else 'ref'
    return f'<span class="nube {cls}">{esc(txt)}</span>'
def celda_puntaje(txt):
    mm = re.match(r'^\s*(\d)\s*[—-]?\s*(.*)$', txt or '')
    if not mm: return esc(txt)
    p = int(mm.group(1)); col = m.RAMP[min(p, 5)]
    return f'<span class="cell{" gris" if p == 0 else ""}" style="background:{col}">{p}<span class="d">{esc(mm.group(2))}</span></span>'
def tabla_html(hdr, rows, render=None, clases=None):
    out = ['<div class="comp"><table><thead><tr>' + ''.join(f'<th class="{(clases or {}).get(i, "")}">{esc(h)}</th>' for i, h in enumerate(hdr)) + '</tr></thead><tbody>']
    for r in rows:
        r = r + [''] * (len(hdr) - len(r)); color = vc(r[0]) if vidx(r[0]) < 7 else 'transparent'
        out.append(f'<tr style="--vc:{color}">' + ''.join(f'<td class="{(clases or {}).get(i, "")}">{(render(i, c) if render else m.inline(esc(c)))}</td>' for i, c in enumerate(r[:len(hdr)])) + '</tr>')
    return ''.join(out) + '</tbody></table></div>'

# ----------------------------------------------------------------------------- despliegue
MODELOS_ORDEN = [('saas', 'SaaS'), ('paas', 'PaaS'), ('privada', 'Nube privada / IaaS dedicada'), ('on-prem', 'On-premise'), ('hibrid', 'Híbrido')]
def tabla_modelo_nube(V):
    """Vendor × modelo: en qué nube o plataforma se ofrece cada modelo, con su condición y su fuente, copiado del análisis de despliegue del vendor."""
    filas = []
    for d in V:
        lines = [l for l in str(d.get('desp_modelos', '')).split('\n') if l.strip().startswith('|')]
        hdr, rows = m.parse_table(lines) if lines else ([], [])
        if not hdr: continue
        col = {m._norm(h)[:6]: i for i, h in enumerate(hdr)}
        i_of, i_nu, i_fu, i_co = col.get('ofreci'), col.get('nubes '), col.get('fuente'), col.get('condic')
        celdas = []
        for clave, _ in MODELOS_ORDEN:
            r = next((r for r in rows if clave in m._norm(r[0])), None)
            if not r: celdas.append('<span class="small">—</span>'); continue
            of = r[i_of] if i_of is not None else ''; nubes = r[i_nu] if i_nu is not None else ''; fu = r[i_fu] if i_fu is not None else ''
            cls, corto = m.chip_modelo(of)
            nub = '' if m._norm(nubes) in ('no aplica', 'no especificado', '', '—') else nubes
            partes = [f'<span class="chip {cls}">{esc(corto)}</span>']
            if nub: partes.append(f'<div class="nubes">{m.inline(esc(nub))}</div>')
            elif m._norm(nubes): partes.append(f'<div class="nubes small">{esc(nubes)}</div>')
            if fu: partes.append(f'<div class="fuente">{esc(m.primera_cita(fu))}</div>')
            celdas.append(''.join(partes))
        filas.append([m.nombre(d['vendor'])] + celdas)
    if not filas: return ''
    hdr = ['Vendor'] + [n for _, n in MODELOS_ORDEN]
    return tabla_html(hdr, filas, lambda i, c: f'<b>{esc(c)}</b>' if i == 0 else c)

def seccion_despliegue(md, V):
    secs = m.sections(md); H = ['<section class="seccion"><p class="sec-eye">Comparativo 1 de 3</p><h2>Modelos de despliegue y nubes</h2>']
    H.append('<p class="small">Qué modelo ofrece cada vendor (SaaS, PaaS, nube privada, on-premise, híbrido), en qué nubes y cuáles quedan excluidas o sin especificar. Cada «Sí», «No» o «Condicionado» tiene su cita documental en el análisis de despliegue del vendor, incluido en su especificación.</p>')
    hdr, rows = tabla_de(m.find_section(secs, 'por proveedor'))
    if hdr:
        def r(i, c): return chip(c) if 1 <= i <= 5 else (f'<b>{esc(m.nombres_en_texto(c))}</b>' if i == 0 else m.inline(esc(c)))
        H.append('<h3>Modelos por vendor</h3>' + tabla_html(hdr, rows, r))
    tmn = tabla_modelo_nube(V)
    if tmn: H.append('<h3 style="page-break-before:always">En qué nube o plataforma se ofrece cada modelo</h3><p class="small">Complemento de la tabla anterior: para cada vendor y cada modelo, las nubes o plataformas (AWS, Azure, GCP, Huawei, OCI, OpenShift, nube privada del vendor…) que sus documentos asocian a ese modelo, con la condición que declaran. Celda vacía de nubes = el modelo no aplica o el vendor no lo especifica. Cada celda indica el documento de origen; la cita completa está en el análisis de despliegue del vendor.</p>' + tmn)
    hdr, rows = tabla_de(m.find_section(secs, 'vendor x nube', 'vendor × nube', 'por nube'))
    if hdr:
        def r(i, c): return f'<b>{esc(m.nombres_en_texto(c))}</b>' if i == 0 else nube(c)
        H.append('<h3 style="page-break-before:always">Nubes: ofrecidas al Banco o solo mencionadas</h3><p class="small"><span class="nube of">Ofrecida para el Banco</span> <span class="nube ref">Solo referencia ajena</span> <span class="nube ne">N/E</span> = no especificado en los documentos del vendor.</p>' + tabla_html(hdr, rows, r))
    contr = m.find_section(secs, 'sin definir', 'contradiccion')
    if contr.strip():
        items = [re.sub(r'^\s*[-*]\s+', '', l) for l in contr.split('\n') if re.match(r'^\s*[-*]\s+', l)]
        cards = []
        for it in items:
            v, _, txt = it.partition(':')
            cards.append(f'<div class="vbox" style="--vc:{vc(v)}"><h4>{esc(m.nombres_en_texto(v.strip()))}</h4><p class="small" style="margin:0">{m.inline(esc(limpia(txt.strip())))}</p></div>')
        H.append('<h3>Despliegue sin definir o con contradicciones</h3><div class="vgrid">' + ''.join(cards) + '</div>')
    resto = [(t, b) for lvl, t, b in secs if t and not any(k in m._norm(t) for k in ('por proveedor', 'vendor x nube', 'sin definir', 'comparativo de despliegue'))]
    for t, b in resto:
        if b.strip(): H.append(f'<h3>{esc(t)}</h3><div class="compact">{m.md_to_html(limpia(b))}</div>')
    return ''.join(H) + '</section>'

# ----------------------------------------------------------------------------- implementación
def seccion_implementacion(md, V):
    secs = m.sections(md); H = ['<section class="seccion"><p class="sec-eye">Comparativo 2 de 3</p><h2>Propuestas de implementación</h2>']
    titular = next((b for lvl, t, b in secs if lvl == 0 and b.strip()), '').strip().split('\n')[0]
    if titular: H.append(f'<p class="titular">{m.inline(esc(limpia(titular)))}</p>')
    cab = m.find_section(secs, 'cabecera')
    fecha = re.search(r'Fecha:\s*([\d-]+)', cab); incompletos = re.search(r'incompletos:\s*(.+)', cab)
    H.append('<p class="small">' + (f'Comparativo escrito el {fecha.group(1)}. ' if fecha else '') + (f'Vendors incompletos: {esc(incompletos.group(1).strip())}. ' if incompletos else '') + 'Las cifras son las de la rúbrica corporativa verificada de cada vendor (0 a 5 por criterio, porcentaje ponderado por bloque).</p>')
    hdr, rows = tabla_de(m.find_section(secs, 'resumen por vendor'))
    if hdr:
        pct_cols = {i for i, h in enumerate(hdr) if '%' in h}
        def r(i, c):
            if i == 0: return f'<b>{esc(m.nombres_en_texto(c))}</b>'
            if i in pct_cols:
                mm = re.match(r'^\s*(\d+(?:\.\d+)?)', c)
                if mm and not re.search(r'\d.*\s(?:y|/)\s.*\d', c):
                    v = float(mm.group(1)); return f'<div class="inl"><span class="num">{v:.0f}%</span><span class="bar"><i style="width:{v:.0f}%"></i></span></div>'
            return m.inline(esc(c))
        H.append('<h3>Resumen por vendor</h3>' + tabla_html(hdr, rows, r, {i: 'pct' for i in pct_cols}))
    hdr, rows = tabla_de(m.find_section(secs, 'criterio a criterio'))
    if hdr:
        hdr = [m.nombres_en_texto(h) for h in hdr]
        def r(i, c): return esc(c) if i == 0 else celda_puntaje(c)
        H.append('<h3 style="page-break-before:always">Estrategia de implementación, criterio a criterio (EI-01 a EI-12)</h3><p class="small">Nota 0 a 5 de cada vendor con el descriptor abreviado de la rúbrica. Más oscuro, más alto; gris, no presentado.</p>' + tabla_html(hdr, rows, r, {i: 'c' for i in range(1, len(hdr))}))
    dif = m.find_section(secs, 'mayor diferencia')
    if dif.strip(): H.append('<h3>Criterios donde más difieren</h3><div class="compact">' + m.md_to_html(limpia(dif)) + '</div>')
    # una tarjeta por vendor
    conocidos = {'cabecera', 'resumen por vendor', 'criterio a criterio', 'mayor diferencia', 'transversal', 'preguntas'}
    vend_secs = [(t, b) for lvl, t, b in secs if lvl == 2 and t and not any(k in m._norm(t) for k in conocidos)]
    if vend_secs:
        H.append('<h3 style="page-break-before:always">Fortalezas y debilidades por vendor</h3><p class="nota-fuente">Cada punto lleva el código del criterio o ítem y la fuente tal como la cita el archivo del vendor. Donde el comparativo actual escribió el nombre de un informe de trabajo en lugar del documento, aparece como «informe de implementación de …»; esas fuentes se sustituyen por la cita documental al relanzar el comparador de implementación.</p><div class="vgrid">')
        for t, b in vend_secs:
            nombre_v = m.nombres_en_texto(t.strip()); partes = re.split(r'\n(?=(?:Fortalezas|Debilidades|Lo que deja al Banco|Señales de alerta|Veredicto)[^\n]*\n)', '\n' + b.strip())
            card = [f'<div class="vbox" style="--vc:{vc(t)}"><h4>{esc(nombre_v)}</h4>']
            for parte in partes:
                parte = parte.strip()
                if not parte: continue
                titulo, _, cuerpo = parte.partition('\n')
                items = [re.sub(r'^\s*[-*]\s+', '', l) for l in cuerpo.split('\n') if re.match(r'^\s*[-*]\s+', l)]
                lis = []
                for it in items:
                    it = limpia(it); mm = re.search(r';\s*[Ff]uente:\s*', it)
                    txt, fu = (it[:mm.start()], it[mm.end():]) if mm else (it, '')
                    lis.append(f'<li>{m.inline(esc(txt.strip().rstrip(".")))}' + (f'<span class="fuente">{esc(fu.strip().rstrip("."))}</span>' if fu else '') + '</li>')
                card.append(f'<div class="k">{esc(titulo.strip())}</div><ul>{"".join(lis)}</ul>' if lis else f'<div class="k">{esc(titulo.strip())}</div><p class="small" style="margin:0">{m.inline(esc(limpia(cuerpo.strip())))}</p>')
            H.append(''.join(card) + '</div>')
        H.append('</div>')
    trans = m.find_section(secs, 'transversal')
    if trans.strip(): H.append('<h3 style="page-break-before:always">Lo que cambia entre vendors</h3><p class="small">Debajo de cada punto, el documento de cada vendor donde está el dato (nombre oficial y página u hoja), tomado de su informe de implementación.</p><div class="compact cols2">' + m.transversal_html(trans, V) + '</div>')
    preg = [(t, b) for lvl, t, b in secs if lvl == 3 and t and b.strip()]
    preg_body = m.find_section(secs, 'preguntas')
    if preg or preg_body.strip():
        H.append('<h3>Preguntas pendientes por vendor</h3><div class="vgrid">')
        i0 = next((i for i, (lvl, t, b) in enumerate(secs) if 'preguntas' in m._norm(t)), None)
        for lvl, t, b in (secs[i0 + 1:] if i0 is not None else []):
            if lvl <= 2: break
            H.append(f'<div class="vbox" style="--vc:{vc(t)}"><h4>{esc(m.nombres_en_texto(t))}</h4>{m.md_to_html(limpia(b))}</div>')
        H.append('</div>')
    return ''.join(H) + '</section>'

# ----------------------------------------------------------------------------- matriz técnica
def seccion_matriz(md):
    secs = m.sections(md); H = ['<section class="seccion"><p class="sec-eye">Comparativo 3 de 3</p><h2>Matriz técnica T1–T8: puntaje del Banco y puntaje verificado</h2>']
    H.append('<p class="small">Puntaje 0–100 por hoja (media de calificaciones 0–4 sobre 4) y total ponderado. «Verificado» es el que resulta de contrastar cada ítem con los documentos del vendor; entre paréntesis, el del Banco. Niveles: Cumple plenamente ≥ 85 · Cumple 70–84 · Parcial 50–69 · No cumple &lt; 50.</p>')
    cuerpo = '\n'.join(b for lvl, t, b in secs)
    bloques = re.split(r'\n\s*\n', cuerpo.strip())
    tablas = [b for b in bloques if b.strip().startswith('|')]
    vendors_en_tabla = []
    if tablas:
        hdr, rows = m.parse_table(tablas[0].split('\n')); vendors_en_tabla = [m.nombres_en_texto(h) for h in hdr[1:]]
        def r(i, c):
            if i == 0: return esc(m.nombres_en_texto(c)).replace('**', '')
            mm = re.match(r'^\s*([\d.]+)\s*\(([\d.]+)\)', c)
            if mm: return f'<span class="num"><b>{mm.group(1)}</b> <span class="small">({mm.group(2)})</span></span>'
            return esc(c)
        H.append('<div class="grid2"><div><h3>Por hoja</h3>' + tabla_html([m.nombres_en_texto(h) for h in hdr], [[c.replace('**', '') for c in row] for row in rows], r, {i: 'c' for i in range(1, len(hdr))}) + '</div>')
        if len(tablas) > 1:
            hdr2, rows2 = m.parse_table(tablas[1].split('\n'))
            H.append('<div><h3>Total por vendor</h3>' + tabla_html(hdr2, [[m.nombres_en_texto(c) for c in row] for row in rows2]) + '</div>')
        H.append('</div>')
    faltan = [v for v in ['FIS', 'Infosys', 'Pismo', 'Sunline', 'Temenos', 'Thought Machine'] if v not in vendors_en_tabla]
    if faltan: H.append(f'<p class="nota-fuente">Este comparativo solo incluye los vendors con las ocho verificaciones T1–T8 y el consolidado en este proyecto: {esc(", ".join(vendors_en_tabla))}. Faltan {esc(", ".join(faltan))}: sus verificaciones se están haciendo en otro equipo; al traer sus carpetas verif/ y correr 03_consolidar y 05_comparar, entran en esta tabla.</p>')
    return ''.join(H) + '</section>'

# ----------------------------------------------------------------------------- documento
def construir(hoy):
    f_desp, f_impl, f_mat = VENDORS / 'COMPARATIVO_DESPLIEGUE.md', VENDORS / 'COMPARATIVO_IMPLEMENTACION.md', VENDORS / 'COMPARATIVO.md'
    disponibles = [(f, n, d) for f, n, d in ((f_desp, 'Despliegue', 'Modelos SaaS/PaaS/privada/on-premise/híbrido, nubes ofrecidas y excluidas, quién opera y región, con contradicciones por vendor.'),
                                              (f_impl, 'Implementación', 'Rúbrica corporativa verificada (EI, F, I), criterio a criterio, fortalezas y debilidades, diferencias transversales y preguntas.'),
                                              (f_mat, 'Matriz técnica T1–T8', 'Puntaje del Banco frente al puntaje verificado por hoja y total ponderado, con nivel de cumplimiento.')) if f.exists()]
    if not disponibles: sys.exit('No hay ningún COMPARATIVO*.md en vendors/.')
    vendors = sorted(p.name for p in VENDORS.iterdir() if p.is_dir() and ((p / 'verif' / 'IMPL.md').exists() or (p / 'informes' / '7_implementacion_pros_contras.md').exists()))
    V = [d for d in (m.cargar_vendor(v) for v in vendors) if d['ok']]
    for i, d in enumerate(V): d['_i'] = i
    H = [m.cabecera_doc('Comparativos entre vendors', hoy, extra_css=CSS_COMP, sub='Comparativos · ')]
    H.append('<header class="portada"><div><h1>Comparativos entre vendors</h1><p class="lead">Tres lecturas transversales de las propuestas de core bancario: cómo se despliega cada solución, cómo propone implantarse y qué puntaje técnico verificado obtiene. Cada dato proviene del expediente de un vendor y conserva su cita documental; el documento expone diferencias, no ordena ni recomienda.</p></div><div class="portada-cards">')
    for i, (f, n, d) in enumerate(disponibles, 1):
        fecha = datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime('%d-%m-%Y')
        H.append(f'<div class="pc"><div class="num">{i}</div><h3>{esc(n)}</h3><p>{esc(d)}</p><p class="meta">Comparativo actualizado el {fecha}</p></div>')
    H.append('</div>' + m.legend_vendors(V) + '</header>')
    if f_desp.exists(): H.append(seccion_despliegue(m.leer_md(f_desp), V))
    if f_impl.exists(): H.append(seccion_implementacion(m.leer_md(f_impl), V))
    if f_mat.exists(): H.append(seccion_matriz(m.leer_md(f_mat)))
    H.append('<section class="seccion"><h2>Metodología</h2><p>Cada vendor se analizó de forma aislada a partir de sus propios documentos; los comparativos solo agregan lo ya escrito y citado por vendor, uno por uno, sin usar lo de un vendor para completar a otro. Las fuentes son los documentos del vendor (nombre oficial y página del PDF, u hoja y fila del Excel). La respuesta del proveedor sin respaldo documental cuenta como «solo declarado». No hay ranking ni recomendación: si el comité la pide, se elabora aparte.</p></section>')
    H.append(m.pie_doc(hoy))
    return '\n'.join(H)

def main():
    args = sys.argv[1:]; pdf = '--pdf' in args
    salida = Path(args[args.index('--salida') + 1]) if '--salida' in args else VENDORS / 'INFORME_COMPARATIVOS.html'
    hoy = datetime.date.today().strftime('%d-%m-%Y')
    salida.write_text(construir(hoy), encoding='utf-8'); print(f'HTML: {salida}')
    if pdf: m.a_pdf(salida, salida.with_suffix('.pdf'))

if __name__ == '__main__':
    main()
