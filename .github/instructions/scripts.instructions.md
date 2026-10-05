---
applyTo: "scripts/*.py"
---
Scripts del pipeline multi-vendor. Todos reciben el vendor como primer argumento y usan scripts/_comun.py para
resolver vendors/<vendor>/. Se ejecutan con el Python del proyecto (.venv). No cambian la estructura de salida
(marcadores ===== PAGE/SHEET/SLIDE =====, formato [E<n>] de la matriz, tabla del consolidado) sin actualizar
.github/copilot-instructions.md y los agentes que la leen.
