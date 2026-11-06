# E09 — Baseline 3D con hidratación · Grupo 2

Fundación IFC del curso, cinco vertidas y 14 días de temperatura calculada.
El SHA evaluado corresponde a la [etiqueta entrega-e09](https://github.com/amvaras/Proyecto-2-MCOC/commit/entrega-e09).

## Abrir los resultados

```powershell
Invoke-Item .\docs\E09_DOSSIER.md
Invoke-Item .\figures\e09_evolucion_espacial.png
Invoke-Item .\figures\e09_evolucion.gif
```

[Dossier](docs/E09_DOSSIER.md) · [Lámina 3D](figures/e09_evolucion_espacial.png) ·
[Máximas](figures/e09_tmax.png) · [Sondas](figures/e09_sondas.png) ·
[Resumen](results/e09_baseline/summary.json).

## Instalar y probar

Windows x64, Python 3.12 e Internet para descargar el lock desde PyPI.
No utiliza otra entrega. El entorno se recrea y no se versiona.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -X utf8 -B -m pytest tests -q -p no:cacheprovider
```

Pytest usa temporales propios dentro de E09. El instalador fija TMP corto
dentro de la entrega para evitar problemas de longitud de rutas de Windows.

## Ejecutar y reproducir

En una instalación nueva sin resultados: `python examples/run_e09.py`.
El destino oficial ya está calculado; se rechaza sobrescribir datos.
Para repetir el cálculo conservando el entregado:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B examples/run_e09.py --output results/e09_repeticion --figures-dir .runtime/figuras_repeticion
```

Regenerar figuras y dossier no requiere resolver otra vez:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B scripts/plot_e09.py --result results/e09_baseline --figures-dir figures
.\.venv\Scripts\python.exe -X utf8 -B scripts/build_e09_dossier.py
.\.venv\Scripts\python.exe -X utf8 -B scripts/check_e09_dossier.py --json results/verification/dossier.json
.\.venv\Scripts\python.exe -X utf8 -B scripts/verify_e09.py
.\.venv\Scripts\python.exe -X utf8 -B scripts/check_e09_time.py
.\.venv\Scripts\python.exe -X utf8 -B scripts/reproduce_e09.py
.\.venv\Scripts\python.exe -X utf8 -B scripts/check_ifc.py geometry/foundation.ifc
```

El límite de 1.200 palabras cuenta todo el texto visible, incluidas tablas,
código, ecuaciones y pies. Los enlaces cuentan por su etiqueta.

## Cambiar hipótesis

```powershell
.\.venv\Scripts\python.exe -X utf8 -B examples/run_e09.py --spacing 0.55 0.55 0.275 --hours 96 --h 12 --ambient 15 --placement-offset 2 --heat-mj-m3 45 --activation-interval-hours 3 --no-animation --output results/variante --figures-dir .runtime/variante_figuras
```

configs/e09/baseline.json separa physics y analysis. El primer bloque define
material, eventos, hidratación y fronteras; el segundo solo controla cortes,
tiempos y animación. Las variantes permanecen locales. No se ajustan parámetros
para obtener 73 °C. --help enumera los argumentos.

## Artefactos y alcance

- grid.npz: etiquetas, ocupación, origen, pasos, ejes e índices.
- temperature.npz: campos por frame y máscara activa; ceros fuera de máscara
  son relleno, no hormigón frío.
- statistics.npz: máxima/mínima/media y nueve sondas en cada paso, con validez.
- steps.npz: pasos, cotas, hidratación, salida, colocación y residuos.
- control.npz: estadísticas del mismo caso sin hidratación.
- summary.json, inputs.json y figure_manifest.json: parámetros, balances, GUID,
  volúmenes por pieza y vínculo verificable entre figuras y campo.

Se reutiliza e08/solver.py con un observador de solo lectura. e09/ añade
instrumentación, artefactos y figuras; no duplica el integrador.
Las herramientas heredadas sostienen pruebas y funciones vigentes, sin copiar
resultados ni documentación histórica. web/ conserva la interfaz opcional E08
y sus pruebas; el dossier E09 utiliza el CLI y figuras estáticas.

Base adiabática, ambiente y propiedades constantes y contacto perfecto;
sin suelo explícito, Arrhenius, calibración ni predicción de fisuras.
Las temperaturas de cara Robin se reconstruyen desde media celda.
Conservación y estabilidad no equivalen a validación experimental.

[Auditoría y rúbrica](docs/E09_AUDITORIA.md) · [Fuentes](docs/E09_FUENTES.json) ·
[Selección de base](docs/E09_BASE_SELECCIONADA.json).
El [inventario de la entrega](docs/E09_ARCHIVOS_A_VERSIONAR.txt) enumera los archivos publicados.
