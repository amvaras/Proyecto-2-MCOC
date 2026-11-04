# Proyecto 2 · Grupo 2 · E05

Universidad de los Andes · Métodos Computacionales en Obras Civiles.
**Laboratorio: jueves 29 de octubre de 2026, 10:30–12:30. 3 puntos.**
Batería de verificación térmica 1D/2D/3D, conservación, fuentes, Neumann y Robin.

Caso G2: Freirina/costa de Huasco, referencia Sarco, Atacama.
Coordenadas docentes: **-28.856102, -71.421831**. Las cajas de esta batería
no predicen la fundación ni acreditan sus límites globales 70 °C/20 °C en 14 días.

## Instalación desde la raíz de P2_E05

Entorno comprobado E05: **CPython 3.12.10 / Windows x64**. Se incluyen las 24
versiones fijadas y sus ruedas locales para reconstruir el entorno sin red.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-index --find-links vendor/wheels -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-index --no-build-isolation --no-deps -e '.[dev,plot,bim]'
.\.venv\Scripts\python.exe -m pip check
```

No es necesario activar PowerShell. Dependencias principales: NumPy 2.5.4,
pytest 9.1.1, Matplotlib 3.11.2, IfcOpenShell 0.9.0.post1. Paquete local 0.5.0.
El almacén es para Windows x64 / Python 3.12; no se ha comprobado otro SO.
El solver importa NumPy y biblioteca estándar, sin necesitar Blender.

## Tests y casos configurables

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m pytest -m e05 -q
.\.venv\Scripts\python.exe -m pytest tests -k robin -q
.\.venv\Scripts\python.exe -m pytest tests/test_e05_verification.py --collect-only -q
.\.venv\Scripts\python.exe examples/run_e05.py --list
.\.venv\Scripts\python.exe examples/run_e05.py --all --config configs/e05/lab.json
```

Diez casos: exact_1d, exact_2d, exact_3d, energy, source, neumann, robin,
spatial, temporal y stability. Categorías: exact, conservation, source,
boundary, convergence y stability. Ejemplos con parámetros modificados:

```powershell
.\.venv\Scripts\python.exe examples/run_e05.py --case exact_3d --shape 8 10 12 --lengths 1.2 0.9 1.6 --k 3.1 --rho 2300 --cp 870 --dt 20 --t-end 3600
.\.venv\Scripts\python.exe examples/run_e05.py --case neumann --dim 3 --face z- --flux -135 --lengths 1.3 1.8 0.7
.\.venv\Scripts\python.exe examples/run_e05.py --case robin --dim 3 --h 50 --initial 22 --ambient 40
.\.venv\Scripts\python.exe examples/run_e05.py --case source --dim 1 --q-dot -1200 --rho 2100 --cp 1100
.\.venv\Scripts\python.exe examples/run_e05.py --case spatial --dim 2 --shape 5 7
```

Sin --output, cada corrida obtiene una carpeta nueva con fecha UTC bajo
results/e05. Un destino no vacío se rechaza para preservar resultados.
Cada caso guarda geometría, material, pasos solicitados/efectivos/máximos,
Fourier por eje, checks con error/tolerancia, JSON, datos NPZ y figura cuando
corresponde. El JUnit también registra parámetros científicos de los tests E05.

**Códigos:** 0=PASS; 1=FAIL numérico; 2=entrada rechazada. Un caso estable
puede incumplir precisión; no se oculta ese resultado ni se relaja la tolerancia.

## Verificación integral e independencia

```powershell
.\.venv\Scripts\python.exe -X utf8 -B scripts/verify_e05.py
.\.venv\Scripts\python.exe -X utf8 -B scripts/check_e05_independence.py --output results/e05/independencia_nueva
.\.venv\Scripts\python.exe scripts/check_ifc.py geometry/foundation.ifc
```

El verificador ejecuta toda la suite, las diez demos, variantes de parámetros,
rechazos deliberados e inspección IFC. Exige importar el paquete de esta carpeta.
La prueba de independencia crea otra copia física fuera del proyecto, instala
en un entorno vacío desde las ruedas de esa copia y repite la verificación.
No utiliza entregas anteriores como dependencia de ejecución.

Resultados reales, conteos y matriz:
[E05_ESTADO](docs/E05_ESTADO.md), [E05_AUDITORIA](docs/E05_AUDITORIA.md).
La [guía de laboratorio](docs/E05_DEMO.md) contiene los siete casos mínimos,
parámetros, referencias, tolerancias y respuestas vinculadas al código.

## Formulación y diferencias frente a E04

Se conservan **sin cambios** los dos solvers heredados. El nodal 1D mantiene
medias celdas en extremos; los casos nuevos usan el núcleo cartesiano E04:
centros x_i=(i+1/2)dx, dx=L/n y volúmenes completos en el borde.
Dirichlet prescribe la cara, sin reemplazar el centro. Robin suma las
resistencias dx/(2k) y 1/h. Neumann usa flujo saliente positivo en ambas caras.

La estabilidad aplicada es min(C_i/sum(G_i)), incluyendo bordes, aristas,
esquinas y capacidades locales. Los límites clásicos Fo≤1/2, 1/4 y 1/6
no sustituyen esa cota local. Las referencias sinusoidales son soluciones
de la PDE continua evaluadas en centros. Solo el estudio temporal utiliza
el modo semidiscreto exacto para aislar el error de Euler.

```text
src/mcoc_p2/thermal_nd.py           Solver conservativo heredado, intacto
src/mcoc_p2/diffusion_1d.py         Solver nodal heredado, intacto
src/mcoc_p2/verification_e05.py     Configuración, referencias y checks
tests/test_e05_verification.py     Parámetros, precisión y robustez E05
examples/run_e05.py                CLI, datos y figuras
configs/e05/lab.json               Configuración editable SI
scripts/verify_e05.py              Verificación integral
scripts/check_e05_independence.py  Instalación y prueba externa
vendor/wheels/                    Dependencias locales Windows/Python 3.12
docs/E05_*.md                     Estado, auditoría y guía
geometry/                         Modelo IFC y antecedentes
evidencias/                       Ejecuciones actuales e históricas
```

Se copiaron físicamente 281 archivos útiles de E04. La carpeta coincidía con
su ZIP en código, tests y documentación, y contenía tres resultados adicionales
de una demo. La procedencia e integridad están en docs/E05_BASE_E04_INVENTARIO.json.
El README E04 se preserva en docs/README_HEREDADO_E04.md; informes, resultados,
inventarios y capturas previos permanecen como antecedentes históricos.
Las ocho capturas Bonsai heredadas no se atribuyen a una nueva sesión E05.

No se implementan etapas posteriores: sin clima, hidratación avanzada,
voxelización, activación, radiación ni Monte Carlo. El contacto perfecto entre
materiales se conserva de E04. El IFC todavía está separado de las cajas
ideales de esta batería. Formulación heredada: [E04_FORMULACION](docs/E04_FORMULACION.md).
