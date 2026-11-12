# MCOC Proyecto 2 — Grupo 2 — E11

Aplicación local para controlar la simulación térmica del IFC real desde el
navegador: clima, material, vertidas, ejecución Python, gráficos, 3D y verificación.

## Abrir sin PowerShell

**Doble clic en [Iniciar E11.bat](Iniciar%20E11.bat).**

El lanzador verifica el entorno local, inicia el servidor en
**http://127.0.0.1:8711/** y abre el navegador predeterminado de Windows.
La primera instalación necesita Python 3.12 e Internet para paquetes oficiales;
una vez instalada, la aplicación funciona offline. No abrir index.html como
archivo suelto: necesita el backend Python.

1. **Meteorología**: inspeccionar snapshot, metadata, CSV y curva; verificar datos.
2. **Configuración / Vertidas**: cambiar parámetros físicos e instantes de colocación.
3. **Ejecutar simulación**: Python calcula pronóstico y ambiente constante con la
   misma física. Se genera un ID y no se reemplazan los resultados oficiales.
4. **Visualización 3D**: arrastrar para rotar, rueda para zoom, seleccionar tiempo,
   vertidas, plano y posición. Corte / Slice y Recorte / Clipping son interactivos.
   Pulsar un vóxel o una sonda para consultar valores.
5. **Temperaturas**: máxima, mínima, media, núcleo, caras y centros de vertidas;
   inspección de muestras con cursor y comparación de ambos escenarios.
6. **Verificación**: ejecutar pruebas reales, reimportar VTK, reconstruir balance
   y comprobar bloqueo de solicitudes externas.
7. **Restaurar nominal** vuelve a los inputs y resultados oficiales E11.
8. **Cerrar aplicación** detiene el servidor. Si cierras el lanzador que lo inició,
   su canal de vigilancia también termina el servidor y los cálculos propios.

Ver [guía breve](docs/E11_DEMO.md), [auditoría](docs/E11_AUDITORIA.md) y
[estado medido](docs/E11_ESTADO.json). Código web único en web/; solver vigente en src/.
No hay CDN, nuevos paquetes web ni una segunda lógica térmica en JavaScript.

## Resultados y ejecución reproducible

Oficiales: results/e11/, figures/ y vtk/e11/. Las dos corridas iniciadas desde
Chrome para verificar esta integración se conservan separadas en results/web_runs/.
Sus inputs y arrays se compararon exactamente con Python directo; evidencia en
results/verification/web_equivalence.json. Las pruebas no reutilizan resultados
oficiales como sustituto de un cálculo nuevo.

Los experimentos nuevos quedan identificados por inputs efectivos, hash, fecha,
snapshot y código. Se conservan hasta seis corridas. La interfaz permite
descargarlas y retirar una seleccionada con inventario y confirmación; nunca la
oficial, ni archivos desconocidos. Cambios sin ejecutar muestran una advertencia.

El entorno instalado .venv es local y está en uso mientras funciona el servidor;
se excluye del entregable y del inventario para versionar. No se copian entornos
de entregas anteriores. No retirar el entorno mientras la aplicación esté abierta.

## Comandos opcionales de desarrollo

Desde esta carpeta en PowerShell:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1
& .\.venv\Scripts\python.exe -m pip check
& .\.venv\Scripts\python.exe -X utf8 -B -m pytest -q -p no:cacheprovider
& .\.venv\Scripts\python.exe -X utf8 -B scripts/verify_e11.py --reproduce
& .\.venv\Scripts\python.exe -X utf8 -B web/abrir.py
~~~

La prueba unitaria JS usa Node si está disponible (solo desarrollo); el navegador
y la aplicación no lo necesitan. El botón de pruebas informa sus contadores y
cualquier omisión explícitamente. PyVista nativo también se abre desde el HTML,
para el resultado seleccionado, sin terminal.

El CLI examples/run_e11.py sigue disponible. Rechaza destinos existentes;
admite --hours, --spacing DX DY DZ, --output, --vtk-dir y --figures-dir.
scripts/plot_e11.py regenera PNG desde campos guardados; la adquisición de otro
snapshot continúa siendo una acción separada mediante scripts/fetch_weather_e11.py.

La [etiqueta entrega-e11](https://github.com/amvaras/Proyecto-2-MCOC/commit/entrega-e11)
identifica el commit evaluado. Para Canvas, copie el SHA completo de ese commit.

