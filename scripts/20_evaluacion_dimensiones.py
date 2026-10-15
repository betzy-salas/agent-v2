#!/usr/bin/env python3
"""Flujo nuevo e independiente: lee las matrices técnicas nuevas (un Excel por vendor en matrices/) y prepara, por vendor y por
dimensión (= hoja), el material para evaluar el resultado de la calificación del Banco. No depende de vendors/, ni de T1..T8, ni de las
verificaciones anteriores. Las calificaciones son las del Banco tal cual (columna VA); no se recalifica.

Por cada Excel de matrices/ (el vendor se toma del nombre del archivo):
  matrices/evaluacion/<vendor>/<hoja>.md        lectura completa de la hoja: puntaje y nivel de la dimensión, tabla por categoría y todos
                                                los ítems con pregunta, respuesta del proveedor, calificación y sustento del evaluador.
  matrices/evaluacion/<vendor>/EVALUACION_<vendor>.md   documento de evaluación por dimensión con marcadores que completa el agente
                                                evaluador-dimensiones (<!-- evaluacion: <hoja> --> y <!-- evaluacion-general -->).
  matrices/evaluacion/EVALUACION_DIMENSIONES.md tabla vendors × dimensiones (puntaje y nivel) y enlace a cada evaluación.

Puntaje de dimensión y de categoría: media de las calificaciones (0–4) sobre 4, ponderada por criticidad (Indispensable/Killer 3,
Deseable/No killer 1), en 0–100. Nivel oficial: ≥ 85 Cumple plenamente · 70–84 Cumple · 50–69 Parcial · < 50 No cumple.

Uso:  python scripts/20_evaluacion_dimensiones.py [--vendor nombre] [--carpeta matrices]
      python scripts/20_evaluacion_dimensiones.py --validar [--vendor nombre]   # señala conteos, puntajes o listas telegráficas en las evaluaciones escritas
"""
import datetime, importlib.util, re, sys
from collections import OrderedDict
from pathlib import Path

AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parent
def _cargar(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, AQUI / archivo); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
p18 = _cargar('p18', '18_resumen_matriz.py'); m07 = _cargar('m07', '07_informe_implementacion.py')
import openpyxl

def vendor_de(archivo):
    """Vendor a partir del nombre del archivo: la carpeta de vendors/ o el nombre oficial que contenga; si no, el propio nombre del archivo."""
    base = re.sub(r'[^a-z0-9]', '', archivo.stem.lower())
    for slug, real in sorted(m07.NOMBRES_VENDOR.items(), key=lambda kv: -len(kv[1])):
        if re.sub(r'[^a-z0-9]', '', real.lower()) in base or re.sub(r'[^a-z0-9]', '', slug.lower()) in base: return slug
    return re.sub(r'[^A-Za-z0-9_-]+', '_', archivo.stem).strip('_').lower()

def md_hoja(vendor, hoja, dim, items):
    p = p18.puntaje(items); cats = OrderedDict()
    for it in items: cats.setdefault(it['cat'], []).append(it)
    sc = sum(1 for i in items if i['va'] is None); dist = {k: sum(1 for i in items if i['va'] == k) for k in range(5)}
    L = [f'# {m07.nombre(vendor)} · Dimensión {hoja}' + (f' · {dim}' if dim else ''), '',
         f'**Puntaje de la dimensión: {p if p is not None else "—"} / 100 · {p18.nivel(p)}** · {len(items)} ítems · calificaciones: 4 → {dist[4]}, 3 → {dist[3]}, 2 → {dist[2]}, 1 → {dist[1]}, 0 → {dist[0]}' + (f', sin calificar → {sc}' if sc else '') + '.', '',
         '## Categorías', '', '| Categoría | Ítems | Puntaje | Nivel | Indispensables o Killer con 0 o 1 |', '|---|---|---|---|---|']
    for c, its in cats.items():
        pc = p18.puntaje(its); bajos = [i['n'] for i in its if i['va'] in (0, 1) and p18.peso(i) == 3]
        L.append(f'| {p18.celda(c)} | {len(its)} | {pc if pc is not None else "—"} | {p18.nivel(pc)} | {", ".join(bajos) or "—"} |')
    L += ['', '## Ítems (lectura completa)', '']
    for c, its in cats.items():
        L += [f'### {c}', '']
        for it in its:
            cal = f'{p18.ESCALA[it["va"]]} ({it["va"]})' if it['va'] is not None else 'Sin calificar (—)'
            if p18.incoherente(it): cal += f' ⚠ clasificación textual «{it["eval"]}» no coincide con el VA'
            L += [f'**{it["n"]}** · {it["crit"] or "sin criticidad"} · **{cal}**' + (f' · evaluador: {it["evaluador"]}' if it['evaluador'] else ''), '',
                  f'- Pregunta: {it["q"]}', f'- Respuesta del proveedor: {it["resp"] or "(vacía)"}', f'- Sustento del evaluador: {it["sus"] or "(sin sustento)"}', '']
    return '\n'.join(L) + '\n', p

PATRONES = [(r'\b\d+\s*(criterios?|[ií]tems?|preguntas?|requerimientos?|categor[ií]as?)\b', 'conteo de ítems o criterios'),
            (r'\b\d+\s*(de|sobre)\s*\d+\b', 'conteo «n de m»'),
            (r'\b\d{1,3}([.,]\d)?\s*/\s*100\b|\bpuntaje\b|\bpuntuaci[oó]n\b', 'puntaje en la prosa'),
            (r'\b(la mayor[ií]a|todos|ninguno|varios|muchos)\s+(de\s+los\s+)?(criterios|[ií]tems)\s+(est[aá]n|obtuv|con\s+\d)', 'conteo encubierto'),
            (r'\b(porque|ya que|dado que)\s+\d+\s', 'justificación numérica'),
            (r'\b(est[aá]n|quedan|quedaron|obtuvieron)\s+en\s+(no cumple|parcial|cumple)', 'nivel usado como conteo'),
            (r'^\s*\*?\*?E\d+\*?\*?\s*[:·-]', 'lista telegráfica que empieza por el código'),
            (r'(E\d+\s*:\s*[^;.]{3,40};\s*){2,}', 'lista telegráfica E<n>: …; E<n>: …')]
def validar(carpeta, solo=None):
    """Señala, en las evaluaciones ya escritas, frases con conteos, puntajes o estilo de lista (prohibidos en la prosa)."""
    hallazgos = 0
    for f in sorted((carpeta / 'evaluacion').glob('*/EVALUACION_*.md')):
        if solo and f.parent.name != solo: continue
        en_prosa = False
        for n, linea in enumerate(f.read_text(encoding='utf-8').splitlines(), 1):
            if linea.startswith('## Dimensión') or linea.startswith('## Evaluación general'): en_prosa = True; continue
            if linea.startswith('## ') or linea.startswith('|') or linea.startswith('**') and '/ 100' in linea or linea.startswith('<!--') or not linea.strip(): continue
            if not en_prosa: continue
            for pat, que in PATRONES:
                mm = re.search(pat, linea, re.I | re.M)
                if mm: hallazgos += 1; print(f'{f.relative_to(RAIZ)}:{n}: {que}: «…{linea[max(0, mm.start() - 50):mm.end() + 50].strip()}…»')
    print('Validación:', 'sin hallazgos' if not hallazgos else f'{hallazgos} frases por reescribir (sin conteos ni puntajes en la prosa; frases completas con el E<n> al final)')
    return hallazgos

def main():
    args = sys.argv[1:]
    if '--validar' in args:
        carpeta = RAIZ / (args[args.index('--carpeta') + 1] if '--carpeta' in args else 'matrices')
        sys.exit(1 if validar(carpeta, args[args.index('--vendor') + 1] if '--vendor' in args else None) else 0)
    carpeta = RAIZ / (args[args.index('--carpeta') + 1] if '--carpeta' in args else 'matrices')
    solo = args[args.index('--vendor') + 1] if '--vendor' in args else None
    archivos = [p for p in sorted(carpeta.glob('*.xls*')) if not p.name.startswith('~$')]
    if not archivos: sys.exit(f'No hay Excel en {carpeta}. Deja ahí la matriz nueva de cada vendor (nombre del archivo con el vendor).')
    hoy = datetime.date.today().strftime('%d-%m-%Y'); salida = carpeta / 'evaluacion'; salida.mkdir(exist_ok=True)
    resumen = []   # (vendor, archivo, [(hoja, dim, puntaje, n)])
    for xlsx in archivos:
        v = vendor_de(xlsx)
        if solo and v != solo and m07.nombre(v).lower() != solo.lower(): continue
        print(f'\n== {xlsx.name} → vendor «{v}» ({m07.nombre(v)})')
        wb = openpyxl.load_workbook(xlsx, data_only=True); hojas = p18.hojas_matriz(wb, informar=True)
        if not hojas: print('  sin hojas de matriz; se omite'); continue
        dv = salida / v; dv.mkdir(exist_ok=True); filas = []
        E = [f'# Evaluación por dimensión — {m07.nombre(v)}', '', f'- Matriz: {xlsx.relative_to(RAIZ)}', f'- Fecha: {hoy}',
             '- Base: calificación del Banco (columna VA, 0–4) y sustento del evaluador, tal como están en la matriz. Sin recalificación.',
             '- Puntaje: media de las calificaciones sobre 4 ponderada por criticidad (Indispensable/Killer 3, Deseable/No killer 1), en 0–100. Nivel: ≥ 85 Cumple plenamente · 70–84 Cumple · 50–69 Parcial · < 50 No cumple.',
             '- La evaluación de cada dimensión la escribe el agente evaluador-dimensiones a partir de la lectura completa de la hoja (archivo <hoja>.md de esta carpeta).', '',
             '## Resultado por dimensión', '', '| Dimensión (hoja) | Nombre | Ítems | Puntaje | Nivel | Lectura |', '|---|---|---|---|---|---|']
        cuerpo = []
        for hoja, rows, h in hojas:
            items, dim = p18.leer_hoja(rows, h)
            if not items: print(f'  {hoja}: sin ítems'); continue
            md, p = md_hoja(v, hoja, dim, items); (dv / f'{hoja}.md').write_text(md, encoding='utf-8')
            filas.append((hoja, dim, p, len(items))); print(f'  {hoja}: {len(items)} ítems · {p} · {p18.nivel(p)}')
            E.append(f'| {hoja} | {p18.celda(dim)} | {len(items)} | {p if p is not None else "—"} | {p18.nivel(p)} | [{hoja}.md]({hoja}.md) |')
            cuerpo += [f'## Dimensión {hoja}' + (f' · {dim}' if dim else ''), '', f'**{p if p is not None else "—"} / 100 · {p18.nivel(p)}**', '', f'<!-- evaluacion: {hoja} -->', '']
        E += ['', '## Evaluación general del proveedor', '', '<!-- evaluacion-general -->', ''] + cuerpo
        (dv / f'EVALUACION_{v}.md').write_text('\n'.join(E) + '\n', encoding='utf-8'); resumen.append((v, xlsx, filas))
    if not resumen: sys.exit('Ningún vendor procesado.')
    hojas_u = []
    for _, _, filas in resumen:
        for h, _, _, _ in filas:
            if h not in hojas_u: hojas_u.append(h)
    C = ['# Evaluación por dimensión — todos los proveedores (matrices nuevas)', '', f'- Fecha: {hoy} · Fuente: un Excel por vendor en {carpeta.relative_to(RAIZ)}/ · calificaciones del Banco tal cual, sin ranking.', '',
         '| Vendor | Matriz | ' + ' | '.join(hojas_u) + ' |', '|---|---|' + '---|' * len(hojas_u)]
    for v, xlsx, filas in resumen:
        por = {h: (p, d) for h, d, p, _ in filas}
        C.append(f'| {m07.nombre(v)} | {xlsx.name} | ' + ' | '.join((f'{por[h][0]} · {p18.nivel(por[h][0])}' if h in por else '—') for h in hojas_u) + ' |')
    nombres = {}
    for _, _, filas in resumen:
        for h, d, _, _ in filas:
            if d and h not in nombres: nombres[h] = d
    if nombres: C += ['', 'Dimensiones: ' + ' · '.join(f'**{h}** {d}' for h, d in nombres.items())]
    C += ['', '## Evaluaciones por vendor', ''] + [f'- {m07.nombre(v)}: [evaluacion/{v}/EVALUACION_{v}.md]({v}/EVALUACION_{v}.md)' for v, _, _ in resumen] + ['', '<!-- lectura-comparada -->', '']
    (salida / 'EVALUACION_DIMENSIONES.md').write_text('\n'.join(C) + '\n', encoding='utf-8')
    print(f'\nConsolidado: {salida.relative_to(RAIZ)}/EVALUACION_DIMENSIONES.md · vendors: {", ".join(v for v, _, _ in resumen)}')

if __name__ == '__main__':
    main()
