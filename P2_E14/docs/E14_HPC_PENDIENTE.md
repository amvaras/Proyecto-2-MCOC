# E14 · Prueba mínima real en Slurm

**PENDIENTE: no se identificó host, cuenta o acceso autorizado a un clúster.** Hay cliente SSH local, pero no `sbatch`, `squeue` o `sacct` locales. Eso no constituye acceso a HPC. No se enviaron trabajos ni se solicitaron credenciales.

Se verifican `array.sbatch`, `submit.sh`, `collect.sh`, el worker y el recolector. Los archivos Bash usan LF; el wrapper usa SLURM_SUBMIT_DIR cuando el planificador copia el script al spool. Cada índice tiene un chunk y output propios. El recolector exige accounting expandido COMPLETED/0:0 y todos los proofs runtime del mismo JobID y manifest; rechaza emulación, accounting vacío o incompleto.

## Cuando exista autorización y acceso

Copiar los archivos de la entrega sin cambiar sus bytes al directorio autorizado. Preparar Python 3.12 y el NumPy fijado; instalar el proyecto local y verificar `pip check`. La instalación Linux sigue pendiente de comprobar. Confirmar con el centro la cuenta, partición, módulos y permisos del filesystem. No se inventan esos valores.

La prueba usa `configs/e14/hpc_smoke.json`: un plan, N=1, un input ya calculado. **No estima riesgo ni mide rendimiento del solver**; verifica envío, array, entorno, cache y recolección sin repetir física.

En una sesión ya autorizada del clúster, desde P2_E14:

```bash
export E14_PYTHON="$PWD/.venv_hpc/bin/python"
unset E14_LOCAL_EMULATION
"$E14_PYTHON" -m pip check
"$E14_PYTHON" -B scripts/verify_e14_offline.py --quick
"$E14_PYTHON" -B examples/run_e14.py prepare --config configs/e14/hpc_smoke.json --output results/e14/hpc/smoke --kind mc --chunk-size 1
```

La estimación debe mostrar **1 input reutilizado y 0 nuevos**. Si indica nuevos o falla un hash, detenerse y revisar. La carpeta de salida debe ser nueva. Configurar los parámetros propios del centro antes de enviar; los scripts no adivinan cuenta/partición. Después:

```bash
job=$(bash scripts/hpc/submit.sh results/e14/hpc/smoke/manifest.json 1)
squeue -j "$job"
sacct --array -j "$job" --format=JobID,State,ExitCode,Elapsed,MaxRSS
bash scripts/hpc/collect.sh "$job" results/e14/hpc/smoke/manifest.json
```

Guardar JobID, logs `%A_%a`, proof runtime y `results/e14/hpc/job-JOBID.json`. Debe haber un índice 0 COMPLETED/0:0. Solo entonces podrá marcarse verificada la ejecución real de esa prueba. Un envío aceptado o una variable SLURM_* no bastan.

Para reanudar, mantener manifest, semillas y hashes. Si un lock permanece, comprobar PID/job antes de retirarlo. No borrar locks desconocidos ni usar `--force-solve` para esta comprobación.

La emulación local no cambia el estado pendiente de HPC real. La documentación está basada en los contratos oficiales de [job arrays](https://slurm.schedmd.com/job_array.html), [sbatch](https://slurm.schedmd.com/sbatch.html) y [sacct](https://slurm.schedmd.com/sacct.html); su adaptación al centro requiere la prueba anterior.
