#!/usr/bin/env python3
"""Valida la ficha T5 de un vendor (<base>/<vendor>/10_ficha_T5.md): que las viñetas sean sustanciales y con fuente.

Rechaza viñetas vacías del tipo «Cumple con el criterio E3» y exige, por viñeta: 25 palabras o más de texto, al menos un
ítem E<n>, una «Fuente:», sin puntos suspensivos; en Fortalezas además un «Confianza:». La tabla «Resumen por
categoría» debe tener las 16 categorías. Código de salida 1 si hay errores, con la lista exacta para corregir.

Uso:  python scripts/11_validar_ficha.py <vendor> [--base carpeta]   (por defecto vendors/<vendor>/informes/10_ficha_T5.md)
"""
import re, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
VACIAS = re.compile(r'^(?:el vendor |el proveedor )?(?:cumple|no cumple|cubre|no cubre|responde|declara)\s+(?:con\s+)?(?:el |los |la |las )?(?:criterios?|ítems?|requerimientos?)?\s*(?:E\d+[, y]*)+\s*[.)]?$', re.I)
MIN_PALABRAS = {'fortalezas': 25, 'debilidades': 25, 'pendientes': 12, 'contradicciones': 20, 'declarado sin sustento': 15}

def secciones(t):
    out = {}
    for parte in re.split(r'^## ', t, flags=re.M)[1:]:
        titulo, _, cuerpo = parte.partition('\n'); out[titulo.strip().lower()] = cuerpo.strip()
    return out

def main():
    args = sys.argv[1:]
    base = Path(args[args.index('--base') + 1]) if '--base' in args else None
    if base is not None: del args[args.index('--base'):args.index('--base') + 2]
    if not args: sys.exit('Uso: python scripts/11_validar_ficha.py <vendor> [--base carpeta]')
    v = args[0]
    f = (RAIZ / base / v / '10_ficha_T5.md') if base else (RAIZ / 'vendors' / v / 'informes' / '10_ficha_T5.md')
    if not f.exists(): sys.exit(f'No existe {f}')
    t = f.read_text(encoding='utf-8-sig').replace('\r\n', '\n'); secs = secciones(t); errores = []
    for sec in ('lectura general', 'fortalezas', 'debilidades', 'pendientes', 'contradicciones', 'declarado sin sustento', 'resumen por categoría'):
        if sec not in secs: errores.append(f'Falta la sección «{sec}»')
    lg = secs.get('lectura general', '')
    if len(lg.split()) < 80: errores.append(f'Lectura general demasiado corta ({len(lg.split())} palabras; mínimo 80)')
    for sec, minimo in MIN_PALABRAS.items():
        vinetas = [re.sub(r'^\s*[-*]\s+', '', l).strip() for l in secs.get(sec, '').split('\n') if re.match(r'^\s*[-*]\s+', l)]
        if sec in ('fortalezas', 'debilidades') and len(vinetas) < 5: errores.append(f'{sec}: {len(vinetas)} viñetas (mínimo 5)')
        if sec == 'pendientes' and len(vinetas) < 5: errores.append(f'{sec}: {len(vinetas)} viñetas (mínimo 5)')
        for i, vi in enumerate(vinetas, 1):
            texto = re.split(r'\bFuente\s*:', vi, 1)[0]; texto = re.sub(r'\*\*', '', texto)
            etiqueta = f'{sec} #{i}: «{texto[:60].strip()}…»'
            if '…' in vi or '...' in vi: errores.append(f'{etiqueta} contiene puntos suspensivos (texto cortado)')
            if not re.search(r'\bE\d+\b', vi): errores.append(f'{etiqueta} no nombra ningún ítem E<n>')
            if sec != 'pendientes' and 'Fuente' not in vi and 'Requiere la verificación' not in vi: errores.append(f'{etiqueta} no tiene «Fuente:»')
            if sec == 'fortalezas' and 'Confianza' not in vi: errores.append(f'{etiqueta} no tiene «Confianza:»')
            n = len(re.findall(r'\w+', texto))
            if n < minimo and 'Requiere la verificación' not in vi: errores.append(f'{etiqueta} tiene {n} palabras de texto (mínimo {minimo}): no dice qué propone el vendor ni qué observó el evaluador')
            if VACIAS.match(re.sub(r'\s*\(.*?\)\s*', ' ', texto).strip()): errores.append(f'{etiqueta} es una frase vacía («cumple con el criterio…»); describe el contenido')
    filas = [l for l in secs.get('resumen por categoría', '').split('\n') if l.strip().startswith('|') and not l.strip().startswith('|---') and 'Categoría' not in l]
    if len(filas) < 16: errores.append(f'Resumen por categoría: {len(filas)} filas (deben ser las 16 categorías)')
    for l in filas:
        c = [x.strip() for x in l.strip().strip('|').split('|')]
        if len(c) >= 4 and (len(c[2].split()) < 5 or len(c[3].split()) < 3): errores.append(f'Resumen por categoría «{c[0]}»: columnas «Lo que demuestra» / «Lo que falta» demasiado cortas')
    if errores:
        print(f'{f}\nERRORES ({len(errores)}):'); [print(' -', e) for e in errores]; sys.exit(1)
    print(f'{f}\nOK: ficha válida (viñetas sustanciales, con ítem, fuente y confianza; tabla con 16 categorías).')

if __name__ == '__main__':
    main()
