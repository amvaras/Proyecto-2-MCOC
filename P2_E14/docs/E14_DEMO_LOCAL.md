# E14 — Demostración con el computador disponible

Modalidad acordada el 18 de noviembre de 2026: trabajar con los recursos locales del grupo. El acceso a un cluster no está confirmado. Esta demostración acredita muestreo reproducible, cálculo paralelo local, métricas y agregación; el requisito de ejecución en cluster sigue sin acreditar y su aceptación debe resolverla el curso.

## Abrir y ejecutar sin comandos

1. Abrir `P2_E14/docs/demo_local`.
2. Hacer doble clic en **Ejecutar demo E14.bat**. Usa el entorno Python propio de E14; si no está instalado, abrir primero el lanzador original `Iniciar E14.bat`.
3. Esperar a que termine. Por defecto ejecuta un plan, N=1000, semilla 20261121 y dos procesos, con malla final .45/.45/.11 m y horizonte de 744 h. Las 1000 realizaciones se reducen a 24 inputs físicos distintos; una caché nueva permite comprobar cálculo térmico real en esta ejecución.
4. Se abre un resumen HTML con resultados, Pf(N), intervalos y primeras semillas. El resumen conserva los enlaces a inputs y outputs de esa corrida.

Cada ejecución crea una carpeta nueva en `results/verification/demo_local_e14`. No reemplaza la corrida oficial ni las ejecuciones anteriores. El tiempo depende del computador; la primera demostración calcula los inputs. Para consultas inmediatas, abrir el `resumen.html` ya generado.

Para ensayar nuevas muestras rápidamente, hacer doble clic en **Probar muestras rapido.bat** después de modificar N o semilla. Consulta los casos conocidos y trabaja con una caché propia; no escribe en la biblioteca oficial. Si se cambia la malla y faltan inputs, calcula únicamente esos casos nuevos.

## Modificar la demostración

Editar `docs/demo_local/parametros.json`: `N` es el número de realizaciones; `master_seed` fija el banco; `workers` es el número de procesos locales (1–4). `plan_ids` elige planes de `configs/e14/study.json`. La malla está en metros y `step_s` en segundos. Dos ejecuciones con igual semilla e inputs deben producir las mismas muestras y métricas, aunque varíen los tiempos de CPU y los IDs de proceso.

Desde PowerShell, situado en P2_E14, también se puede ejecutar:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B docs\demo_local\ejecutar.py --N 2000 --seed 20261122 --workers 2 --abrir
```

Para mostrar rápidamente nuevas muestras y probabilidades usando inputs ya comprobados:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B docs\demo_local\ejecutar.py --N 10000 --seed 20261122 --workers 2 --reutilizar-oficial --abrir
```

El resumen distingue simulaciones nuevas de inputs reutilizados. Remuestrear no exige volver a integrar un input determinista idéntico. El modo rápido permite ensayar la actividad sin esperar la física nuevamente.

## Qué mostrar al ayudante

| Solicitud | Evidencia |
|---|---|
| Generar nuevas muestras | Cambiar N/semilla y ejecutar; banco completo en `manifest.json`. |
| Mostrar seeds | Tabla del HTML y `bank.samples` dentro del manifest. |
| Ejecutar un batch | Lanzador y progreso por tarea; dos procesos locales por defecto. |
| Inspeccionar la ejecución | `progress.json`, `summary.json` y `verificacion_local.json`; cada chunk registra PID, host y estado. No son JobIDs Slurm. |
| Explicar inputs/outputs | Manifest: parámetros, hashes, versiones, muestras, tareas y mapping. Chunks: métricas y balance por input. Summary: agregación Monte Carlo. |
| Agregar resultados | `examples/run_e14.py aggregate --manifest RUTA_DEL_MANIFEST`; no repite el solver. |
| Mostrar Pf(N) | Imagen y tabla/series del resumen. La corrida oficial de 10000 realizaciones por plan sigue disponible en la web E14. |
| Explicar independencia | Cada ID deriva su generador desde la semilla maestra; el orden de procesos no cambia los draws. Historias completas conservan dependencia temporal. Los planes comparten draws para una comparación emparejada. |
| Slurm | Scripts preparados y emulación local comprobada; ejecución remota no acreditada. |

La web original continúa funcionando con `Iniciar E14.bat` y `http://127.0.0.1:8714/`. Allí se pueden editar muestras y decisiones, ejecutar y consultar resultados. Su worker usa un proceso; el lanzador de esta guía demuestra paralelismo con varios procesos.

## Reanudar una corrida interrumpida

Conservar la carpeta y usar su manifest, sin cambiar los parámetros:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B docs\demo_local\ejecutar.py --resume RUTA_DEL_MANIFEST --retry-failed --abrir
```

Una corrida terminada se consulta abriendo su HTML; para otra muestra se crea una nueva. Si queda un lock por interrupción, comprobar primero que el proceso no siga ejecutándose. La agregación exige todas las tareas y no interpreta errores numéricos como éxitos térmicos.

## Interpretación para la defensa

«Ejecutamos Monte Carlo en paralelo en nuestro computador con semillas reproducibles, inputs y resultados trazables. Dejamos preparado Slurm; no presentamos una ejecución de cluster porque el acceso no está confirmado».

Pf es la frecuencia de exceder Tmáx>70 °C **o** ΔTmáx>20 °C bajo el modelo discreto declarado. La enumeración oficial tiene un mínimo de 85%, por lo que no se encontró un plan que cumpla 5%. La ejecución correcta del programa y el cumplimiento físico del plan son cuestiones distintas. Los IC cuantifican muestreo condicional, no incertidumbre experimental total ni seguridad de obra.

## Corrida completa comprobada en este computador

[Abrir resumen HTML](../results/verification/demo_local_e14/20261118T125535Z-0193f754/resumen.html). N=1000, semilla 20261121, 24 simulaciones nuevas, dos procesos observados y 398,2 s. Los 24 inputs coinciden exactamente en métricas, balances y hashes de campos con las referencias existentes. Pf=84,90%, IC95%=[82,528%; 87,064%]; referencia exacta del plan=85%. No cumple el objetivo térmico del 5%. El programa y la agregación sí pasaron sus comprobaciones.

Modo rápido probado con N=2000 y semilla 20261122: Pf=85,55%, 24 inputs reutilizados y cero simulaciones nuevas. También se comprobó reanudar una corrida parcial y las 15 pruebas dirigidas de workflow, estadística, Slurm local e integridad. [Evidencia de esta ampliación](../results/verification/demo_local_e14.json).
