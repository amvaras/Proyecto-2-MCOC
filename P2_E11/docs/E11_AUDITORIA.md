# E11 — Auditoría de integración HTML–Python

Esta auditoría registra la implementación y las pruebas realizadas antes
de publicar la entrega. La etiqueta `entrega-e11` identifica el commit evaluado.

## Auditoría inicial y arquitectura elegida

El HTML heredado en web/ sí ejecutaba Python: permitía IFC, malla, material,
hidratación, vertidas, cancelación, fotogramas y WebGL. Pero llamaba al ejecutor
E08, usaba ambiente constante y no tenía meteorología E11, corte, clipping,
sondas ni verificación actual desde navegador. Las figuras se leían de archivos.

Se ampliaron directamente index.html, app.js, styles.css, servidor.py y abrir.py.
No hay un segundo HTML, servidor equivalente ni solver paralelo.
Application conserva el contrato E08 usado por su prueba heredada; la API pública
y el lanzador usan E11. Python es la fuente de verdad; JavaScript presenta
campos, filtros y curvas. El estudio geométrico y el IFC local siguen disponibles.

Se reutilizan lectura IFC, voxelización, activación, hidratación, ensamblaje,
solver E08, weather/boundaries E10 y exportación/reimportación PyVista.
Se añadió e11.webdata para validar/adaptar datos, sin integrar física nueva.
El escritor JSON E11 convierte escalares NumPy a tipos JSON; no cambia números
del solver, unidades o tolerancias. No se añadieron dependencias de ejecución.
Node es opcional, exclusivamente para una prueba unitaria JS de desarrollo.

## Matriz de requisitos oficiales

| Requisito | Archivo | Test / evidencia | Resultado | Estado |
|---|---|---|---|---|
| A Weather trazable (0,8) | e11/weather.py, webdata.py, app.js | Snapshot auténtico; validación backend desde HTML; original/CSV/metadata y curva consultados | 72 horas; hashes, unidades y cobertura PASS | CUMPLE Y VERIFICADO |
| B Robin meteorológico (0,8) | e10/boundaries.py, e08/solver.py, e11/pipeline.py | Casos analíticos y cambios aislados de h, ambiente, T inicial, activación, resolución, hidratación, suelo y moldaje | Campos cambian; comparación mantiene física y pasos iguales dentro de cada corrida | CUMPLE Y VERIFICADO |
| C Visualización 3D (0,7) | viewer.js, vtkio.py, viewer.py | WebGL real Chrome; slice/clip; test XYZ asimétrico; PyVista abierto desde HTML | Celdas y VTK coinciden; GPU informa error GL 0 | CUMPLE Y VERIFICADO |
| D Demostración (0,7) | Iniciar E11.bat, abrir.py, README, E11_DEMO | Lanzador real Windows, dos corridas desde formularios, pruebas desde HTML y bloqueo externo | Operación gráfica sin terminal después de abrir | CUMPLE Y VERIFICADO |

No se garantiza puntaje. La GUI de ParaView está NO VERIFICADA.
La comparación de arrays y los tests no equivalen a validación contra obra.

## Pruebas y resultados ejecutados

- Regresión previa E11: 361 pruebas. Regresión completa actual:
  **393 aprobadas, 0 fallidas, 0 errores, 0 omitidas; 123,974 s**.
  JUnit: results/verification/tests.xml.
- Desde el botón HTML se ejecutaron realmente los tests E11 y web:
  **48 aprobadas, 0 fallidas/errores/omitidas; 69,97 s**.
  Evidencia propia: results/web_runs/verification/tests.xml y tests.txt.
  Ese resultado se mostró con fecha, separado de la auditoría anterior.
- Los 32 casos web incluyen HTTP/recursos locales, metadata y hashes, dos
  equivalencias API/Python, ocho cambios físicos aislados, rechazo de inputs,
  Host/Origin/token, rutas, concurrencia/cancelación, resultados parciales,
  VTK, sondas, máscaras, retiro seguro y cierre del lanzador.
- La prueba JS asimétrica 2×3×4 verifica los tres planos, ambos lados de clip,
  temperatura por celda, futuros, visibilidad y ausencia de modificación física.
- Dos corridas iniciadas por clics y formularios en Chrome se reprodujeron con
  Python directo y HTTP bloqueado. Igualdad EXACTA de todas las matrices de
  grid, fields, statistics y ambos archivos de pasos, sin ajustar tolerancias.
  Ver results/verification/web_equivalence.json.
- Corrida nominal HTML 224521f59e2f4bdcaca00beb965942d8: 7730 celdas, 36 h,
  Tmax=41,2635678134 °C; sus arrays coinciden exactamente con los oficiales.
- Corrida modificada HTML 5b32e0d930d949888f8bd6c42feb65ac: h=18 W/(m² K),
  referencia constante=25 °C, colocación V1=23 °C y activación V2=3 h.
  Tmax=43,9741418907 °C; diferencia final máxima respecto del nominal
  2,8136144911 °C. Cambian cuatro inputs: no atribuir esa diferencia solo a h.
- Ambos escenarios de cada corrida mantienen iguales geometría, materiales,
  hidratación, activaciones, suelo, moldaje y pasos. El contraste meteorológico
  nominal da diferencia final de campo 0,652165 °C.
- Verificar campos desde HTML reimportó cuatro VTI y reconstruyó el balance
  desde capacidades, campos y energías guardadas; no se limitó a leer PASS.
  En la corrida modificada: residual reconstruido máximo 4,30e−6 J,
  tolerancia 0,276301 J.
- La reproducción offline de los oficiales siguió dando igualdad exacta tras
  la integración. IFC4: cinco IfcFooting, unidades m y esquema validado.
  La física de E10 y el archivo IFC no se modificaron.

## Comprobaciones reales de navegador

Chrome predeterminado de Windows abrió la URL 127.0.0.1:8711 mediante el .bat.
Se observó carga de HTML/CSS/JS y datos, 3D WebGL, actualización tras cálculos,
advertencia de cambios sin ejecutar, inputs físicos, sondas y curvas con cursor.
Se consultó el snapshot y metadata; su validación se ejecutó desde un botón.
El mismo campo se abrió en la ventana nativa PyVista mediante el HTML.
No se presentan PNG como sustituto de las dos vistas interactivas.

Slice XZ mostró 366 celdas; clipping lateral, 4097 celdas. A 9 h se observaron
3596 celdas activas; a 36 h, 7730. Ocultar V5 mostró 7222 sin cambiar las
7730 físicamente activas; restaurarla recuperó el pedestal. Rotación, zoom,
consulta de vóxel (33,1180 °C) y curva de núcleo se comprobaron en Chrome.
Los tres planos y ambos lados del recorte tienen además prueba JS asimétrica.
La evidencia de interacción final se conserva en web_browser.json y e11_web.png.
La sesión PyVista de esta integración usa native_web_session.json, sin
sobrescribir la evidencia nativa anterior. Ese registro solo contiene apertura;
el cierre de la nueva ventana se comprobó por su ausencia en el inventario de
ventanas y procesos, sin atribuirle un evento de cierre que no quedó guardado.

El botón de bloqueo externo produjo un evento real CSP connect-src y PASS.
Los recursos del navegador son locales; el servidor no descarga clima.
El CLI de simulación bloquea ambos puntos urlopen. Esta es evidencia de
bloqueo de solicitudes externas; no se deshabilitó la red global de Windows.

## Seguridad, trazabilidad y limpieza

Servidor ligado exclusivamente a 127.0.0.1. Host y Origin permitidos, token
efímero contra solicitudes cruzadas, JSON limitado, rutas cerradas y CSP sin
CORS abierto. No hay ejecución de comandos enviados por navegador ni lectura
arbitraria del PC. Los subprocesos usan scripts y argumentos internos fijos,
stdin DEVNULL, una tarea a la vez, límites de grilla/memoria/pasos y timeout.
El token no es una autenticación de usuarios; es una protección local CSRF.

Cada ejecución tiene ID, inputs efectivos, hashes, fecha, modelo y snapshot.
Se retienen las dos corridas necesarias para demostrar equivalencia; la oficial
permanece independiente. El retiro requiere inventario SHA vigente y confirmación;
rechaza oficiales y conserva archivos desconocidos. No se crean ZIP de respaldo.
La descarga ZIP opcional se construye en memoria, sin crear un archivo histórico.

El entorno local instalado se conserva por estar activo y necesario para la app.
Se excluye de versionado y del tamaño de archivos entregables. La limpieza de
.runtime/.tmp propios usa dry-run y --apply; no retira entornos activos.
Tamaños, contadores y enlaces se verifican en E11_ESTADO.json.

## Problemas encontrados y corregidos

La primera carga detectó tuplas meteorológicas tratadas como arrays: corregida
la adaptación JSON. El primer arnés de tests tenía un nombre local que ocultaba
http.client: corregido sin cambiar resultados esperados. Dos cambios físicos
detectaron np.bool en el balance que impedía serializar JSON: convertido con
.item(), sin modificar la física. El cierre por HTTP con un lector de stdin
buffered causaba un error del intérprete: se sustituyó por lectura de descriptor.

La prueba real del .bat encontró un bloqueo de inicio al heredar ese pipe de
vigilancia en los cálculos. Una corrida alcanzó timeout y se informó FAIL.
Los hijos de cálculo, tests y PyVista ahora reciben DEVNULL. Los tests nuevos
ejecutan una simulación bajo vigilancia del padre y comprueban cierre por EOF
y por HTTP; ambos pasan. La corrida fallida no produjo campos científicos.

Continúan 150 avisos de deprecación de VTK/NumPy en la suite, no fallos;
no se ocultaron. No quedan defectos bloqueantes observados en esta demo local.

## Limitaciones y protección de entregas

Pronóstico de grilla, no estación de obra. Modelo no calibrado, contacto perfecto,
hidratación por edad sin Arrhenius, h constante, sin viento/radiación explícitos
y suelo resistivo idealizado. Malla nominal gruesa: error volumétrico total
0,9675 % y del pedestal 9,8294 %; sin nueva convergencia térmica de E11.
No hay tensiones ni certificación de seguridad/fisuración.

No se escribió en E10 ni otras entregas. SHA de P2_E10.zip antes/después:
2bfa49ec2cc8ffd4ff5fdd19db4a569a10d4c72c7390f92485481ad2e98fee19.
E11_BASE.json conserva la selección original; E11_REPOSITORIO.json es la
inspección previa de solo lectura, no un SHA evaluado E11.
La [etiqueta entrega-e11](https://github.com/amvaras/Proyecto-2-MCOC/commit/entrega-e11)
referencia la publicación en la rama `codex/e11`.

