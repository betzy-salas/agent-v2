#!/usr/bin/env python3
"""F0 · Mapa de secciones de cada PDF: vendors/<vendor>/docs/txt/<nombre>.toc.md

Localiza las páginas de índice del documento, parsea sus entradas (número de sección, título,
página impresa), verifica el desfase página PDF − página impresa buscando los encabezados en el
cuerpo, y escribe el mapa con ambas numeraciones. Añade una asignación SUGERIDA de secciones a
las dimensiones T1–T8 por palabras clave, que la persona debe revisar.

Uso: python scripts/01a_toc_pdf.py <vendor> [--forzar]
"""
import re, sys, collections
from _comun import arg_vendor, vendor_dir

v = arg_vendor(); d = vendor_dir(v); forzar = '--forzar' in sys.argv
txtdir = d / 'docs' / 'txt'
CLAVES = {
    'T1 Arquitectura': r'arquitectura|visi[oó]n general|descripci[oó]n general del producto|roadmap|multi.?tenan',
    'T2 Infraestructura y cloud': r'infraestructura|cloud|nube|red\b|redes|networking|hardware|dimensionamiento|hosting',
    'T3 Integración': r'integraci[oó]n|api|interfaces|eventos|mensajer[ií]a|gateway|iso ?20022|iso ?8583',
    'T4 Datos': r'\bdatos\b|data\b|base de datos|anal[ií]tica|reporter[ií]a|migraci[oó]n|lakehouse|warehouse',
    'T5 Desarrollo': r'desarrollo|sdk|devops|devsecops|customizaci[oó]n|personalizaci[oó]n|parametr|pruebas|testing|ci/cd',
    'T6 Seguridad': r'seguridad|security|certificaci|cifrado|identidad|acceso|iam|pci|iso ?27001|cumplimiento',
    'T7 Continuidad': r'continuidad|disaster|recuperaci[oó]n|dr\b|rto|rpo|disponibilidad|contingencia|respaldo|backup',
    'T8 Soporte': r'soporte|sla|mantenimiento|servicio|capacitaci[oó]n|transferencia|escalamiento|garant[ií]a|salida',
}
def paginas_de(txt):
    parts = re.split(r'\n\n===== PAGE (\d+) =====\n', txt)[1:]
    return dict(zip(map(int, parts[0::2]), parts[1::2]))
def parsear_indice(pages, cand):
    lines = [l.strip() for n in cand for l in pages[n].splitlines() if l.strip()]
    entries, i = [], 0
    while i < len(lines):
        m = re.match(r'^(\d+(?:\.\d+)*)\.?\s*(.*)$', lines[i])
        if m and (not m.group(2) or re.search(r'\.{3,}|\d+\s*$', m.group(2))):
            num, rest, j = m.group(1), m.group(2), i + 1
            while not re.search(r'\d+\s*$', rest) and j < len(lines) and not re.match(r'^\d+(\.\d+)+\.?\s*$', lines[j]):
                rest += ' ' + lines[j]; j += 1
            pm = re.search(r'(\d+)\s*$', rest)
            if pm and 1 <= int(pm.group(1)) <= len(pages) + 5:
                title = re.sub(r'\s*\.{2,}.*$', '', rest).strip(); title = re.sub(r'\s+\d+$', '', title).strip()
                if title and len(title) < 160: entries.append((num, title, int(pm.group(1))))
            i = j
        else: i += 1
    return entries
def desfase(pages, entries):
    votos = collections.Counter()
    for num, title, p in entries:
        if num.count('.') != 1: continue
        pat = re.escape(' '.join(title.split()[:3]))
        for dlt in (0, 1, 2, 3, -1):
            if (p + dlt) in pages and re.search(pat, pages[p + dlt], re.I) and re.search(re.escape(num) + r'\.?\s', pages[p + dlt]):
                votos[dlt] += 1; break
    return (votos.most_common(1)[0] if votos else (None, 0)), votos
for f in sorted(txtdir.glob('*.txt')):
    raw = (d / 'docs' / 'raw' / f'{f.stem}.pdf')
    if not raw.exists() and not (d / 'docs' / 'raw' / f'{f.stem}.PDF').exists(): continue  # solo PDFs
    toc_path = txtdir / f'{f.stem}.toc.md'
    if toc_path.exists() and not forzar: print(f'· {f.stem}: ya existe .toc.md (usa --forzar)'); continue
    pages = paginas_de(f.read_text(encoding='utf-8', errors='replace'))
    cand = [n for n, p in pages.items() if sum(1 for l in p.splitlines() if re.search(r'\.{3,}\s*\d+\s*$|\s\d{1,3}\s*$', l)) > 12 and n <= max(15, len(pages) // 8)]
    entries = parsear_indice(pages, cand) if cand else []
    (dlt, votos_ok), votos = desfase(pages, entries) if entries else ((None, 0), {})
    out = [f'# Mapa de secciones — {f.stem}', '',
           f'Archivo texto: `docs/txt/{f.name}` (marcadores `===== PAGE n =====`, n = página PDF). Total: {len(pages)} páginas PDF.']
    if not entries:
        out += ['', '**No se detectó un índice en el documento.** Construye el mapa a mano: abre el PDF, localiza la tabla de contenido y lista `sección → p. PDF`.', '',
                '## Páginas con títulos detectados (heurístico)', '', '| p. PDF | primera línea |', '|---|---|']
        out += [f'| {n} | {next((l.strip() for l in p.splitlines() if l.strip()), "")[:90]} |' for n, p in pages.items() if re.match(r'^\s*\d+(\.\d+)*\.?\s+[A-ZÁÉÍÓÚ]', p.strip()[:60])][:120]
        toc_path.write_text('\n'.join(out) + '\n', encoding='utf-8'); print(f'· {f.stem}: SIN índice detectado → mapa heurístico'); continue
    out += [f'Índice del documento en PDF p.{min(cand)}–{max(cand)} ({len(entries)} entradas).', '']
    if dlt is None: out += ['**Desfase no verificado**: no se pudieron localizar los encabezados en el cuerpo. Compruébalo a mano antes de citar.']
    else:
        out += [f'**Desfase: página PDF = página impresa + {dlt}** (verificado en {votos_ok} encabezados de nivel 2; votos {dict(votos)}).',
                'Las páginas de la tabla «Índice completo» se dan en las dos numeraciones; cita siempre la PDF.']
    out += ['', '## Secciones por dimensión (SUGERIDO por palabras clave — revisar y corregir a mano)', '', '| Dimensión | Secciones candidatas (p. PDF) |', '|---|---|']
    dd = dlt or 0
    for dim, pat in CLAVES.items():
        hits = [f'{num} {t[:45]} (p.{p+dd})' for num, t, p in entries if num.count('.') <= 1 and re.search(pat, t, re.I)]
        out.append(f'| {dim} | {" · ".join(hits[:8]) if hits else "—"} |')
    out += ['', '## Índice completo (del propio documento)', '', '| Sección | Título | p. impresa | p. PDF |', '|---|---|---|---|']
    for num, t, p in entries:
        out.append(f'| {"&nbsp;&nbsp;" * num.count(".")}{num} | {t} | {p} | {p + dd if dlt is not None else "?"} |')
    toc_path.write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(f'· {f.stem}: {len(entries)} entradas, desfase {"+"+str(dlt) if dlt is not None else "NO verificado"} → {toc_path.name}')
