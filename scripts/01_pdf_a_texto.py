#!/usr/bin/env python3
"""F0 · PDF → texto con marcadores "===== PAGE n =====" (n = página PDF).

Uso: python scripts/01_pdf_a_texto.py <vendor> [--forzar]
"""
import sys, fitz
from _comun import arg_vendor, vendor_dir, escribir_nombres

v = arg_vendor(); d = vendor_dir(v); forzar = '--forzar' in sys.argv
raw, out = d / 'docs' / 'raw', d / 'docs' / 'txt'
out.mkdir(parents=True, exist_ok=True)
pdfs = sorted(raw.glob('*.pdf')) + sorted(raw.glob('*.PDF'))
if not pdfs: sys.exit(f"No hay PDF en vendors/{v}/docs/raw")
for pdf in pdfs:
    destino = out / f'{pdf.stem}.txt'
    if destino.exists() and not forzar:
        print(f'· {pdf.name}: ya existe {destino.name} (usa --forzar)'); continue
    doc = fitz.open(pdf); vacias = 0
    with open(destino, 'w', encoding='utf-8') as o:
        for i, p in enumerate(doc, 1):
            t = p.get_text()
            if not t.strip(): vacias += 1
            o.write(f'\n\n===== PAGE {i} =====\n{t}')
    aviso = f'  ⚠ {vacias} páginas sin texto (¿escaneado? necesita OCR)' if vacias else ''
    print(f'· {pdf.name}: {len(doc)} páginas → {destino.name}{aviso}')
print('NOMBRES.md actualizado:', escribir_nombres(d).relative_to(d.parent.parent))
