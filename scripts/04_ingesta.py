#!/usr/bin/env python3
"""Pipeline de ingesta de un vendor: 01 PDF → txt, 01a mapas de secciones, 01b anexos → txt,
02 matriz → T1..T8, y actualiza la tabla de documentos de INVENTARIO.md. Muestra los conteos.

Uso: python scripts/04_ingesta.py <vendor> [--forzar]
"""
import re, sys, subprocess, hashlib, datetime, zipfile
from pathlib import Path
from _comun import arg_vendor, vendor_dir, RAIZ, archivos_raw, slug_de

v = arg_vendor(); d = vendor_dir(v); extra = [a for a in sys.argv[2:] if a.startswith('--')]
py = sys.executable
def run(script, *args):
    print(f"\n▶ {script} {v} {' '.join(args)}"); r = subprocess.run([py, str(RAIZ / 'scripts' / script), v, *args]); 
    if r.returncode: print(f"  ⚠ {script} terminó con código {r.returncode}")
raw = d / 'docs' / 'raw'
archivos = archivos_raw(raw)
if not archivos: sys.exit(f"vendors/{v}/docs/raw está vacío: copia ahí los documentos del vendor.")
if any(p.suffix.lower() == '.pdf' for p in archivos): run('01_pdf_a_texto.py', *extra); run('01a_toc_pdf.py', *extra)
if any(p.suffix.lower() in ('.xlsx', '.xlsm', '.pptx') for p in archivos): run('01b_anexos_a_texto.py', *[a for a in extra if a != '--forzar'])
run('02_matriz_a_texto.py')

# ---- INVENTARIO: tabla de documentos
def fecha_meta(p):
    try:
        if p.suffix.lower() == '.pdf':
            import fitz; m = fitz.open(p).metadata.get('modDate', '') or ''
            mm = re.search(r'D:(\d{4})(\d{2})(\d{2})', m); return f"{mm.group(1)}-{mm.group(2)}-{mm.group(3)}" if mm else '—'
        core = zipfile.ZipFile(p).read('docProps/core.xml').decode('utf8')
        mm = re.search(r'<dcterms:modified[^>]*>(\d{4}-\d{2}-\d{2})', core); return mm.group(1) if mm else '—'
    except Exception: return '—'
def unidades(p):
    t = d / 'docs' / 'txt' / f'{slug_de(p, raw)}.txt'
    if not t.exists(): return '—'
    s = t.read_text(encoding='utf-8', errors='replace')
    n = len(re.findall(r'^===== (PAGE|SHEET|SLIDE)', s, re.M)); return f"{n} {'pp.' if 'PAGE' in s else 'hojas' if 'SHEET' in s else 'slides'}"
filas = []
for p in archivos:
    tipo = {'.pdf': 'PDF', '.xlsx': 'Excel', '.xlsm': 'Excel', '.pptx': 'PPTX', '.docx': 'Word'}.get(p.suffix.lower(), p.suffix)
    sl = slug_de(p, raw); txt_ok = (d / 'docs' / 'txt' / f'{sl}.txt').exists(); toc_ok = (d / 'docs' / 'txt' / f'{sl}.toc.md').exists()
    filas.append(f"| {p.relative_to(raw)} | {tipo} | {fecha_meta(p)} | _(completar)_ | {unidades(p)} · {p.stat().st_size // 1024} KB · txt {'✓' if txt_ok else '—'} · toc {'✓' if toc_ok else '—'} |")
inv = d / 'INVENTARIO.md'; s = inv.read_text(encoding='utf-8') if inv.exists() else f"# INVENTARIO — {v}\n\n"
tabla = "| Archivo (docs/raw) | Tipo | Fecha/versión | Dimensiones que toca | Notas |\n|---|---|---|---|---|\n" + "\n".join(filas)
if re.search(r'\| Archivo \(docs/raw\) \|.*?(?=\n## |\Z)', s, re.S):
    s = re.sub(r'\| Archivo \(docs/raw\) \|.*?(?=\n## |\Z)', tabla, s, count=1, flags=re.S)
else: s += "\n" + tabla + "\n"
conteos = {f.stem: sum(1 for l in f.read_text(encoding='utf-8').splitlines() if l.startswith('[E')) for f in sorted((d / 'matriz').glob('T*.txt'))}
estado = (f"\n## Estado de la ingesta\n\nActualizado {datetime.date.today().isoformat()} por scripts/04_ingesta.py.\n\n"
          f"| Paso | Estado |\n|---|---|\n| Documentos en docs/raw | {len(archivos)} |\n| Convertidos a docs/txt | {len(list((d/'docs'/'txt').glob('*.txt')))} |\n"
          f"| Mapas .toc.md | {len(list((d/'docs'/'txt').glob('*.toc.md')))} |\n| Matriz T1–T8 | {' · '.join(f'{k} {n}' for k,n in conteos.items())} = {sum(conteos.values())} ítems |\n")
s = re.sub(r'\n## Estado de la ingesta\n.*?(?=\n## |\Z)', estado, s, count=1, flags=re.S) if '## Estado de la ingesta' in s else s + estado
inv.write_text(s, encoding='utf-8')
print(f"\n✔ INVENTARIO.md actualizado. Ítems por hoja: {conteos} → total {sum(conteos.values())}")
print(f"Revisa: vendors/{v}/NOMBRES.md (nombres oficiales para citar) y los .toc.md (desfase y secciones por dimensión).")
