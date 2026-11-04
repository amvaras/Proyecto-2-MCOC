# MCOC — Proyecto 2 — Grupo 2

Universidad de los Andes, Métodos Computacionales en Obras Civiles.
Planificación de vertidas de hormigón masivo para una fundación de aerogenerador.

Caso G2: Freirina / costa de Huasco, Atacama, Chile; Parque Eólico Sarco como
referencia. Coordenadas docentes: **latitud -28.856102, longitud -71.421831**.
El proyecto general contempla 14 días desde la primera vertida y criterios
Tmax ≤ 70 °C y diferencial térmico ≤ 20 °C.

## Alcance actual: E01

Evaluación: miércoles 21 de octubre de 2026, 10:30–13:20, 3 puntos. Base Python
reproducible, solver propio 1D explícito con Dirichlet/Neumann/Robin, tests,
benchmark exacto e IFC4 preliminar de cinco vertidas. El ejemplo numérico no
predice la temperatura real de Sarco ni demuestra cumplimiento de sus límites.

El IFC fue generado con Python/IfcOpenShell y verificado automáticamente.
Su apertura y revisión humana en **Blender 5.1.2 / Bonsai v0.9.0-post1** están
documentadas mediante ocho capturas en `Evidencias/bonsai/`, inspeccionadas
durante la auditoría. Se distinguió esta evidencia de la validación automatizada.
La auditoría técnica E01 concluyó **COMPLETO**: 67 tests aprobados, benchmark
reproducido y cinco volúmenes IFC comprobados. Consultar el
[informe de auditoría](docs/AUDITORIA_TECNICA_E01.md),
[estado técnico](docs/E01_ESTADO.md) y [evidencias](docs/E01_EVIDENCIAS.md).

## Instalación en Windows PowerShell

Entorno comprobado: **CPython 3.12.10, Windows x64**. Se selecciona Python 3.12
para usar la rueda de IfcOpenShell efectivamente instalada y probada. No se ha
verificado Python 3.14. `requirements-lock.txt` fija dependencias transitivas
comprobadas; `pyproject.toml` separa núcleo NumPy de extras de tests, dibujo y BIM.

Desde la raíz de esta carpeta:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-build-isolation --no-deps -e '.[dev,plot,bim]'
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe examples/run_diffusion_1d.py
.\.venv\Scripts\python.exe scripts/check_ifc.py geometry/foundation.ifc
```

No hace falta activar el entorno ni cambiar la política de ejecución de
PowerShell. Si se activa con `.\.venv\Scripts\Activate.ps1`, se puede usar
`python` en lugar de la ruta al ejecutable. Las instrucciones posteriores usan
esta abreviatura; en caso de duda mantener la ruta explícita de arriba.

## Ejecutar

```powershell
python -m pytest -q
python examples/run_diffusion_1d.py --output results
python scripts/check_ifc.py geometry/foundation.ifc --json results/ifc_check.json
```

El ejemplo guarda `results/diffusion_1d.png`, datos NPZ y parámetros/error JSON.
Superpone la solución exacta final y muestra perfiles desde t=0 a 24 h e historia
del centro y extremos. Usa L=1 m, 81 nodos, k=2 W/(m K), rho=2400 kg/m³,
cp=900 J/(kg K), T inicial=20+10 sin(pi x/L), extremos a 20 °C y fuente nula.
Son parámetros ilustrativos, sin calibración del material real.

El benchmark ejecutado dio dt=67,5 s, 1280 pasos, Fo=0,4 y error máximo
0,000645135652 °C. La auditoría volvió a ejecutar **67 tests**, sin fallos ni
omisiones, en un tercer entorno vacío. Las 24 versiones fijadas coincidieron
con el archivo de dependencias. Se verificaron por separado segundo orden
espacial y primer orden temporal. Registros actuales: `docs/evidencias/auditoria/`.

La API `mcoc_p2.solve` admite condición inicial y fuente como escalar o vector,
fuente constante y fronteras constantes. `Neumann` usa flujo **saliente positivo**
en ambos extremos; Robin usa `q_out=h*(T_surface-T_ambient)`.
La derivación, energía con medias celdas y cota Robin están en
[formulación 1D](docs/FORMULACION_1D.md).

## BIM e independencia del solver

Flujo del proyecto: Blender (herramientas 3D) → Bonsai (autoría BIM) → IFC
(geometría, identidad y propiedades) → IfcOpenShell (lectura Python) → futuro
discretizador → solver. Actualmente el benchmark 1D y el IFC son componentes
separados; aún no se realiza la conexión geométrica al cálculo térmico.
El solver solo importa NumPy y biblioteca estándar; no necesita Blender abierto.

`foundation.ifc` contiene cinco IfcFooting en metros y coordenadas locales.
Planta octagonal de 18 m entre caras, borde de 1,10 m, altura central de 3,30 m
y pedestal cilíndrico de diámetro 7 m y altura 1 m. La transición está dividida
en dos troncos octagonales, según la guía. Detalles e instrucciones de apertura
en [IFC y Bonsai](docs/IFC_BONSAI.md).

## Estructura

```text
src/mcoc_p2/diffusion_1d.py      Materiales, fronteras, integración y energía
tests/                         Balances, soluciones exactas, estabilidad e IFC
examples/run_diffusion_1d.py    Demostración reproducible con figura y datos
geometry/foundation.ifc        Fuente principal BIM, cinco vertidas
scripts/create_preliminary_ifc.py / check_ifc.py
scripts/check_diffusion_accuracy.py   Error espacial/temporal y coherencia del NPZ
scripts/check_bonsai_evidence.py      Integridad de capturas inspeccionadas y datos IFC
scripts/verify_e01.py           Verificación técnica integral y conservación de historial
docs/FORMULACION_1D.md          Balance, discretización y estabilidad
docs/IFC_BONSAI.md              Procedencia y revisión humana del modelo
docs/E01_ESTADO.md / E01_EVIDENCIAS.md / FUENTES.md
docs/AUDITORIA_TECNICA_E01.md    Hallazgos, correcciones y matriz de cumplimiento
docs/evidencias/auditoria/      Salidas actuales, parámetros, figuras y resultados JUnit
docs/historico/                 Copia preservada del estado anterior a la auditoría
Evidencias/bonsai/              Ocho capturas humanas y registro de su inspección
requirements-lock.txt          Versiones comprobadas en Python 3.12 / Windows
```

Se agregaron formulación, procedencia de fuentes y evidencias separadas para
facilitar la trazabilidad. `results/` contiene salidas de trabajo y los entornos
virtuales son locales. Para refrescar los registros de forma explícita:

```powershell
python scripts/verify_e01.py
# Guardar una comprobación independiente en otra carpeta:
python scripts/verify_e01.py --output results/verificacion_independiente
```

## Límites y siguientes etapas

Se soporta únicamente un dominio 1D uniforme, material constante y fronteras y
fuentes prescritas constantes. No hay clima, hidratación avanzada, activación
de vertidas, suelo, voxelización, solver 2D/3D, Monte Carlo, HPC ni optimización.
Tampoco se validó el material frente a mediciones. Estas funciones pertenecen
a etapas E02–E15 y se mencionan como contexto, sin implementarlas aquí.

Los documentos docentes consultados y ausentes están en [fuentes](docs/FUENTES.md).
El alcance técnico obligatorio de E01 está cubierto; las funciones de etapas
posteriores descritas arriba no son pendientes de esta entrega.
