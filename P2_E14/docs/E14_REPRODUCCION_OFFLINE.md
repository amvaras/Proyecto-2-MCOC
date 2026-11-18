# E14 · Reproducir resultados guardados sin Internet

El conjunto oficial contiene 8 planes × 24 escenarios = **192 inputs térmicos únicos**, ocho curvas experimentales y tres historias climáticas congeladas. Monte Carlo usa 10000 realizaciones emparejadas por plan, semilla 20261119; reutiliza esos inputs. La referencia para decidir es la enumeración exacta del modelo discreto.

## Entorno necesario

Este equipo tiene `.venv` propio instalado y `pip check` correcto. Con ese entorno, verificar, consultar tablas, visualizar y regenerar figuras no requiere Internet. Python 3.12 y las versiones declaradas en `requirements-lock.txt` deben estar instaladas previamente.

En un equipo nuevo sin paquetes, `requirements-lock.txt` por sí solo **no permite instalar offline**. Preparar las dependencias desde PyPI oficial antes de desconectarse. No se adjuntan ruedas, entornos copiados ni un repositorio de paquetes. La instalación inicial en otro sistema operativo no se declara verificada.

Una vez disponibles las dependencias, el proyecto propio puede instalarse sin red:

```powershell
.\.venv\Scripts\python.exe -m pip install --no-index --no-build-isolation --no-deps -e .
.\.venv\Scripts\python.exe -m pip check
```

No usar `scripts/install.ps1` sin conexión: descarga las dependencias iniciales. No ejecutar scripts `fetch_*` para mostrar estos resultados.

## Verificación sin recalcular temperatura

Desde P2_E14:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B scripts\verify_e14_offline.py --report results/verification/offline_e14.json
```

El programa bloquea conexiones de red e integradores térmicos en su propio proceso. Comprueba SHA256 de los archivos sellados, 192 configuraciones y sus casos guardados, semillas, probabilidades y CI; reconstruye máximos, S25, hidratación y balance desde los campos existentes. No integra de nuevo la ecuación térmica. La reducción de 31 miembros a tres historias se vuelve a verificar sobre el JSON original local, sin consultar proveedores.

Para una comprobación rápida posterior:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B scripts\verify_e14_offline.py --quick
```

`--quick` conserva hashes y reagrupación de los 192 inputs; omite reconstruir S25 desde todos los pasos. Una discrepancia detiene la verificación. No editar hashes para ocultarla. `--seal` es exclusivamente la creación inicial del conjunto; no se usa para aprobar cambios posteriores.

## Consultar el conjunto único

```powershell
.\.venv\Scripts\python.exe -X utf8 -B web\servidor.py --port 8714
```

Abrir **http://127.0.0.1:8714/**. Solo usa la conexión local al servidor; no descarga bibliotecas web. El HTML no se abre como archivo suelto. En E14 alternar «Restaurar MC oficial» y «Ver enumeración exacta»; en «06 · Visualización 3D» usar tiempo, slice y clipping, y en «07 · Temperaturas» elegir la magnitud. No pulsar «Ejecutar simulación» para consultar los resultados ya guardados.

- `results/e14/official.json`: índice de procedencia, hashes y correspondencia de los 192 inputs.
- `results/e14/plans.csv`: ocho planes, duraciones, horizontes, extremos, estados límite, Pf e intervalos.
- `results/e14/enumeration` y `monte_carlo`: métricas y bancos originales.
- `results/e14/representative` y `vtk/e14`: un caso ilustrativo crítico, no un plan factible.
- `figures` y `results/e14/figures.json`: 15 figuras y su procedencia.

La biblioteca `results/e14/cache` conserva 72 resultados físicos únicos y referencias locales a los 120 casos base. Es parte del conjunto científico reutilizable; no es un caché descartable del navegador o de Python.

Para volver a dibujar figuras desde arrays, sin simulación:

```powershell
.\.venv\Scripts\python.exe -X utf8 -B scripts\plot_e14.py
Invoke-Item .\figures
```

Las imágenes 3D regeneradas pueden variar entre versiones de controlador gráfico. Los originales sellados se conservan como referencia; cualquier diferencia de bytes debe investigarse. No es necesario regenerarlos para la defensa.

Ningún plan cumple Pf≤5%; el mínimo encontrado es 85%. Los pesos y recursos son hipótesis; los IC cuantifican solo muestreo condicional, no calibración experimental ni error numérico. Regresión integrada actual: 447 pruebas aprobadas, sin fallos u omisiones, en `results/verification/junit.xml`; auditoría sin simulaciones en `results/verification/offline_e14.json`.
