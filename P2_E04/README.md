# Proyecto 2 · Grupo 2 · E04

Revisión oral: **28 de octubre de 2026, 10:30–13:20. 4 puntos.**
Solver térmico propio 2D/3D, Dirichlet, Neumann, Robin, fuente volumétrica,
contacto entre dos materiales y BIM del caso base. Canvas pide solamente
repositorio y commit evaluado; no requiere informe.

G2: Freirina/costa de Huasco, referencia Sarco, Atacama.
Coordenadas docentes: **-28.856102, -71.421831**.
Los ejemplos son cajas ideales. No predicen la fundación ni acreditan
cumplimiento de los límites globales 70 °C/20 °C en 14 días.

## Instalación

Entrar en **P2_E04** antes de ejecutar. No es necesario activar el entorno:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-build-isolation --no-deps -e '.[dev,plot,bim]'
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest tests -q
```

E04 se comprobó con Python 3.12.14, Windows x64 y las dependencias fijadas
heredadas. Instalar esta carpeta evita importar el paquete de otra entrega.
Linux/macOS: Python 3.12 y `.venv/bin/python`. Python no necesita Blender abierto.

## Demo para la revisión oral

```powershell
.\.venv\Scripts\python.exe examples/run_e04.py --dim 2 --case sine --n 16
.\.venv\Scripts\python.exe examples/run_e04.py --dim 3 --case sine --n 16
.\.venv\Scripts\python.exe examples/run_e04.py --dim 3 --case robin --h 12
.\.venv\Scripts\python.exe examples/run_e04.py --dim 3 --case source --q-dot 1000
.\.venv\Scripts\python.exe examples/run_e04.py --dim 2 --case flux
.\.venv\Scripts\python.exe examples/run_e04.py --dim 3 --case two-materials
```

Salidas: `summary.json`, `solution.npz` y `temperature.png` bajo
`results/e04/<caso>_<dim>d/`. Para comparar sin sobrescribir, dar una ruta nueva
con `--output`. `--n` indica celdas, dx=1/n. `--dt` y `--t-end` están en segundos.
El paso automático es 0,8 veces la cota local. Un paso excesivo se rechaza con
código 2. Ejemplo deliberadamente inestable:

```powershell
.\.venv\Scripts\python.exe examples/run_e04.py --dim 3 --n 16 --dt 100000
```

La fuente de demo es prescrita, constante y uniforme; no es hidratación.
`two-materials` requiere n par para alinear la interfaz x=0,5 m con una cara.
Las figuras 3D muestran tres cortes ortogonales y la historia de temperaturas.

## Evidencia de la rúbrica

| Criterio | Dónde mostrarlo |
|---|---|
| Balance/discretización (1,2) | `thermal_nd.py`, `E04_FORMULACION.md` |
| Bordes y signos (1,0) | `boundary_heat_rates`, `face_temperature`, tests de caras y esquinas |
| Fuentes/unidades (0,7) | `power`, caso source, balance adiabático |
| Código/estabilidad (0,7) | `capacity/diagonal`, `solve_nd`, convergencia separada |
| BIM (0,4) | `geometry/foundation.ifc`, verificador, vista y capturas heredadas |

Preparación: [guía oral](docs/E04_ORAL.md), [formulación](docs/E04_FORMULACION.md),
[lectura Schmidt](docs/E04_SCHMIDT.md), [estado y resultados](docs/E04_ESTADO.md).

## Verificación integral y BIM

```powershell
.\.venv\Scripts\python.exe scripts/verify_e04.py --output results/e04/nueva_verificacion
.\.venv\Scripts\python.exe scripts/check_ifc.py geometry/foundation.ifc
.\.venv\Scripts\python.exe scripts/render_ifc_preview.py --output results/e04/foundation.png
```

El verificador ejecuta tests heredados/nuevos, convergencia, seis demos,
validación IFC y su vista. Guarda logs, versiones, JUnit y hashes. Exige tests
aprobados sin omisiones y rechaza un destino que ya contiene archivos.
Los resultados de preparación están en `evidencias/e04/`.
Abrir el IFC en Bonsai para mostrar cinco vertidas. Las capturas heredadas son
de E01; las vistas desde Python no se atribuyen a otra sesión de Bonsai.

## Alcance y conservación

El núcleo nuevo usa centros de celda y volumen completo hasta el borde.
Dirichlet fija la cara, sin sobrescribir su celda. El solver nodal 1D heredado
con medias celdas se conserva sin cambios. Se admiten cajas uniformes por eje,
propiedades constantes en tiempo pero variables por celda, contacto perfecto,
fuente prescrita y condiciones constantes por cara.

No hay hidratación, clima real, voxelización IFC, activación de vertidas,
radiación ni Monte Carlo. El BIM y el solver siguen separados.
La raíz conserva E01 y `P2_E02/` conserva E02. E04 hereda físicamente E02;
los estados e inventarios anteriores son históricos. El usuario confirmó que
la demo y defensa E02 ya se realizaron. El README E02 está preservado en
`docs/README_HEREDADO_E02.md`.

Para Canvas obtener el SHA después del commit final con `git rev-parse HEAD`,
publicar la rama y declarar ese mismo SHA. No cambiarlo durante evaluación.
