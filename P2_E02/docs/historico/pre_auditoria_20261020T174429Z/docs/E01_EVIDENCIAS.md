# Evidencias de ejecución E01

Fecha de revisión: 20 de octubre de 2026 (America/Santiago). Los instantes UTC
exactos de la corrida automatizada se guardan en `evidencias/verification.json`.
Este registro describe el árbol local preparado, no un commit nuevo publicado.

## Entorno y dependencias

Windows AMD64, CPython **3.12.10**. Versiones comprobadas:

| Dependencia | Versión |
|---|---|
| NumPy | 2.5.4 |
| Matplotlib | 3.11.2 |
| pytest | 9.1.1 |
| IfcOpenShell | 0.9.0.post1 |

Dependencias transitivas y herramientas de instalación: `requirements-lock.txt`.
IfcOpenShell se instaló con rueda `py312-none-win_amd64` y se ejecutó su motor de
geometría y validación EXPRESS. No se dedujo compatibilidad solo de un número de versión.

## Comandos efectivamente ejecutados

En la raíz del clon, con la ruta explícita al Python del entorno cuando no
estaba activado. Se abrevian las rutas de entornos como `.venv` y `.venv-repro`:

```powershell
git clone https://github.com/amvaras/Proyecto-2-MCOC.git Proyecto-2-MCOC
git status --short --branch
git branch -a
git ls-remote --heads origin
git log -3 --oneline
git switch -c e01/base-termica-ifc
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install numpy matplotlib pytest ifcopenshell setuptools wheel
.\.venv\Scripts\python.exe -m pip install --no-build-isolation -e '.[dev,plot,bim]'
.\.venv\Scripts\python.exe -m pytest tests/test_diffusion_1d.py -q
.\.venv\Scripts\python.exe scripts/create_preliminary_ifc.py
.\.venv\Scripts\python.exe scripts/check_ifc.py --json results/ifc_check.json
.\.venv\Scripts\python.exe examples/run_diffusion_1d.py
.\.venv\Scripts\python.exe scripts/verify_e01.py
py -3.12 -m venv .venv-repro
.\.venv-repro\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv-repro\Scripts\python.exe -m pip install --no-build-isolation --no-deps -e '.[dev,plot,bim]'
.\.venv-repro\Scripts\python.exe -m pip check
.\.venv-repro\Scripts\python.exe -m pytest -q
.\.venv-repro\Scripts\python.exe examples/run_diffusion_1d.py --output results/repro
git diff --check
git status --short --branch
```

El archivo de versiones fijadas se generó desde las distribuciones realmente
instaladas, excluyendo la ruta editable del propio proyecto. La segunda
instalación utilizó ese archivo y repitió los tests y el ejemplo con éxito.
`.venv-repro` es un entorno local limpio, no una prueba en otro computador o SO.

## Tests y solver

- Primera corrida térmica: **52 passed in 0.46s**.
- Corrida completa inicial con IFC: **54 passed in 6.31s**.
- Segundo entorno instalado desde versiones fijadas: **54 passed in 6.68s**,
  más `No broken requirements found.` y mismo error del benchmark.
- Última corrida completa: ver salida literal en `evidencias/pytest.txt`;
  `verify_e01.py` aborta si cualquier comprobación devuelve error.
- No hubo fallos de pytest en las corridas efectuadas. Sí se corrigieron
  artefactos del render de la vista previa, inspeccionando la figura resultante.

Pruebas físicas: perfil uniforme invariable; Dirichlet impuestos; energía de
perfil no uniforme adiabático; fuente uniforme y espacial; flujo Neumann
positivo/negativo en ambas caras; Robin con balance por paso, h=0 y estado
lineal; rechazo de dt excesivo; validación de parámetros; modos exactos seno
y Robin con reducción de error al refinar. No son solo tests de existencia.

Benchmark ejecutado: L=1 m, nx=81, dx=0,0125 m, alpha=9,259259259e-7 m²/s,
dt=67,5 s, **1280 pasos**, **86400 s**, **Fo=0,4**. Dirichlet 20 °C en ambos
extremos, fuente nula, T inicial=20+10 sin(pi x/L). Error final L∞:
**0,0006451356521708362 °C**. Ver `evidencias/diffusion_1d.json`,
`diffusion_1d.npz` y `diffusion_1d.png`. No es una predicción del caso G2 real.

## IFC

Archivo: `geometry/foundation.ifc`, esquema IFC4, metros, cinco elementos
IfcFooting llamados Vertida_01–Vertida_05, GUID únicos reproducibles, material
preliminar y jerarquía espacial. Validación de esquema/EXPRESS: **0 incidencias**.
Bounding box global: **(-9; -9; 0) a (9; 9; 4,30) m**, a redondeo numérico.

| Vertida | z [m] | Volumen analítico [m³] |
|---|---|---:|
| 01 | 0–0,55 | 147,625714 |
| 02 | 0,55–1,10 | 147,625714 |
| 03 | 1,10–2,20 | 214,224351 |
| 04 | 2,20–3,30 | 88,924748 |
| 05 | 3,30–4,30 | 38,484510 |

El volumen teselado del pedestal es 38,477191 m³: diferencia de aproximadamente
0,019 % por aproximar el círculo con triángulos. El perfil IFC conserva radio
exacto 3,5 m. El verificador exige volumen positivo, coincidencia con fórmula
analítica a 0,05 %, bounding boxes, cotas y malla cerrada por incidencias de arista.
Ver salida completa y GUID en `evidencias/ifc_check.json`.

Se generaron e inspeccionaron vistas desde la geometría leída mediante
IfcOpenShell (`evidencias/foundation_preview.png`). **Blender/Bonsai: versiones
no verificadas, sin sesión de interfaz ejecutada, sin capturas atribuidas a Bonsai.**
No se halló Blender en PATH ni en las carpetas habituales revisadas. No se
afirma una búsqueda exhaustiva en todos los discos. Procedencia e instrucciones
humanas: `docs/IFC_BONSAI.md`.

## Git y permisos

- Repositorio oficial: https://github.com/amvaras/Proyecto-2-MCOC.
- Rama remota observada: únicamente `main`.
- HEAD local de base y SHA remoto observado de `main`:
  `206804ada592c09c17e8e30ab77d39e63da11c0b` (`Initial commit`).
- Rama de trabajo local: `e01/base-termica-ifc`.
- Ese HEAD contiene solo el README inicial. **No identifica la implementación E01.**
- Estado preparado: README modificado y archivos nuevos de código, tests,
  geometría, entorno, documentación y evidencias. No se crearon commits, no se
  hizo push, no se abrió PR y no se alteró historia compartida.
- Conector GitHub: cuenta `MinuteRogue12`, `pull=true`, `push=false`.
- Credencial HTTPS de Git local: cuenta `javimosqueira`; consulta autenticada
  de la API oficial confirmó también `pull=true`, `push=false`, `admin=false`.
- La API devolvió `protected=false` para main; esto no otorga permiso de escritura.
- La identidad de autor configurada en Git es distinta del permiso remoto;
  tener `user.name` y `user.email` no permite publicar.

La consulta de permisos mantuvo la credencial solo en memoria y no se guardó
ni mostró su secreto. Falta autorización explícita para crear el nuevo commit,
y falta permiso o vía de revisión mediante fork para publicarlo. El enlace de
Canvas queda pendiente hasta verificar un nuevo SHA remoto real.

## Pasos de publicación pendientes

Estos comandos son instrucciones para después de la autorización explícita;
no son acciones ya realizadas. Ejecutarlos desde la raíz del clon, revisando
previamente todos los archivos incluidos:

```powershell
git diff --check
.\.venv\Scripts\python.exe scripts/verify_e01.py
git status --short --branch
git add README.md .gitignore .gitattributes pyproject.toml requirements-lock.txt src tests examples geometry scripts docs
git diff --cached --stat
git commit -m "E01: base reproducible BIM IFC y solver termico 1D"
git rev-parse HEAD
# Solo tras autorización de publicación y permiso de escritura otorgado:
git push -u origin e01/base-termica-ifc
git ls-remote --heads origin e01/base-termica-ifc
```

Comparar el SHA completo de `git rev-parse HEAD` con el de `git ls-remote` y
verificar el commit en GitHub. Luego abrir PR hacia main para revisión, sin
force push. Si no se otorga escritura, la propietaria puede recibir el trabajo
o revisar un PR desde un fork autorizado; no cambiar el remote actual sin
documentar esa elección.

Para Canvas, después de verificar la publicación:

```text
Repositorio: https://github.com/amvaras/Proyecto-2-MCOC
Commit evaluado: pegar aquí la URL real del nuevo commit publicado
```

Nota opcional (menos de 100 palabras, adaptar al estado de ese momento):
«Base E01 con solver 1D explícito, condiciones Dirichlet/Neumann/Robin,
tests físicos y analíticos, y modelo IFC4 de cinco vertidas verificado mediante
IfcOpenShell. La revisión visual e interacción desde Bonsai están pendientes.
El ejemplo es un benchmark numérico; todavía no representa la fundación real,
el clima ni la hidratación. Los límites térmicos del caso final no se evalúan aquí».
