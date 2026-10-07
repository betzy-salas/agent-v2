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
.vbox .fuente{display:block;color:var(--ink-3);font-size:.7rem} .dot{display:inline-block;width:14px;height:14px;border-radius:50%;vertical-align:middle;border:2px solid transparent} .dot.of{background:#2a78d6;border-color:#2a78d6} .dot.cond{background:transparent;border-color:#2a78d6} .dot.no{background:transparent;border-color:#8a8f98;border-style:dashed} .dot.vacio{background:var(--track);width:8px;height:8px;border:0} .grid-nubes .comp table{font-size:.72rem} .grid-nubes .comp th{font-size:.6rem;padding:4px 3px;text-align:center} .grid-nubes .comp td{padding:5px 3px} .grid-nubes .comp td:first-child{font-weight:600;font-family:var(--body);white-space:normal;border-left:0;padding-left:0;font-size:.74rem} .chip.mini{font-size:.6rem;padding:1px 6px;margin-left:5px} .comp td .nubes{margin-top:4px;font-size:.78rem;line-height:1.3} .comp td .fuente{display:block;color:var(--ink-3);font-size:.64rem;margin-top:3px;line-height:1.25}
.titular{font-size:1.05rem;line-height:1.45;background:var(--panel);border-left:5px solid var(--accent);padding:10px 14px;border-radius:0 8px 8px 0;margin:0 0 1rem}
.seccion{page-break-before:always} .sec-eye{font-family:var(--display);font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:var(--accent);font-weight:800;margin:0 0 .2rem}
.portada-cards{display:grid;grid-template-columns:repeat(3,1fr);gap:14px} .pc{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px;min-width:0} .pc .num{font-family:var(--display);font-size:2rem;font-weight:800;color:var(--accent);line-height:1} .pc h3{margin:.4rem 0 .3rem;font-size:1.05rem} .pc p{margin:0;font-size:.84rem;color:var(--ink-2)} .pc .meta{font-size:.72rem;color:var(--ink-3);margin-top:.5rem}
.compact ol,.compact ul{font-size:.86rem} .nota-fuente{font-size:.78rem;color:var(--ink-3);background:var(--panel);border:1px dashed var(--line);border-radius:8px;padding:8px 12px}

.ancha table{table-layout:auto;border-spacing:0 5px;width:100%} .ancha th,.ancha td{border-bottom:0}
.ancha th.grupo{text-align:center;padding:8px 4px 6px;border-bottom:0;border-radius:8px 8px 0 0;vertical-align:bottom} .ancha th.grupo .gn{display:block;font-family:var(--display);font-size:.82rem;letter-spacing:.04em;color:var(--ink)} .ancha th.grupo .gc{display:block;font-size:.6rem;letter-spacing:0;text-transform:none;color:var(--ink-3);font-weight:500;margin-top:2px}
.ancha th.sub{font-size:.56rem;letter-spacing:0;text-transform:none;padding:3px 1px 6px;text-align:center;color:var(--ink-3);border-bottom:2px solid var(--line)}
.ancha .g1{background:color-mix(in srgb,var(--accent) 6%,var(--panel))} .ancha .g0{background:color-mix(in srgb,var(--ink) 3%,var(--panel))}
.ancha th.ini,.ancha td.ini{border-left:0} .ancha td.ini{border-radius:8px 0 0 8px} .ancha td.fin{border-radius:0 8px 8px 0}
.ancha td{padding:6px 2px;border-bottom:0} .ancha td.vcol{white-space:nowrap;padding:7px 12px 7px 10px;border:1px solid var(--line);border-left:6px solid var(--vc,var(--line));border-radius:8px;background:var(--panel)} .ancha th.vcol,.ancha th.scol{white-space:nowrap;vertical-align:bottom;padding:0 8px 6px;border-bottom:2px solid var(--line)} .ancha td.scol{padding:7px 8px;border-bottom:1px solid var(--line);white-space:nowrap}
.ancha .vname{font-family:var(--display);font-weight:800;font-size:.9rem}
.ancha .tile,.leyenda-tiles .tile{display:block;height:24px;line-height:22px;border-radius:6px;text-align:center;font-family:var(--display);font-size:.54rem;font-weight:700;letter-spacing:.02em;border:1px solid transparent;box-sizing:border-box}
.ancha .tile.of,.leyenda-tiles .tile.of{background:var(--mc);color:var(--mt);border-color:var(--mc)} .ancha .tile.cond,.leyenda-tiles .tile.cond{background:transparent;color:var(--mc);border:2px solid var(--mc);line-height:20px} .ancha .tile.no,.leyenda-tiles .tile.no{background:transparent;color:var(--ink-3);border:2px dashed #8a8f98;line-height:20px} .ancha .tile.vacio,.leyenda-tiles .tile.vacio{background:var(--track);height:6px;margin:9px 6px;border-radius:3px}
.ancha.invertida td{padding:1px 3px;border-bottom:0} .ancha.invertida td.vcol,.ancha.invertida th.vcol{width:1%;white-space:nowrap;vertical-align:middle;border-left:3px solid var(--line);padding:1px 14px 1px 10px} .ancha.invertida .mcol{white-space:nowrap;padding:1px 10px 1px 8px;font-size:.72rem;width:1%} .ancha.invertida .mlab{font-weight:700;color:var(--mc)} .ancha.invertida th.grupo{font-family:var(--display);font-size:.76rem;letter-spacing:.04em;color:var(--ink);padding:6px 4px;border-bottom:2px solid var(--line);border-radius:0;background:var(--panel)} .ancha.invertida th.mcol{text-align:left;padding:0 8px 6px;border-bottom:2px solid var(--line)} .ancha.invertida tbody.grupo-vendor{page-break-inside:avoid;break-inside:avoid} .ancha.invertida tr.fin td{border-bottom:2px solid var(--line)} .ancha.invertida .tile{height:16px;line-height:14px;font-size:.56rem;max-width:70px;margin:1px auto;border-radius:5px} .ancha.invertida .tile.cond,.ancha.invertida .tile.no{line-height:12px;overflow:hidden} .ancha.invertida .tile.vacio{height:4px;margin:7px auto;width:26px} @media print{.ancha.invertida .tile{height:15px;line-height:13px} .ancha.invertida .tile.cond,.ancha.invertida .tile.no{line-height:11px} .ancha.invertida .tile.vacio{height:4px;margin:6px auto}}
.hoja-nubes{page-break-before:always;display:flex;flex-direction:column} .hoja-nubes .comp{flex:0 0 auto} .leyenda-tiles{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:auto;padding-top:22px} .lt-box{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:9px 14px 10px} .lt-grupo{display:flex;flex-wrap:wrap;gap:5px 14px;align-items:center;margin-top:5px} .lt-k{display:block;font-family:var(--display);font-size:.58rem;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-3);font-weight:700} .lt-item{display:inline-flex;align-items:center;gap:5px;font-size:.7rem;color:var(--ink-2)} .lt-item .tile{width:32px;height:16px;line-height:14px;font-size:.5rem;display:inline-block;border-radius:4px} .lt-item .tile.cond,.lt-item .tile.no{line-height:12px} .lt-item .tile.vacio{width:22px;height:4px;margin:0} @media print{.hoja-nubes{min-height:181mm}}
@media print{.ancha .tile{height:22px;line-height:20px} .ancha .tile.cond,.ancha .tile.no{line-height:18px} .ancha .tile.vacio{height:5px;margin:8px 6px}}
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
INCLUIR_VISTA_INVERTIDA = False   # variante descartada por la usuaria (2026-10-07); se conserva el código por si se retoma
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

PLATAFORMAS = [('AWS', (r'\baws\b', r'amazon')), ('Azure', (r'azure',)), ('GCP', (r'\bgcp\b', r'google')), ('OCI', (r'\boci\b', r'oracle')),
               ('Huawei', (r'huawei',)), ('OpenShift', (r'openshift',)), ('Nube privada', (r'private cloud', r'nube privada', r'nubes privadas', r'privada'))]
def marcas_nubes(ofrecido, nubes):
    """Devuelve {plataforma: estado} a partir del texto «Nubes para ese modelo» y del estado del modelo. Estados: of (ofrecida),
    cond (condicionada o solo compatibilidad declarada), no (mencionada pero el modelo no se ofrece)."""
    t = m._norm(nubes); o = m._norm(ofrecido)
    if not t or t.startswith('no aplica') or t.startswith('no especificado'): return {}
    estado_modelo = 'of' if o.startswith('si') else 'no' if o == 'no' or o.startswith('no (') else 'cond'
    out = {}
    clausulas = [c.strip() for c in re.split(r'[;.]', t) if c.strip()]   # cada cláusula se juzga por separado: «Azure (oferta inicial); tambien cloud-agnostic»
    for nombre_p, pats in PLATAFORMAS:
        for pat in pats:
            cl = next((c for c in clausulas if re.search(pat, c)), None)
            if cl:
                debil = re.search(r'compatib|tambien|también|segun|según|menciona|declara|solo para|referencia|opcional', cl)
                out[nombre_p] = 'no' if estado_modelo == 'no' else 'cond' if (estado_modelo == 'cond' or debil) else 'of'
                break
    return out

LEYENDA_DOTS = '<p class="small"><span class="dot of"></span> ofrecida para ese modelo · <span class="dot cond"></span> condicionada o solo compatibilidad declarada · <span class="dot no"></span> mencionada, pero el modelo no se ofrece · <span class="dot vacio"></span> no la asocia a ese modelo. «Nube privada» incluye la nube privada del vendor (p. ej. FIS Private Cloud) o del cliente.</p>'

def grids_nubes(V):
    """Una cuadrícula por vendor: filas = modelos, columnas = plataformas; la celda marca si la plataforma se ofrece para ese modelo."""
    cards = []
    for d in V:
        lines = [l for l in str(d.get('desp_modelos', '')).split('\n') if l.strip().startswith('|')]
        hdr, rows = m.parse_table(lines) if lines else ([], [])
        if not hdr: continue
        col = {m._norm(h)[:6]: i for i, h in enumerate(hdr)}; i_of, i_nu = col.get('ofreci'), col.get('nubes ')
        filas = []
        for clave, nombre_m in MODELOS_ORDEN:
            r = next((r for r in rows if clave in m._norm(r[0])), None)
            marcas = marcas_nubes(r[i_of], r[i_nu]) if r and i_of is not None and i_nu is not None else {}
            cls, corto = m.chip_modelo(r[i_of]) if r else ('', '—')
            celdas = ''.join(f'<td class="c"><span class="dot {marcas[pn]}" title="{pn}"></span></td>' if pn in marcas else '<td class="c"><span class="dot vacio"></span></td>' for pn, _ in PLATAFORMAS)
            filas.append(f'<tr><td>{esc(nombre_m.split(" / ")[0])}<span class="chip {cls} mini">{esc(corto)}</span></td>{celdas}</tr>')
        cards.append(f'<div class="vbox grid-nubes" style="--vc:{m.vcolor(d["_i"])}"><h4>{esc(m.nombre(d["vendor"]))}</h4><div class="comp"><table><thead><tr><th>Modelo</th>' + ''.join(f'<th class="c">{esc(pn)}</th>' for pn, _ in PLATAFORMAS) + '</tr></thead><tbody>' + ''.join(filas) + '</tbody></table></div></div>')
    if not cards: return ''
    leyenda = '<p class="small"><span class="dot of"></span> ofrecida para ese modelo · <span class="dot cond"></span> condicionada o solo compatibilidad declarada · <span class="dot no"></span> mencionada, pero el modelo no se ofrece · <span class="dot vacio"></span> no la asocia a ese modelo. «Nube privada» incluye la nube privada del vendor (p. ej. FIS Private Cloud) o del cliente.</p>'
    return leyenda + '<div class="vgrid">' + ''.join(cards) + '</div>'

ABREV_MODELO = {'saas': 'SaaS', 'paas': 'PaaS', 'privada': 'Priv', 'on-prem': 'OnP', 'hibrid': 'Híb'}
COLOR_MODELO = {'saas': ('#2a78d6', '#fff'), 'paas': ('#eb6834', '#fff'), 'privada': ('#1baf7a', '#fff'), 'on-prem': ('#eda100', '#1b1b1b'), 'hibrid': ('#4a3aa7', '#fff')}   # paleta categórica validada (dataviz)
NOMBRE_MODELO_LARGO = {'saas': 'SaaS', 'paas': 'PaaS', 'privada': 'Nube privada / IaaS dedicada', 'on-prem': 'On-premise', 'hibrid': 'Híbrido'}
def tile(clave, est):
    bg, fg = COLOR_MODELO[clave]
    return f'<span class="tile {est or "vacio"}" style="--mc:{bg};--mt:{fg}">{ABREV_MODELO[clave] if est else ""}</span>'

def tabla_nubes_ancha(V):
    """Vista alternativa en una sola tabla: filas = vendors; columnas = nubes, y dentro de cada nube una ficha por modelo.
    El color de la ficha identifica el modelo (leyenda al pie); su relleno, si la nube se ofrece, es condicionada o solo se menciona."""
    datos = []
    for d in V:
        lines = [l for l in str(d.get('desp_modelos', '')).split('\n') if l.strip().startswith('|')]
        hdr, rows = m.parse_table(lines) if lines else ([], [])
        if not hdr: continue
        col = {m._norm(h)[:6]: i for i, h in enumerate(hdr)}; i_of, i_nu = col.get('ofreci'), col.get('nubes ')
        por_modelo = {}
        for clave, _ in MODELOS_ORDEN:
            r = next((r for r in rows if clave in m._norm(r[0])), None)
            por_modelo[clave] = marcas_nubes(r[i_of], r[i_nu]) if r and i_of is not None and i_nu is not None else {}
        datos.append((d, por_modelo))
    if not datos: return ''
    def n_vendors(pn): return sum(1 for _, pm in datos if any(pm[c].get(pn) == 'of' for c, _ in MODELOS_ORDEN))
    th1 = '<tr><th class="vcol">Vendor</th>' + ''.join(f'<th colspan="{len(MODELOS_ORDEN)}" class="grupo g{i % 2}"><span class="gn">{esc(pn)}</span><span class="gc">{n_vendors(pn)} de {len(datos)} la ofrecen</span></th>' for i, (pn, _) in enumerate(PLATAFORMAS)) + '</tr>'
    filas = []
    for d, por_modelo in datos:
        celdas = ''
        for i, (pn, _) in enumerate(PLATAFORMAS):
            for k, (clave, _) in enumerate(MODELOS_ORDEN):
                celdas += f'<td class="g{i % 2}{" ini" if k == 0 else ""}{" fin" if k == len(MODELOS_ORDEN) - 1 else ""}">{tile(clave, por_modelo.get(clave, {}).get(pn))}</td>'
        filas.append(f'<tr style="--vc:{m.vcolor(d["_i"])}"><td class="vcol"><span class="vname">{esc(m.nombre(d["vendor"]))}</span></td>{celdas}</tr>')
    leyenda = ('<div class="leyenda-tiles"><div class="lt-box"><span class="lt-k">Modelo (color de la ficha)</span><div class="lt-grupo">' + ''.join(f'<span class="lt-item">{tile(clave, "of")}<span>{esc(NOMBRE_MODELO_LARGO[clave])}</span></span>' for clave, _ in MODELOS_ORDEN) + '</div></div>'
               '<div class="lt-box"><span class="lt-k">Estado (relleno de la ficha)</span><div class="lt-grupo">'
               f'<span class="lt-item">{tile("saas", "of")}<span>ofrecida para ese modelo</span></span>'
               f'<span class="lt-item">{tile("saas", "cond")}<span>condicionada o solo compatibilidad declarada</span></span>'
               f'<span class="lt-item">{tile("saas", "no")}<span>mencionada, pero el modelo no se ofrece</span></span>'
               f'<span class="lt-item">{tile("saas", None)}<span>no la asocia a ese modelo</span></span></div></div></div>')
    return '<div class="comp ancha"><table><thead>' + th1 + '</thead><tbody>' + ''.join(filas) + '</tbody></table></div>' + leyenda

def tabla_nubes_invertida(V):
    """Copia invertida de la vista alternativa: filas = vendor × modelo (SaaS, PaaS… dentro de cada vendor); columnas = nubes.
    La ficha toma el color del modelo de su fila; el texto dice el estado: Sí (ofrecida), Cond. (condicionada), Menc. (mencionada sin ofrecer)."""
    datos = []
    for d in V:
        lines = [l for l in str(d.get('desp_modelos', '')).split('\n') if l.strip().startswith('|')]
        hdr, rows = m.parse_table(lines) if lines else ([], [])
        if not hdr: continue
        col = {m._norm(h)[:6]: i for i, h in enumerate(hdr)}; i_of, i_nu = col.get('ofreci'), col.get('nubes ')
        por_modelo = {}
        for clave, _ in MODELOS_ORDEN:
            r = next((r for r in rows if clave in m._norm(r[0])), None)
            por_modelo[clave] = marcas_nubes(r[i_of], r[i_nu]) if r and i_of is not None and i_nu is not None else {}
        datos.append((d, por_modelo))
    if not datos: return ''
    TXT = {'of': 'Sí', 'cond': 'Cond.', 'no': 'Menc.'}
    th = '<tr><th class="vcol">Vendor</th><th class="mcol">Modelo</th>' + ''.join(f'<th class="grupo c">{esc(pn)}</th>' for pn, _ in PLATAFORMAS) + '</tr>'
    filas = []
    for gi, (d, por_modelo) in enumerate(datos):
        for k, (clave, _) in enumerate(MODELOS_ORDEN):
            bg, fg = COLOR_MODELO[clave]
            celdas = ''.join((lambda est: f'<td class="c g{gi % 2}">' + (f'<span class="tile {est}" style="--mc:{bg};--mt:{fg}">{TXT[est]}</span>' if est else '<span class="tile vacio"></span>') + '</td>')(por_modelo.get(clave, {}).get(pn)) for pn, _ in PLATAFORMAS)
            primera = f'<td class="vcol g{gi % 2}" rowspan="{len(MODELOS_ORDEN)}"><span class="vname">{esc(m.nombre(d["vendor"]))}</span></td>' if k == 0 else ''
            filas.append((gi, f'<tr class="{"fin" if k == len(MODELOS_ORDEN) - 1 else ""}">{primera}<td class="mcol g{gi % 2}"><span class="mlab" style="--mc:{bg}">{esc(NOMBRE_MODELO_LARGO[clave].split(" / ")[0])}</span></td>{celdas}</tr>'))
    cuerpos = ''.join('<tbody class="grupo-vendor">' + ''.join(f for g, f in filas if g == gi) + '</tbody>' for gi in range(len(datos)))
    return '<div class="comp ancha invertida"><table><thead>' + th + '</thead>' + cuerpos + '</table></div>'

def seccion_despliegue(md, V):
    secs = m.sections(md); H = ['<section class="seccion"><p class="sec-eye">Comparativo 1 de 3</p><h2>Modelos de despliegue y nubes</h2>']
    H.append('<p class="small">Qué modelo ofrece cada vendor (SaaS, PaaS, nube privada, on-premise, híbrido), en qué nubes y cuáles quedan excluidas o sin especificar. Cada «Sí», «No» o «Condicionado» tiene su cita documental en el análisis de despliegue del vendor, incluido en su especificación.</p>')
    hdr, rows = tabla_de(m.find_section(secs, 'por proveedor'))
    if hdr:
        def r(i, c): return chip(c) if 1 <= i <= 5 else (f'<b>{esc(m.nombres_en_texto(c))}</b>' if i == 0 else m.inline(esc(c)))
        H.append('<h3>Modelos por vendor</h3>' + tabla_html(hdr, rows, r))
    gn = grids_nubes(V)
    tmn = tabla_modelo_nube(V)
    if tmn: H.append('<h3 style="page-break-before:always">En qué nube o plataforma se ofrece cada modelo</h3><p class="small">Complemento de la tabla anterior: para cada vendor y cada modelo, las nubes o plataformas (AWS, Azure, GCP, Huawei, OCI, OpenShift, nube privada del vendor…) que sus documentos asocian a ese modelo, con la condición que declaran. Celda vacía de nubes = el modelo no aplica o el vendor no lo especifica. Cada celda indica el documento de origen; la cita completa está en el análisis de despliegue del vendor.</p>' + tmn)
    if gn: H.append('<h3 style="page-break-before:always">Resumen por vendor: plataformas por modelo</h3><p class="small">La misma información de la tabla anterior, en cuadrícula: una fila por modelo y una columna por nube o plataforma. Solo marca lo que los documentos del vendor asocian a cada modelo; la fuente de cada fila está en la tabla anterior.</p>' + gn)
    ta = tabla_nubes_ancha(V)
    if ta: H.append('<div class="hoja-nubes"><h3>Vista alternativa: vendors por fila, nubes y modelos en columnas</h3><p class="small">Cada vendor en una fila y cada nube o plataforma en un grupo de columnas; dentro del grupo, una ficha por modelo de despliegue. El color de la ficha dice qué modelo es y su relleno si la nube se ofrece, es condicionada o solo se menciona (leyenda al pie). Debajo del nombre de cada nube, cuántos vendors la ofrecen en firme.</p>' + ta + '</div>')
    ti = tabla_nubes_invertida(V) if INCLUIR_VISTA_INVERTIDA else ''
    if ti: H.append('<h3 style="page-break-before:always">Vista invertida: modelos como filas dentro de cada vendor, nubes en columnas</h3><p class="small">Misma información que la vista anterior con los ejes cambiados: cada vendor agrupa cinco filas (SaaS, PaaS, nube privada, on-premise, híbrido) y cada columna es una nube o plataforma. La ficha toma el color del modelo de su fila y su texto indica el estado: Sí = ofrecida, Cond. = condicionada o solo compatibilidad declarada, Menc. = mencionada pero el modelo no se ofrece; barra gris = no la asocia.</p>' + ti)
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
