# MCOC Proyecto 2 · E14

Monte Carlo reproducible, comparación de ocho planes y campos térmicos 3D, con el mismo solver de E13. Versión de entrega: [entrega-e14](https://github.com/amvaras/Proyecto-2-MCOC/tree/entrega-e14/P2_E14), rama `codex/e14` del repositorio de Amelia.

**Modalidad comprobada: ejecución paralela local.** Se recalcularon 24 inputs térmicos con dos procesos y se verificó igualdad exacta con las referencias. Acceso a cluster no confirmado; la ejecución remota del enunciado continúa sin acreditar.

- [Demostración local y resultados guardados](docs/E14_DEMO_LOCAL.md).
- [Lanzador para recalcular](docs/demo_local/Ejecutar%20demo%20E14.bat) y [modo rápido para nuevas muestras](docs/demo_local/Probar%20muestras%20rapido.bat).
- [Auditoría de la entrega](docs/E14_AUDITORIA_20261118.md) e [identificación para Canvas](docs/E14_PUBLICACION.md).

Abrir `Iniciar E14.bat` con doble clic y entrar a **http://127.0.0.1:8714/**. La pestaña inicial es «E14 · Monte Carlo / HPC». «06 · Visualización 3D» muestra el caso ilustrativo `curado_frio5 / M4_SS_m00`, incluyendo cortes y clipping. No es un plan factible: Pf exacta condicional = 85%.

En PowerShell, desde esta carpeta:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1
.\.venv\Scripts\python.exe -X utf8 -B -m pytest -q
.\.venv\Scripts\python.exe -X utf8 -B web\servidor.py --port 8714
```

Instalación local Python 3.12 desde PyPI oficial y proyecto editable propio; versiones en `requirements-lock.txt`. El lanzador instala solo si falta `.venv`. No copiar entornos. En otra ubicación, instalar de nuevo para que el import editable apunte a la copia.

Verificar los resultados oficiales guardados, sin modificarlos ni repetir física:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B scripts\verify_e14_offline.py --quick
Invoke-Item .\figures
```

Nueva semilla, N o plan: editar una **nueva** configuración dentro de la entrega y preparar una carpeta nueva; no reemplazar el oficial. CLI `prepare` muestra inputs únicos, reutilización y coste antes de ejecutar. Web exige estimación actualizada antes de lanzar un lote.

```powershell
.\.venv\Scripts\python.exe -X utf8 -B examples\run_e14.py prepare --config configs/e14/study.json --output results/e14/nuevo_lote --kind mc
.\.venv\Scripts\python.exe -X utf8 -B examples\run_e14.py run --manifest results/e14/nuevo_lote/manifest.json --workers 2
```

Guías técnicas breves:

- [Operación y ubicaciones](docs/E14_OPERACION.md).
- [Modelo, incertidumbres y estadística](docs/E14_FORMULACION.md).
- [Estado y verificaciones](docs/E14_ESTADO.md).
- [Reproducción sin Internet y auditoría sin simulaciones](docs/E14_REPRODUCCION_OFFLINE.md).
- [Prueba real de Slurm pendiente](docs/E14_HPC_PENDIENTE.md).
- [Conjunto definitivo y pendientes antes de F02](docs/E14_CIERRE_F02.md).

Resultados únicos oficiales: `results/e14/enumeration` (24 átomos/plan), `monte_carlo` (10000 realizaciones/plan), `cache` (casos físicos únicos), `representative` (campos críticos), `vtk/e14` y `figures`. La base E13 seleccionada se conserva físicamente como control reutilizable. No depende de otra entrega.

Slurm tiene sintaxis y emulación local verificadas; **no hubo ejecución en clúster**. No se encontró un plan con Pf≤5%. Los intervalos MC no incluyen error numérico ni incertidumbre de calibración. No se prepararon diapositivas F02, informe final ni dossier E15.

La actualización del índice de integridad por los metadatos de publicación queda documentada en `results/verification/publicacion_final_e14.json`; conserva los hashes del código físico, datos, campos y resultados.
