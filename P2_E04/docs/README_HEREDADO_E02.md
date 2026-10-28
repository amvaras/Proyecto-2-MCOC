# Proyecto 2 — G2 — E02: round-trip IFC y demo 1D

Entrega del 22 de octubre de 2026, 10:30–12:30 (Santiago). Esta carpeta incluye
la base técnica completa de E01 disponible en Git, sus evidencias e historial,
y las herramientas E02. Puede copiarse fuera del repositorio y ejecutarse sola.
**Estado: software verificado; edición real en Bonsai y defensa oral PENDIENTES.**

Todos los comandos siguientes parten de esta carpeta, no de la raíz E01.
No se necesita Blender para ejecutar Python. Para el round-trip humano sí se
necesita Blender con Bonsai en el computador del estudiante.

## Instalación

PowerShell (Python 3.12):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-build-isolation --no-deps -e '.[dev,plot,bim]'
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
```

Linux: `python3.12 -m venv .venv`; sustituir el ejecutable de los comandos por
`.venv/bin/python`. No copiar entornos virtuales entre máquinas.

## Demo parametrizable

```powershell
.\.venv\Scripts\python.exe examples/run_e02_1d.py --nx 81 --dt 67.5 --output results/e02/base
.\.venv\Scripts\python.exe examples/run_e02_1d.py --nx 81 --dt 33.75 --output results/e02/temporal
.\.venv\Scripts\python.exe examples/run_e02_1d.py --nx 41 --dt 1 --output results/e02/espacial41
.\.venv\Scripts\python.exe examples/run_e02_1d.py --nx 81 --dt 1 --output results/e02/espacial81
```

`--t-end` permite variar el tiempo final en segundos. Salidas: resumen JSON y
NPZ con posiciones, tiempos, temperaturas y solución exacta. El ejemplo E01
`examples/run_diffusion_1d.py --output results/e01_demo` conserva su figura.
La barra ideal y el IFC siguen siendo componentes separados.

## IFC y demostración Bonsai

```powershell
.\.venv\Scripts\python.exe scripts/check_ifc.py geometry/foundation.ifc
.\.venv\Scripts\python.exe scripts/compare_ifc_e02.py geometry/foundation.ifc geometry/e02/foundation_trabajo.ifc
# Solo después de guardar la edición humana:
.\.venv\Scripts\python.exe scripts/compare_ifc_e02.py geometry/foundation.ifc geometry/e02/foundation_bonsai_e02.ifc --require-change --json evidencias/e02/roundtrip_real.json
```

La copia de trabajo inicialmente no tiene diferencias. No se entrega un IFC
falsamente atribuido a Bonsai. Sigue [la guía](docs/E02_DEMO.md) para editarlo.
El comparador detecta propiedades/atributos, altas y bajas por GUID, y excluye
IDs STEP e historial administrativo. **No compara sólidos ni certifica autoría.**
Su alcance corresponde a la edición recomendada de la propiedad Estado.
Exit codes: 0 comparación correcta; 1 sin diferencias con `--require-change`;
2 error de lectura, escritura o argumentos.

## Verificación y documentos

```powershell
.\.venv\Scripts\python.exe scripts/verify_e01.py --output results/e02/verificacion
```

No ejecutar el verificador sin `--output`: su destino heredado son registros
históricos. El inventario heredado y `VERIFICAR_INTEGRIDAD_E01.py` describen el
respaldo local E01, no esta entrega ampliada; no son el verificador de E02.

- [Base y archivos disponibles](docs/BASE_HEREDADA_E01.md).
- [Guía de demo y defensa](docs/E02_DEMO.md).
- [Estado](docs/E02_ESTADO.md) y [auditoría](docs/E02_AUDITORIA.md).
- [README original preservado](docs/README_HEREDADO_E01.md).

Política acumulativa: raíz = E01; P2_E02 = E01 + E02; futuras P2_E03/P2_E04
incluirán la entrega anterior y sus extensiones dentro de su propia carpeta.
Se prefieren copias físicas a dependencias entre entregas. Nunca usar symlinks,
rutas absolutas ni imports hacia otra entrega. Dependencias externas de Python
se reconstruyen con los archivos declarados.
