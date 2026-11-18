# Abrir la revisión F02

Descomprime el ZIP y abre una terminal en la carpeta P2_E14. Usa Python 3.12.

En Linux o macOS:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
.venv/bin/python web/servidor.py
```

En Windows puedes ejecutar `Iniciar E14.bat`. Si prefieres la terminal, usa
`py -3.12` para crear el entorno y `.venv\Scripts\python.exe` en las
órdenes de instalación y arranque.

Abre http://127.0.0.1:8714/ en el navegador y selecciona **F02 · Enfriamiento**.
El HTML se sirve con Python. Los gráficos, campos guardados y paneles E14
funcionan localmente una vez instaladas las dependencias.

Para verificar los resultados F02 incluidos, ejecuta `python scripts/verify_f02.py`
con el Python del entorno virtual. Los 24 escenarios, controles, evidencia
del navegador y tabla comparativa están en `results/f02/`.

Para regenerar las simulaciones con `scripts/run_f02.py`, o auditar los
archivos históricos E14 con el verificador archivado, los scripts usan la
etiqueta Git `entrega-e14` para la procedencia. Con acceso al repositorio,
puedes obtenerla dentro de la extracción independiente mediante:

```bash
git init
git fetch --depth=1 https://github.com/amvaras/Proyecto-2-MCOC.git tag entrega-e14
```

Estas órdenes no sustituyen los archivos extraídos. Luego sigue
`docs/F02_ENFRIAMIENTO.md` y usa una carpeta de resultados nueva.
