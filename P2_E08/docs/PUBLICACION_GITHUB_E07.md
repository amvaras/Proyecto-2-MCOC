# Importación de E07 para GitHub

Fecha: 4 de noviembre de 2026, America/Santiago.
Repositorio: https://github.com/amvaras/Proyecto-2-MCOC.
Rama de esta entrega: `codex/e07`, creada desde la entrega E04 publicada.

## Procedencia

El usuario entregó `P2_E07.zip` y autorizó incorporarlo al repositorio.
SHA256 del ZIP original:
`80a2005ba77d773e88161f8157a3aabb287966b21c4fcb835d6e46f40fc1036a`.

Se verificaron los **1811 archivos** enumerados por el inventario E07:
todos coincidieron con sus hashes antes de preparar la publicación.
Se extrajeron 1845 archivos útiles; el ZIP también contiene 33 resultados
posteriores a ese inventario, que se conservan. El propio inventario completa
la cuenta. Se excluyeron 7456 archivos de entornos y cachés recreables.
Las 24 ruedas de `vendor/wheels/` se conservan para la instalación sin red.

La entrega incluye físicamente su base E06 dentro de P2_E07. No se recibió una
carpeta E06 independiente y no se creó una entrega E06 diferente a partir de
esta copia acumulativa. Los archivos existentes de E01, E02 y E04 no cambiaron.
El caso hipotético local del rectángulo no forma parte de este commit.

## Ajustes de publicación

No se modificó el código, los tests, las configuraciones ni el IFC recibido.
Solo se adaptaron estos dos archivos originales:

- `.gitattributes`: conserva los bytes de esta carpeta sin conversión automática
  de finales de línea. Así Git no invalida los hashes de código y evidencias
  al almacenar o descargar el proyecto. El original está en
  `GITATTRIBUTES_ORIGINAL_ZIP_E07.txt`.
- `README.md`: agrega un aviso de importación que distingue los estados
  históricos de publicación de la operación Git actual. Su versión original
  está en `README_ORIGINAL_ZIP_E07.md`.

Los inventarios originales se preservan sin regenerarlos: describen el ZIP
anterior a estos ajustes, no un inventario cerrado de los archivos añadidos
durante la publicación. `PUBLICACION_E07_PROCEDENCIA.json` registra lo importado.
Las frases antiguas de E06/E07 sin publicar en documentos o logs conservan su
contexto histórico y no identifican el SHA de la publicación actual.

## Comprobación local

Se creó `.venv-e07` fuera de la carpeta de entrega. Las dependencias se
instalaron sin red exclusivamente desde las ruedas del ZIP, con Python 3.12.
Después se instaló el paquete E07 0.7.0 desde esta carpeta y se ejecutó:

```powershell
..\.venv-e07\Scripts\python.exe -X utf8 -B scripts/verify_e07.py --output evidencias/publicacion_20261104
```

Los logs, conteos de pruebas, versiones, hashes y resultados están en
[`../evidencias/publicacion_20261104/verification.json`](../evidencias/publicacion_20261104/verification.json).
El comando comprueba conservación de código heredado, regresión térmica,
IFC, demostraciones BIM–grilla y un rechazo de resolución inválida.

Resultado nuevo: **252 pruebas aprobadas, 0 fallidas, 0 errores y 0 omitidas**
(61,556 s JUnit), **60 variantes térmicas** y **dos demostraciones E07**
aprobadas. Se comprobaron tres resoluciones de volumen: 0,55/0,275/0,1375 m.
La ejecución usó CPython 3.12.14 en Windows y mcoc-p2 0.7.0.

Para repetir con el entorno autónomo descrito en el README, usar
`.\.venv\Scripts\python.exe` y un destino nuevo. El entorno de preparación
no se incluye en Git.

El SHA evaluado se obtiene del commit Git que contiene esta carpeta.
El éxito de la publicación debe comprobarse con la referencia remota;
esta constancia no reemplaza esa comprobación ni certifica una defensa oral.
