# Reproducción de F01

## Versiones de referencia

| Componente | Rama publicada | SHA |
|---|---|---|
| Geometría y etapas | `codex/e07` | `269d389a8f60ce8ab346110e2ca24a1926b8bb62` |
| Integrador de vertidas | `codex/e08` | `19dae6f307ef8e669d13a18ddf8e9ce28e95a953` |
| Hidratación y baseline | `codex/e09` | `156eccb34c736888b699b0bfeac3b0fc3ba412d5` |
| Envolvente y fronteras | `codex/e10` | `a8e742696b68b4bb7090c114409ee8addc931195` |
| Meteorología y colocación | `codex/e11` | `9be8b923f6e25a040ddf85815f3981a9cf70f22d` |
| Métricas y geometría | `codex/e12` | `509ab715c6da1e937e282ec836c3c6756752205a` |
| Escenarios y riesgo | `codex/e13` | `9fc62cd4d5d0a4ee36810827add3ceb9e00f6527` |
| Ocho planes, 192 casos nominales y banco MC | `codex/e14` | `f9d2faa150f9fdda007679386568326497f0d239` |
| Recomendación provisional, resultados e IC | `codex/e15` | `0bb141827d24f7bed24137fad86119998f10e743` |
| Exportación de defensa con refrigeración y visor | `codex/f02-zip-export` | `969c8141f3daf4b9e6c7778f29bfe34d937e9fe5` |

La rama F01 se basa en la exportación F02. Los archivos nuevos están bajo `P2_F01/`. La procedencia histórica de E15 se conserva en su rama, con enlace en el artículo. En F01 se añadieron una síntesis académica, tablas derivadas, visualizaciones de los registros y sensibilidades algebraicas. Las métricas, pesos, datos, kernel, recomendación nominal y archivos de defensa se conservan.

## Compilar el artículo

Desde `P2_F01`, con pdfTeX/TeX Live y los paquetes declarados en `articulo.tex`:

```bash
pdflatex -interaction=nonstopmode -halt-on-error -jobname=F01_Articulo_Academico_Final articulo.tex
pdflatex -interaction=nonstopmode -halt-on-error -jobname=F01_Articulo_Academico_Final articulo.tex
```

La bibliografía está directamente en el fuente. Todas las figuras necesarias para compilar están incluidas. Las vistas IFC y el gráfico meteorológico son renderizados archivados, de `geometry/foundation.ifc` y las tres instantáneas identificadas en `data/ensemble/reduction.json`.

Desde `P2_F01`, para regenerar gráficas y CSV derivados con Python, NumPy y Matplotlib:

```bash
python generar_figuras.py ../P2_E14
```

Los resultados derivados se basan en `results/f02/{planes.csv,enumeration.json,fields.npz}`, `results/e14/{official.json,enumeration/,monte_carlo/summary.json}` y `data/hydration/source_terms.txt`. La imagen de campo y los cortes toman el instante crítico almacenado de M4 SS, m17. El script usa los estados originales. Los cambios de versión pueden alterar el render y los metadatos del PDF.

## Reproducir y verificar resultados físicos

Desde una copia de la exportación F02, fijar el commit de defensa y entrar en `P2_E14`:

```bash
git switch --detach 969c8141f3daf4b9e6c7778f29bfe34d937e9fe5
cd P2_E14
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m pip install --no-build-isolation --no-deps -e '.[dev,plot,bim,viz]'
python -m pip check
python scripts/run_f02.py --workers 4 --output results/f02_repro
python scripts/run_f02.py --workers 3 --controls --output results/f02_repro
python scripts/verify_f02.py --output results/f02_repro
mkdir -p .runtime
python -m pytest -q -p no:cacheprovider --basetemp .runtime/pytest-f02 tests
python web/servidor.py --port 8714
```

Abrir `http://127.0.0.1:8714/` para consultar la evidencia integrada que acompaña al visor. El comando de simulación usa las historias y fuentes archivadas. La salida de la repetición queda separada del directorio oficial. En Windows, usar `.venv\Scripts\python.exe` conforme a la guía E14.

Para reproducir la verificación del archivo sellado de E14, cambiar primero al SHA E14 en otra copia. Desde su carpeta `P2_E14`, instalar las dependencias indicadas en su README y ejecutar `python scripts/verify_e14_offline.py`. El comando comprueba los resultados guardados sin red ni integración. La configuración `configs/e14/study.json` fija 10.000 realizaciones por plan y semilla maestra 20261119. El banco, resúmenes, intervalos y manifiesto están en `results/e14/monte_carlo/`. La guía detallada es `docs/E14_REPRODUCCION_OFFLINE.md`. El flujo en clúster real quedó pendiente.

| Evidencia | Ruta en `P2_E14/` |
|---|---|
| IFC y fuente de calor | `geometry/foundation.ifc`, `data/hydration/source_terms.txt` |
| Ensamble archivado, metadatos, reducción y series | `data/ensemble/`, `data/weather/` |
| Programas comparados y parámetros de enfriamiento | `configs/e14/study.json`, `configs/f02/moderate_20.json` |
| Ensayos de difusión, activación, S25 y tubos | `tests/test_diffusion_1d.py`, `tests/test_e08_solver.py`, `tests/test_e12.py`, `tests/test_f02.py` |
| Verificación numérica E14, pruebas y entorno | `results/verification/numerics_e14.json`, `results/verification/junit.xml`, `results/verification/environment.json` |
| Casos F02, auditoría, campos y verificación del visor | `results/f02/enumeration.json`, `controls.json`, `verification.json`, `fields.npz`, `browser.json` en `results/f02/` |
| Núcleo del cálculo | `src/mcoc_p2/e08/solver.py`, `e10/boundaries.py`, `e12/metrics.py`, `e14/model.py`, `f02/pipes.py`, `f02/study.py` bajo `src/mcoc_p2/` |

E14 documenta Python 3.12.10 AMD64 y dependencias bloqueadas en `requirements-lock.txt`. La versión del perfil local se registra en `results/verification/hpc_runtime_local.json`. La disponibilidad inicial de paquetes puede requerir conexión al índice de Python. Los cálculos usan instantáneas locales y conservan las fuentes archivadas.
