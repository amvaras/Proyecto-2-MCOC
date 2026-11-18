# E14 · Operación breve

**Versión de entrega: [entrega-e14](https://github.com/amvaras/Proyecto-2-MCOC/tree/entrega-e14/P2_E14).** Se trabaja exclusivamente en P2_E14; E13 se conserva intacta. Umbrales: Tmax 70°C, ΔT global 20°C, Pf conjunta 5%. Ninguno de los ocho planes cumple.

**Modalidad actual acordada: computador local.** La [demostración local](E14_DEMO_LOCAL.md) permite ejecutar con dos procesos, cambiar N/semilla y abrir un resumen HTML. El acceso a un cluster no está confirmado; la ejecución remota continúa sin acreditar.

## Abrir

Doble clic en `Iniciar E14.bat` desde la carpeta E14; después abrir **http://127.0.0.1:8714/**. El servidor escucha solo 127.0.0.1. Evitar abrir `index.html` directamente: necesita Python para consultar resultados y calcular.

```powershell
Set-Location -LiteralPath 'C:\Users\Usuario\Desktop\Proyecto-2-MCOC\P2_E14'
.\.venv\Scripts\python.exe -X utf8 -B web\servidor.py --port 8714
```

La primera instalación usa `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1`; crea `.venv` propio con Python 3.12 y paquetes oficiales fijados. No cambia instalaciones globales ni necesita otra entrega. En una copia trasladada hay que reinstalar el editable.

Panel E14: comparación oficial, estado de Slurm, semilla, N, método, estimación de coste, lote, cancelación, reanudación, Pf(N), IC y primeras semillas. Cambiar inputs deja advertencia de procedencia anterior y exige estimar nuevamente. Cada ejecución nueva conserva sus inputs. Un diagnóstico individual produce campo 3D, no Pf.

Panel E13: cinco controles anteriores, ocho curvas y tres climas originales. Panel «06 · Visualización 3D»: el caso oficial E14, tiempo, slice, clipping y máximo. «07 · Temperaturas»: núcleo, superficie y ΔT. El caso ilustrativo es `curado_frio5/M4_SS_m00`: Tmax=51,4824°C a 213,5 h; ΔTmax=28,8110°C a 642,25 h. La envolvente sobre sus 24 átomos llega a 51,4987°C. El mayor diferencial ocurre después de retirar la protección a 600 h.

## Ubicaciones y gráficos

| Producto | Ubicación |
|---|---|
| Configuración oficial | [study.json](../configs/e14/study.json) |
| Enumeración exacta | [summary.json](../results/e14/enumeration/summary.json) |
| MC 10000/plan | [summary.json](../results/e14/monte_carlo/summary.json) |
| Seeds, inputs y mapping | [manifest MC](../results/e14/monte_carlo/manifest.json) |
| Campos críticos, balance y máximos | [summary ilustrativo](../results/e14/representative/summary.json) |
| Series, campos y todos los pasos | NPZ en `results/e14/representative` |
| VTK/ParaView | [e14.pvd](../vtk/e14/e14.pvd) |
| Inventario de 15 PNG con procedencia | [figures.json](../results/e14/figures.json) |
| Controles de malla, paso, área y S25 | [numerics_e14.json](../results/verification/numerics_e14.json) |

Abrir primero [cortes térmicos](../figures/e14_secciones.png), [curvas](../figures/e14_temperaturas.png), [probabilidades](../figures/e14_probabilidades.png), [Pf(N)](../figures/e14_pf_N.png) y [sensibilidad](../figures/e14_sensibilidad.png). Los PNG tienen unidades, contexto y pie de procedencia. Regenerar figuras no integra temperatura:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B scripts\plot_e14.py
Invoke-Item .\figures
```

## Reproducir y verificar

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -X utf8 -B -m pytest tests/test_e14_statistics.py tests/test_e14_workflow.py tests/test_e14_web.py tests/test_e14_hpc.py -q
.\.venv\Scripts\python.exe -X utf8 -B -m pytest -q
.\.venv\Scripts\python.exe -X utf8 -B scripts\verify_e14_offline.py --quick
.\.venv\Scripts\python.exe -X utf8 -B scripts\validate_e14_hpc.py
```

La última suite incorpora una prueba JS opcional si Node está en PATH; no es dependencia de la aplicación. Bash se usa para verificar Slurm. Ejecución secuencial/paralela real ya comprobada: [parallel.json](../results/verification/parallel.json). El comando `scripts/verify_e14_parallel.py` vuelve a ejecutar seis solves gruesos: usar solo si cambia algo que justifique repetirlos.

Una configuración modificada requiere **nuevo** destino con `run_e14.py prepare --config ... --output ... --kind mc`; luego `run --manifest ... --workers 2`. `prepare` informa coste antes del solve. `--resume` valida hashes; `--retry-failed` repite errores explícitamente. No editar manifests o resultados oficiales a mano, ni usar `--force-solve` por rutina. Un lock abandonado exige comprobar proceso/job antes de retirarlo.

## Slurm: pendiente de acceso real

En un clúster autorizado, copiar físicamente la entrega autónoma conservando bytes y crear `.venv_hpc` con Python 3.12/NumPy fijados. Instalar desde PyPI oficial y el proyecto propio; ejecutar `pip check`. La instalación Linux y sus ruedas siguen **NO VERIFICADAS** aquí. Antes de enviar, configurar cuenta/partición/módulos con el administrador; no se inventaron credenciales ni se envió ningún job.

```bash
export E14_PYTHON="$PWD/.venv_hpc/bin/python"
bash scripts/hpc/submit.sh results/e14/monte_carlo/manifest.json 2
squeue -j JOBID
sacct -j JOBID --format=JobID,State,ExitCode,Elapsed,MaxRSS
bash scripts/hpc/collect.sh JOBID results/e14/monte_carlo/manifest.json
```

Validar primero un chunk pequeño; conservar sbatch/job ID, sacct y outputs. Un array con inputs ya calculados valida orquestación, no rendimiento térmico. No afirmar HPC real a partir de variables SLURM_* o emulación.

El recolector exige accounting expandido de todos los índices COMPLETED/0:0 y pruebas runtime del mismo JobID/manifest; rechaza salidas vacías, parciales o de emulación. Se probó con fixtures, no contra un clúster. El wrapper también se probó copiado a un spool sintético usando SLURM_SUBMIT_DIR, como define [sbatch](https://slurm.schedmd.com/sbatch.html).

## Límites

Pesos y recursos son hipótesis; no existe validación experimental de la fundación ni cinética térmica calibrada. Área staircase y S25 siguen aproximadas. La menor Pf encontrada (85%) no cumple y no demuestra óptimo global. IC95% MC cuantifica solo muestreo, no incertidumbre física total. No se prepararon F02, informe final ni dossier definitivo E15.
