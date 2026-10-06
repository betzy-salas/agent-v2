# Verificación técnica RFP core bancario — versión para GitHub Copilot

Esta carpeta contiene todo lo construido con Claude Code traducido al formato de GitHub Copilot
(VS Code y Copilot coding agent). Las reglas, los 14 agentes y el flujo son los mismos; cambia solo
el envoltorio. Los scripts Python de `scripts/` se usan tal cual.

## Qué hay

La carpeta es autocontenida: es un repositorio listo para abrir en VS Code con Copilot.

```
copilot/
├── README.md, EJECUCION.md           ← esta guía y el guion paso a paso por vendor
├── requirements.txt, .gitignore
├── scripts/                          ← los 10 scripts del pipeline (00 … 06, 02b rúbrica de implementación, _comun.py)
├── vendors/                          ← vacía; cada vendor se crea con scripts/00_nuevo_vendor.py
└── .github/
    ├── copilot-instructions.md        ← reglas comunes (equivale a CLAUDE.md); Copilot lo lee solo
    ├── agents/                        ← 18 agentes personalizados (*.agent.md)
    │   ├── verificador-t1-arquitectura … verificador-t8-soporte
    │   ├── redactor-diagnostico, redactor-ejecutivo, redactor-ejecutivo-t5,
    │   │   redactor-pros-contras, redactor-fortalezas-debilidades
    │   ├── verificador-implementacion (rúbrica corporativa 0–5), redactor-implementacion, analista-despliegue y comparador-implementacion (comparativos)
    │   └── revisor-cruzado
    ├── prompts/                       ← prompts reutilizables con parámetros (*.prompt.md), se invocan con /nombre
    │   ├── verificar-t1 … verificar-t8 (T6 → verificar-t6-bloque + unir-t6)
    │   ├── verificar-implementacion (rúbrica EI/F/I), implementacion (resumen pros y contras)
    │   ├── despliegue (modelos SaaS/PaaS y nubes por vendor, comparativo), comparar-implementacion (comparativo)
    │   ├── validar, consolidar, top-diferencias
    │   ├── informe-diagnostico, resumen-ejecutivo, pros-contras, informe-ejecutivo-t5, fortalezas-debilidades
    │   └── revision-cruzada, corregir-informes
    └── instructions/                  ← reglas por ruta (*.instructions.md): verif/, informes/, scripts/
```

## Instalación

1. Copia la carpeta `copilot/` completa donde vaya a vivir el repositorio y ábrela en VS Code como raíz del
   espacio de trabajo (Copilot busca `.github/` en la raíz). Si la integras en un repositorio que ya tiene
   `.github/`, copia dentro solo `copilot-instructions.md`, `agents/`, `prompts/` e `instructions/`.
   Crea el entorno: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
2. En VS Code, activa en la configuración de Copilot: `chat.promptFiles` (prompts), `chat.agentFilesLocations`
   o el equivalente de agentes personalizados, y `github.copilot.chat.codeGeneration.useInstructionFiles`.
   Los nombres exactos cambian entre versiones; en los ajustes busca «prompt files», «custom agents» e
   «instruction files».
3. Abre Copilot Chat en modo **Agent** y comprueba que en el selector de agentes aparecen los 14 y que al
   escribir `/` se ofrecen los prompts.
4. Los vendors ya verificados con Claude Code (por ejemplo `vendors/sunline/`) se pueden copiar tal cual a `vendors/`; los formatos son idénticos.

## Instalación en Windows (entorno corporativo)

En Windows el lanzador es `py` y el entorno se activa de otra forma. Desde la carpeta del repositorio, en PowerShell:
```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python scripts\04_ingesta.py <vendor>
```
Llamar al intérprete por su ruta (`.venv\Scripts\python`) evita depender de qué Python abre `py`. Para activar el
entorno y escribir solo `python`: `.venv\Scripts\Activate.ps1` (si PowerShell lo bloquea, ejecutar una vez
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, o usar `.venv\Scripts\activate.bat` desde cmd).
Detrás de un proxy corporativo: añadir `--proxy http://usuario:clave@proxy:puerto` al `pip install`, o usar el índice
interno de paquetes que indique TI. Las rutas de los scripts aceptan `/` o `\` indistintamente.

## Uso por vendor

Terminal:
```bash
python scripts/00_nuevo_vendor.py <vendor>
# copiar la propuesta, la matriz del Banco y los anexos a vendors/<vendor>/docs/raw
python scripts/04_ingesta.py <vendor>
```
Revisar `vendors/<vendor>/NOMBRES.md` y el `.toc.md` de la propuesta.

Copilot Chat (modo Agent), una hoja por conversación:
```
/verificar-t1          → pide el vendor
/verificar-t2 … /verificar-t5, /verificar-t7, /verificar-t8
/verificar-t6-bloque   → pide vendor y bloque (1, 2, 3); tres conversaciones
/unir-t6               → une los tres parciales en verif/T6.md
/verificar-implementacion → puntúa la rúbrica corporativa de implementación (necesita matriz/IMPL.txt, lo genera la ingesta)
/implementacion        → pros y contras de la propuesta de implementación (usa IMPL.md si existe)
/validar               → ejecuta scripts/06_validar_verif.py <vendor> (formato, conteos y citas de cada hoja)
/consolidar            → ejecuta scripts/03_consolidar.py <vendor>
/top-diferencias       → los 20 ítems con mayor diferencia, para la revisión manual
/informe-diagnostico, /resumen-ejecutivo, /pros-contras, /informe-ejecutivo-t5, /fortalezas-debilidades
/revision-cruzada
/corregir-informes     → aplica las correcciones de la revisión a un informe
```
Después de todos los vendors: `python scripts/05_comparar.py` y, para los comparativos, `/despliegue` (modelos y nubes) y `/comparar-implementacion` (implementaciones).

También se puede elegir el agente en el selector y escribir la orden a mano: «verifica T3 del vendor acme».
En el Copilot coding agent de GitHub.com se asigna un issue al agente con el mismo texto.

## Diferencias respecto a la versión de Claude Code

| Claude Code | GitHub Copilot |
|---|---|
| `CLAUDE.md` | `.github/copilot-instructions.md` |
| `.claude/agents/*.md` con `tools: Read, Grep, Glob, Write` | `.github/agents/*.agent.md` con `tools: ['codebase', 'search', 'editFiles', …]` |
| `model: opus` por agente | El modelo lo elige el usuario en Copilot; usar el más capaz disponible para los verificadores |
| Varios agentes en paralelo desde un chat | Una conversación por hoja; T6 en tres conversaciones + `/unir-t6` |
| Hook `SubagentStop` con notificación de macOS | No existe; cada conversación termina con el resumen en el chat |
| El orquestador valida formato, conteos y citas tras cada agente | Ejecutar `/validar` (scripts/06_validar_verif.py) después de cada hoja |
| Memoria entre sesiones | No hay; todo el contexto está en `copilot-instructions.md`, `NOMBRES.md` e `INVENTARIO.md` |

## Mantenimiento

`CLAUDE.md` y `copilot-instructions.md` deben decir lo mismo. Si se cambia una regla en uno, copiarla al otro.
Los agentes de `copilot/.github/agents/` se generaron a partir de `.claude/agents/` sustituyendo rutas y
herramientas; si se edita un agente en un lado, replicar el cambio en el otro.
