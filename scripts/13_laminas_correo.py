#!/usr/bin/env python3
"""Dos láminas para adjuntar a un correo (PNG 16:9 a doble resolución + PDF), con el diseño del deck corporativo.

Lámina 1 · Resultado T5: ranking de vendors (puntaje, nivel, categorías en verde/amarillo/rojo) y la primera idea de la «Lectura general»
de la ficha T5 de cada vendor; franja con la lectura de la escala.
Lámina 2 · Implementación y despliegue: porcentajes de la rúbrica (EI, F, I), duración, implementador y señales por vendor; modelos de
despliegue ofrecidos y nubes; «Veredicto en una frase» de implementación de cada vendor.

No calcula ni redacta nada: toma lo ya escrito en <base>/<vendor>/9_semaforo_T5.md y 10_ficha_T5.md, en vendors/<vendor>/informes/7_ y 8_,
verif/IMPL.md y vendors/COMPARATIVO_IMPLEMENTACION.md (mismas fuentes que la presentación T5, scripts 10 y 12).

Uso:  python scripts/13_laminas_correo.py [--base carpeta]      (por defecto vendors/)
Salida: <base>/LAMINAS_CORREO.html, .pdf y LAMINA_1_resultado_T5.png, LAMINA_2_implementacion.png (2560×1440).
"""
import datetime, html, importlib.util, re, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parent
spec = importlib.util.spec_from_file_location('p10', AQUI / '10_presentacion_t5.py'); p10 = importlib.util.module_from_spec(spec); spec.loader.exec_module(p10)
m = p10.m
esc = html.escape

CSS = p10.CSS_COE + """
.rk{display:flex;align-items:center;gap:7pt;padding:8pt 0;border-bottom:1px solid #e3e6ec} .rk .pos{width:22pt;height:22pt;border-radius:50%;background:#ff6400;color:#fff;font-weight:800;font-size:10pt;display:flex;align-items:center;justify-content:center;flex:none}
.rk .v{width:92pt;font-weight:800;color:#00205b;font-size:12pt;flex:none} .rk .n{font-family:"JetBrains Mono",Consolas,monospace;font-weight:700;font-size:16pt;width:40pt;text-align:right;flex:none}
.rk .tr{flex:1;height:10pt;background:#eef1f4;border-radius:5pt;overflow:hidden} .rk .tr i{display:block;height:100%} .rk .lv{width:80pt;flex:none;text-align:center} .rk .sm{width:60pt;flex:none;font-size:7.6pt;color:#5f6b7a;text-align:right;white-space:nowrap}
.lect{border-bottom:1px solid #e3e6ec;padding:3pt 0 2.5pt} .lect .vn{display:block;color:#00205b;font-size:8.6pt;margin-bottom:.5pt} .lect ul{margin:0;padding-left:10pt;font-size:7.4pt;line-height:1.27} .lect li{margin:0} .lect li b{color:#00205b} .lect li i{font-style:normal;color:#5f6b7a;font-size:6.8pt}
.franja{margin-top:10pt;background:#eef1f4;border-radius:5pt;padding:8pt 14pt;font-size:8pt;color:#3d4a5c;line-height:1.4} .franja b{color:#00205b}
.ver{font-size:8.7pt;line-height:1.38;border-bottom:1px solid #e3e6ec;padding:4pt 0} .ver b{color:#00205b}
.pie img{height:18pt}
"""

NEGATIVO = re.compile(r'descuent|\brest[aá]|brecha|\bcae\b|riesgo|contradic|falta|pendiente|\bpero\b|no cumple|rojo|parcial|exposici|diferencia', re.I)
def frase_sustento(texto):
    """Frase en positivo de la lectura general: lo que el vendor ofrece y hace coherente su resultado. Se descartan las frases con descuentos,
    brechas o «pero»; entre las positivas se prefiere la que no repite cifras. Si ninguna es positiva, la primera frase."""
    frases = [f.strip() for f in re.split(r'(?<=[.!?])\s+', (texto or '').strip()) if f.strip()]
    positivas = [f for f in frases if not NEGATIVO.search(f)]
    return next((f for f in positivas if not re.search(r'\d', f)), positivas[0] if positivas else (frases[0] if frases else ''))

SUJETO = re.compile(r'^(?:(?:en\s+)?(?P<items>E\d+(?:\s*,\s*E\d+)*(?:\s*(?:y|e)\s*E\d+)?)\s+)?(?:(?:el|la)\s+(?:proveedor|vendor|propuesta|respuesta|verificación)\s+|se\s+)?(?:describe|describen|declara|declaran|propone|proponen|plantea|plantean|reporta|reportan|indica|indican|presenta|presentan|menciona|mencionan|documenta|documentan|ofrece|ofrecen|define|definen|muestra|muestran)\s+', re.I)
CORTE = re.compile(r',?\s+(?:y|e)\s+(?:el\s+evaluador|la\s+verificaci[oó]n|el\s+banco)\b|,\s+(?:y\s+)?(?:lo\s+que|con\s+observaci[oó]n)\b|;', re.I)
def lo_que_ofrece(v):
    """De una fortaleza de la ficha («**Título**: en E38 y E49 el proveedor describe X, y el evaluador…») devuelve (título, X, ítems):
    el contenido concreto que el vendor ofrece, sin la valoración del evaluador y sin recortar palabras del texto original."""
    v = v.strip(); mm = re.match(r'^\*\*(.+?)\*\*\s*:?\s*(.*)$', v, re.S)
    titulo, cuerpo = (mm.group(1), mm.group(2)) if mm else ('', v)
    cuerpo = re.split(r'\s(?=(?:Fuente|Confianza)\s*:)', cuerpo)[0].strip()
    items = ''
    ms = SUJETO.match(cuerpo)
    if ms:
        items = ms.group('items') or ''; cuerpo = cuerpo[ms.end():]
    cuerpo = CORTE.split(cuerpo)[0].strip(' .,;')
    if not items:   # ítems solo en la «Fuente: E13, E18 - …» de la viñeta
        mf = re.search(r'Fuente\s*:\s*((?:E\d+(?:\s*,\s*)?)+)', v); items = ', '.join(re.findall(r'E\d+', mf.group(1))) if mf else ''
    if cuerpo: cuerpo = cuerpo[0].upper() + cuerpo[1:]
    return titulo, cuerpo, re.sub(r'\s+', ' ', items)

def titulo_vineta(v, max_palabras=12):
    """Título en negrita de una viñeta de la ficha («**Título**: …»); recortado si el título arrastra texto («… en E6 y E7 la respuesta…»)."""
    mm = re.match(r'^\*\*(.+?)\*\*', v.strip()); t = mm.group(1) if mm else re.split(r'[.:]', v.strip())[0]
    t = re.split(r'\s+(?:en|según|de acuerdo con)\s+E\d+', t)[0].strip(' :;,')
    palabras = t.split()
    return ' '.join(palabras[:max_palabras]) if len(palabras) > max_palabras else t

def construir(base):
    V = p10.cargar(base)
    if not V: sys.exit(f'No encontré ningún 9_semaforo_T5.md bajo {base}.')
    for i, d in enumerate(V):
        d['_i'] = i; d['dist_cat'], d['dist'] = p10.distribucion_items(d['ruta']); d['ficha'] = p10.leer_ficha(d['ruta'].parent / '10_ficha_T5.md')
    orden = sorted(V, key=lambda d: -(d['pct'] or 0)); pos = {d['vendor']: k + 1 for k, d in enumerate(orden)}
    logo = p10._data_uri(base / 'assets' / 'logo.png')
    MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
    t = datetime.date.today(); mes = f'{MESES[t.month - 1].capitalize()} {t.year}'
    def sem(d): return {k: sum(1 for c in d['cats'] if c['color'] == k) for k in ('VERDE', 'AMARILLO', 'ROJO')}
    def bar(titulo, derecha=''): return f'<div class="bar"><h2>{esc(titulo)}</h2><span class="r">{esc(derecha)}</span></div>'
    def pie(fuente): return f'<div class="pie"><span>{esc(fuente)}</span><span class="c">Datos elaborados por BCP para uso Interno</span>' + (f'<img src="{logo}" alt="">' if logo else '') + '</div>'
    def lay(*celdas, ancho=None):
        tds = ''.join('<td' + (' style="width:%s"' % ancho[i] if ancho else '') + '>' + c + '</td>' for i, c in enumerate(celdas))
        return '<table class="lay"><tr>' + tds + '</tr></table>'
    H = [f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Láminas T5 para correo</title>{m.FONTS}<style>{CSS}</style></head><body>']

    # ---- lámina 1 · resultado T5
    izq = '<h3 class="az">Ranking por puntaje T5</h3>'
    for d in orden:
        n = sem(d); c = p10.color_de(d['pct']); fill, ink = p10.PILL[c]
        izq += (f'<div class="rk"><span class="pos">{pos[d["vendor"]]}</span><span class="v">{esc(m.nombre(d["vendor"]))}</span><span class="n" style="color:{ink}">{d["pct"]}</span>'
                f'<span class="tr"><i style="width:{d["pct"]}%;background:{ {"VERDE": "#b8d680", "AMARILLO": "#fcc97d", "ROJO": "#f7786e"}[c] }"></i></span>'
                f'<span class="lv"><span class="pill p{p10._cls(c)}">{esc(d["nivel"])}</span></span></div>')
    der = '<h3 class="az">Lo que ofrece cada propuesta y sustenta su resultado</h3>'
    for d in orden:
        f = d['ficha'] or {}; puntos = ''
        for x in (f.get('fortalezas') or [])[:3]:
            tit, que, items = lo_que_ofrece(x)
            if not que: continue
            puntos += f'<li><b>{esc(tit)}</b>{": " if tit else ""}{esc(m.nombres_en_texto(que))}' + (f' <i>({esc(items)})</i>' if items else '') + '</li>'
        der += f'<div class="lect"><b class="vn">#{pos[d["vendor"]]} {esc(m.nombre(d["vendor"]))}</b><ul>{puntos or "<li>Sin fortalezas en la ficha.</li>"}</ul></div>'
    n_cat = len(orden[0]['cats']); n_items = sum(orden[0]['dist'].values()) if orden[0]['dist'] else None
    franja = (f'<div class="franja"><b>Cómo leer.</b> Puntaje T5 = media de las calificaciones del Banco (0–4) en la hoja T5 ponderada por criticidad (Indispensable y Killer ×3, Deseable ×1), sobre 100. '
              f'Niveles: Cumple plenamente ≥ 85 · Cumple 70–84 · Parcial 50–69 · No cumple &lt; 50. '
              'Las calificaciones son las del Banco y no se modifican; la verificación documental solo aporta la evidencia que sustenta fortalezas, debilidades y contradicciones.</div>')
    H.append(f'<section class="s">{bar("Revisión Técnica Resultados T5 · Resultado por vendor", "Capacidades de desarrollo (hoja T5) · " + mes)}<div class="body">' + lay(izq, der, ancho=('40%', '60%')) + franja + '</div>'
             + pie('Fuente: Matriz técnica del Banco, hoja T5 · semáforo y ficha T5 de cada vendor') + '</section>')

    # ---- lámina 2 · implementación y despliegue
    IMP = p10.datos_implementacion(V); g = IMP['general']
    if g:
        DESP, PLAT = p10.datos_despliegue(orden); desp = {v: filas for v, _, filas in DESP}
        hdr, rows = g['resumen']; filas = ''
        if hdr:
            col = {m._norm(h): i for i, h in enumerate(hdr)}
            def ci(*pref): return next((i for h, i in col.items() if any(h.startswith(m._norm(p)) for p in pref)), None)
            i_v, i_du, i_im, i_ei, i_f, i_i, i_se = ci('vendor'), ci('duraci'), ci('implementador'), ci('% estrategia', 'ei'), ci('% fabricante'), ci('% implementador'), ci('señales', 'senales')
            por_v = {}
            for r in rows:
                r = r + [''] * (len(hdr) - len(r)); por_v[m._norm(m.nombre(r[i_v]))] = r
            for d in orden:
                r = por_v.get(m._norm(m.nombre(d['vendor'])))
                if not r: continue
                def pc(j):
                    mm = re.search(r'[\d.]+', r[j] or '') if j is not None else None
                    lvl = p10.nivel_pct(float(mm.group(0))) if mm else None
                    return f'<td class="mono {p10._cls(lvl) if lvl else ""}" style="text-align:center;font-weight:700">{esc(r[j]) if j is not None else "—"}</td>'
                fl = desp.get(d['vendor'], [])
                ofrec = [nm for nm, cls, _, _ in fl if cls == 'si']; cond = [nm for nm, cls, _, _ in fl if cls == 'cond']
                nubes = []
                for _, _, _, marcas in fl:
                    for pn, est in marcas.items():
                        if est == 'of' and pn not in nubes and pn != 'Nube privada': nubes.append(pn)   # la nube privada ya va como modelo
                dtxt = ('<b>Ofrece:</b> ' + esc(', '.join(ofrec)) if ofrec else '<b>Ofrece:</b> —') + (' · <b>Condicionado:</b> ' + esc(', '.join(cond)) if cond else '') + ('<br><b>Nubes ofrecidas:</b> ' + esc(', '.join(nubes)) if nubes else '<br><b>Nubes ofrecidas:</b> no especifica')
                filas += (f'<tr><td class="k">#{pos[d["vendor"]]} {esc(m.nombre(d["vendor"]))}</td>{pc(i_ei)}{pc(i_f)}{pc(i_i)}<td>{esc(r[i_du]) if i_du is not None else "—"}</td><td>{esc(r[i_im]) if i_im is not None else "—"}</td>'
                          f'<td style="font-size:7.6pt">{dtxt}</td><td class="mono" style="text-align:center">{esc(r[i_se]) if i_se is not None else "—"}</td></tr>')
        vers = ''
        for d in orden:
            pv = g['por_vendor'].get(d['vendor'], {}); lst = next((v for k, v in pv.items() if 'veredicto' in m._norm(k)), [])
            if lst: vers += f'<div class="ver"><b>#{pos[d["vendor"]]} {esc(m.nombre(d["vendor"]))}.</b> {esc(m.nombres_en_texto(lst[0]))}</div>'
        H.append(f'<section class="s">{bar("Revisión Técnica Resultados T5 · Implementación y despliegue", "Rúbrica corporativa de implementación y modelos de despliegue · " + mes)}<div class="body">'
                 + '<table class="t" style="font-size:8.1pt"><thead><tr><th style="width:12%">Vendor (ranking T5)</th><th style="width:8%">% Estrategia (EI)</th><th style="width:8%">% Fabricante (F)</th><th style="width:11%">% Implementador (I)</th><th style="width:11%">Duración propuesta</th><th style="width:17%">Implementador</th><th>Modelos de despliegue y nubes ofrecidos</th><th style="width:6%">Señales de alerta</th></tr></thead><tbody>' + filas + '</tbody></table>'
                 + '<p class="leg" style="margin:5pt 0 6pt;font-size:8pt">Rúbrica 0–5 por criterio, ponderada: EI estrategia de implementación · F perfil del fabricante · I perfil del implementador. Color por nivel: <i class="V"></i>≥ 70 <i class="A"></i>50–69 <i class="R"></i>&lt; 50. Despliegue: modelos que el vendor ofrece (Sí) o condiciona y nubes en firme para esos modelos, según sus documentos.</p>'
                 + '<h3 class="az" style="font-size:12.5pt;margin-top:2pt">Veredicto de implementación en una frase</h3>' + vers + '</div>'
                 + pie('Fuente: rúbrica de implementación (IMPL), informes 7_ y 8_ y comparativo de implementación de cada vendor') + '</section>')
    H.append('</body></html>')
    return '\n'.join(H)

def main():
    args = sys.argv[1:]
    base = Path(args[args.index('--base') + 1]) if '--base' in args else RAIZ / 'vendors'
    if not base.is_absolute(): base = RAIZ / base
    out = base / 'LAMINAS_CORREO.html'; out.write_text(construir(base), encoding='utf-8'); print(f'HTML: {out}')
    pdf = out.with_suffix('.pdf'); m.a_pdf(out, pdf)
    try:
        import fitz
    except ImportError:
        sys.exit('PDF listo; para los PNG instala PyMuPDF: pip install pymupdf')
    doc = fitz.open(pdf); nombres = ['LAMINA_1_resultado_T5.png', 'LAMINA_2_implementacion.png']
    for i, page in enumerate(doc):
        if i >= len(nombres): break
        pix = page.get_pixmap(dpi=192); pix.save(base / nombres[i]); print(f'PNG: {base / nombres[i]} · {pix.width}×{pix.height}')
    if doc.page_count != len(nombres): print(f'AVISO: el PDF tiene {doc.page_count} páginas (se esperaban {len(nombres)}): alguna lámina se desbordó.')

if __name__ == '__main__':
    main()
