#!/usr/bin/env python3
"""Exporta como PNG la cuadrícula «plataformas por modelo»: la hoja 4 del informe de comparativos y la diapositiva del deck T5.
Lee los PDF ya generados (no los regenera): vendors/INFORME_COMPARATIVOS.pdf (scripts/08 --pdf) y <base>/PRESENTACION_T5_COE.pdf
(scripts/10 --pdf --estilo coe). Localiza la página por su texto («plataformas por modelo» + «Otras»), así no depende del número de hoja.

Uso:  python scripts/17_imagenes_despliegue.py [--base carpeta] [--dpi 220]
Salida: <base>/HOJA_4_plataformas_por_modelo.png y <base>/DIAPOSITIVA_plataformas_por_modelo.png (requiere PyMuPDF: pip install pymupdf)
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

def pagina(pdf, *claves):
    import fitz
    d = fitz.open(pdf)
    for p in d:
        t = p.get_text()
        if all(k.lower() in t.lower() for k in claves): return p
    return None

def main():
    args = sys.argv[1:]
    base = RAIZ / (args[args.index('--base') + 1] if '--base' in args else 'presentacion_t5')
    dpi = int(args[args.index('--dpi') + 1]) if '--dpi' in args else 220
    try: import fitz  # noqa
    except ImportError: sys.exit('AVISO: falta PyMuPDF (pip install pymupdf)')
    tareas = [(RAIZ / 'vendors' / 'INFORME_COMPARATIVOS.pdf', ('plataformas por modelo', 'Otras'), base / 'HOJA_4_plataformas_por_modelo.png'),
              (base / 'PRESENTACION_T5_COE.pdf', ('plataformas por modelo', 'Modelo:', 'Otras'), base / 'DIAPOSITIVA_plataformas_por_modelo.png')]
    for pdf, claves, out in tareas:
        if not pdf.exists(): print(f'AVISO: no existe {pdf} (genera primero el PDF)'); continue
        p = pagina(pdf, *claves)
        if p is None: print(f'AVISO: en {pdf.name} no hay página con {claves}'); continue
        pix = p.get_pixmap(dpi=dpi); pix.save(out); print(f'PNG: {out} · página {p.number + 1} de {pdf.name} · {pix.width}×{pix.height}')

if __name__ == '__main__':
    main()
