# E07 — Auditoría de implementación y revisión oral

Fecha: 4 de noviembre de 2026, America/Santiago. Grupo 2.
Veredicto técnico: **LISTA PARA LA REVISIÓN ORAL E07**, dentro del alcance
de integración geométrica y estructuras de construcción/hidratación.
No se declara una simulación térmica final ni se garantiza puntuación.
Estado formal separado: **COMMIT E06 PENDIENTE DE PUBLICACIÓN**; E07 sin
commit publicado verificado. No se hicieron operaciones Git de escritura.

## Base y conservación

P2_E07 no existía al comenzar. Se inspeccionó E06: arquitectura del paquete,
thermal_nd.py, lector/validador/generador IFC, sus 198 pruebas, resultados,
auditoría y restricciones formales. Se copiaron físicamente **1292 archivos
útiles**, sin entornos ni cachés. La base conserva documentación, figuras,
evidencias, IFC y las 24 ruedas bloqueadas para instalación sin red.

[E07_BASE_E06_INVENTARIO.json](E07_BASE_E06_INVENTARIO.json) identifica los
archivos útiles copiados y sus SHA256. El inventario completo de E06 anterior
al trabajo está en
[E06_INTEGRIDAD_PREVIA.json](../evidencias/e07/E06_INTEGRIDAD_PREVIA.json).
El README E06 original está en README_HEREDADO_E06.md. Los inventarios E06
heredados siguen siendo constancias históricas de esa entrega.

Solo se modificaron dos archivos heredados: README.md y pyproject.toml
(versión/descripcion 0.7.0). requirements-lock.txt no cambió. No se modificó
ningún solver, test, script, configuración o modelo IFC heredado. Los 29
archivos Python heredados en src/tests/examples/scripts conservan sus bytes.
No se eliminó ningún archivo técnico de la base.

Archivos de implementación nuevos: e07/__init__.py, geometry.py, ifc.py,
voxel.py, faces.py, construction.py, hydration.py, coupling.py y plots.py bajo
src/mcoc_p2; examples/run_e07.py; configs/e07/demo.json;
scripts/verify_e07.py y check_e07_independence.py; tres archivos de tests E07
y e07_helpers.py. Se añaden los cuatro documentos E07 solicitados, enunciado,
inventario base, README heredado, figuras y resultados reales.

La comparación SHA256/tamaño/mtime final protege E01 (7579 archivos),
E02 (7660), E04 (7722), E05 (8342) y E06 (8717). No se encontró P2_E03.
El resultado completo está en
[proteccion_entregas.json](../evidencias/e07/proteccion_entregas.json).

## Matriz de cumplimiento

Las rutas de evidencia siguientes se refieren a
[verificacion_02](../evidencias/e07/verificacion_02/verification.json).
Las preguntas se prepararon con respuestas y comandos; no se atribuye a la
automatización una defensa oral humana que todavía no se ha observado.

| Requisito | Implementación | Test | Evidencia | Estado |
|---|---|---|---|---|
| 1. Extracción IFC | ifc.read_pours, PourSolid y ClosedMesh | Lectura real, unidades mm, placement rotado/trasladado, rechazo de metadatos | demo/geometry.json y geometry.npz; ifc_check heredado | CUMPLE Y VERIFICADO |
| 2. Primer voxelizador | voxelize y ClosedMesh.classify | Cubo conocido, prisma cóncavo, frontera/arista/vértice, orientación y escala | demo/voxels.npz; tests geometry | CUMPLE Y VERIFICADO |
| 3. vertida_id | Voxelization y desempate por menor ID | Identificadores reales, centro compartido, orden de entrada y solapes | geometry.json, voxels.npz, checks | CUMPLE Y VERIFICADO |
| 4. Estimación volumétrica | Voxelization.report y estudio cúbico | Volumen conocido independiente; total/por pieza del IFC; tres pasos | summary.json y e07_error_volumen.png | CUMPLE Y VERIFICADO |
| 5. Diseño de hidratación | AdiabaticCurve, HydrationContext, q_dot_h | Derivada adiabática, integral independiente, agotamiento y edad | hydration, construction.npz, curva | CUMPLE CON OBSERVACIONES |
| 6. Estructura de activación | PourEvent, ConstructionState | t=0, posterior, simultáneos, no repetición y eventos exactos | timeline, test_e07_construction | CUMPLE Y VERIFICADO |
| Oral 1: pertenencia | Semiespacios comprobados y ángulo sólido | interior/exterior, malla en L y límites degenerados | E07_DEMO pregunta 1; geometry.py | CUMPLE Y VERIFICADO |
| Oral 2: staircase | Caras cartesianas y cuantificación por pieza | Cubo exacto y geometría docente | Figuras de vóxeles y superficies; pregunta 2 | CUMPLE Y VERIFICADO |
| Oral 3: error frente a Δ | Tres resoluciones con errores firmados | Cambio de volumen sin exigir monotonía | volume_study; pregunta 3 | CUMPLE Y VERIFICADO |
| Oral 4: superficie exterior | exposed_faces con seis vecinos | Celda anisótropa, normal/área, misma pieza y pieza futura | faces.npz, exterior, timeline; pregunta 4 | CUMPLE Y VERIFICADO |
| Oral 5: interfaz | contacts y conductancia en MaskedAssembly | Mismo ID, IDs activos distintos y vecino futuro; intercambio opuesto | interfaces y tests de contacto; pregunta 5 | CUMPLE Y VERIFICADO |
| Oral 6: inicialización | advance_to solo en celdas nuevas | Temperaturas previas preservadas, edad cero y no reaplicación | construction.npz, timeline; pregunta 6 | CUMPLE Y VERIFICADO |
| Oral 7: unidades q_dot_h | H_vol [J/m³] × tasa [1/s] | Fuente/potencia y comparación dimensional con capacidad | source y assembly; pregunta 7 | CUMPLE Y VERIFICADO |
| Oral 8: curva adiabática | T_ad y source derivadas de ξ | Derivada de T_ad y cuadratura de calor total | Figura de curva, tests de hidratación; pregunta 8 | CUMPLE Y VERIFICADO |
| Oral 9: temperatura | Modelo por edad real sin dependencia de T | Fuente idéntica a 10 y 70 °C | Test prescribed_curve y pregunta 9 | CUMPLE CON OBSERVACIONES |
| Compatibilidad térmica | MaskedAssembly con clases y balances E06 | Coincidencia de potencia/energía/cota en máscara completa, Robin y adiabático | Tests full_mask y potencia demo | CUMPLE Y VERIFICADO |
| Regresión completa | verify_e07 → verify_e05 | 198 heredadas +54 nuevas, diez casos y 60 variantes | JUnit y reportes térmicos | CUMPLE Y VERIFICADO |
| Autonomía | Copia física y nueva instalación offline | Suite y demostraciones externas | e07_independencia | CUMPLE Y VERIFICADO |
| Conservación de entregas | Inventarios antes/después | SHA256, nombres, tamaños y fechas | proteccion_entregas.json | CUMPLE Y VERIFICADO |

Las observaciones sobre hidratación indican parámetros ficticios y ausencia
de dependencia térmica/calibración, admitidas por el alcance preliminar E07.
No representan una capacidad cinética avanzada que se haya dado por aprobada.

## Ejecuciones reales

1. Primer intento de tests nuevos: **dos errores de colección** por importación
   relativa del helper desde un directorio tests sin paquete. Se conserva
   e07_primeros_tests/pytest.xml. Se cambió a importación del helper desde el
   directorio de tests; no se cambió la física para obtener PASS.
2. Suite nueva intermedia: 44 aprobadas; con CLI, 50. Se añadieron tres
   regresiones de metadatos IFC y una de propiedades por vertida: **54 nuevas**.
3. Verificación integral 01: 251 aprobadas en 30,479 s JUnit, antes de la última
   regresión de configuración por pieza.
4. Verificación integral local final 02: **252 aprobadas en 32,038 s JUnit**,
   0 fallos, errores u omisiones. Se repitió también la batería térmica.
5. Verificación externa: **252 aprobadas en 31,225 s JUnit**, 0 fallos,
   errores u omisiones. Dos demos E07, diez casos térmicos y 60 variantes PASS.

Desglose: diffusion_1d 62; E02 13; thermal_nd 57; IFC heredado 5;
E05 61; geometry E07 25; construction E07 22; CLI E07 7.
No se sumaron ejecuciones repetidas para inflar el número de tests distintos.

El primer caso de figuras mostró repr de NumPy en el título de resolución;
se convirtió a float y se aclararon los ticks. La malla cúbica inicial de
0,2 m mostró sesgo de reparto por centros exactamente sobre interfaces.
Se preservó esa demo y se adoptó una grilla nominal anisótropa con dz=0,1375 m,
sin empates de frontera en este caso. El desempate sigue probado por separado.
No se ocultaron errores por vertida: la geometría aproximada sigue siendo
una discretización staircase.

## Geometría y volúmenes

El lector procesa las cinco geometrías IFC reales con transformaciones y SI,
sin reconstrucción manual para clasificar centros. El validador previo
comprueba cotas docentes, mallas orientadas, jerarquía y propiedades.
La referencia malla es 636,877717582 m³, con diferencia 0,007318866 m³ frente
a 636,885036448 m³ analíticos por teselación circular. No se mezclan ambas.

La grilla nominal tiene origen aproximadamente (−9,−9,0) m, pasos
(0,275;0,275;0,1375) m, dimensiones 66×66×32 y límite superior (9,15;9,15;4,4) m.
Tiene 139392 celdas, 60892 ocupadas y V_celda=0,0103984375 m³.
V_voxel=633,18165625 m³; diferencia absoluta 3,696061332 m³ y error 0,5803408%
frente a malla IFC. No hay centros compartidos entre piezas en esta grilla.

| ID | Celdas | Volumen voxel [m³] | Volumen malla IFC [m³] | Error absoluto relativo [%] |
|---|---:|---:|---:|---:|
| 1 | 14088 | 146,49318750 | 147,62571363 | 0,7671605 |
| 2 | 14088 | 146,49318750 | 147,62571363 | 0,7671605 |
| 3 | 20630 | 214,51976563 | 214,22435090 | 0,1378997 |
| 4 | 8544 | 88,84425000 | 88,92474828 | 0,0905240 |
| 5 | 3542 | 36,83126563 | 38,47719114 | 4,2776655 |

| Δ cúbico [m] | Grilla | Ocupadas | V_voxel [m³] | Error total frente a malla [%] |
|---|---|---:|---:|---:|
| 0,55 | 33×33×8 | 3855 | 641,37562500 | 0,7062435 |
| 0,275 | 66×66×16 | 30639 | 637,19545313 | 0,0498896 |
| 0,1375 | 131×131×32 | 244477 | 635,54470117 | 0,2093049 |

La malla fina cúbica reduce mucho algunos errores por pieza, pero el total
de la intermedia se beneficia de cancelaciones. No se declara orden espacial
ni monotonía del voxelizador. Los costos reales medidos están en elapsed_s de
cada fila de summary.json; no se usan tiempos estimados como evidencia.
El presupuesto de dos millones de celdas se controla antes de reservar puntos.

## Superficies, interfaces y construcción

Exterior final: **12736 caras y 747,93125 m²** de área staircase.
Áreas x−/x+/y−/y+: 53,8071875 m² cada una; z−/z+: 266,35125 m² cada una.
Las áreas no se presentan como superficie euclídea exacta del IFC.

Interfaces activas del modelo completo: **9032 caras y 683,045 m²**.
Por par: 1–2 266,35125; 2–3 256,595625; 3–4 121,831875; 4–5 38,26625 m².
Se cuentan una sola vez. Los contactos de igual ID no son interfaces entre
vertidas, pero sí participan en conducción. El total de contactos conductivos
activos es 176308. No se aplica Robin sobre ninguna interfaz interna activa.

El calendario ficticio activa a 0,5,10,15,20 h con colocación 18,19,20,21,22 °C.
time_grid alcanza todos los eventos exactamente; max_step=7000 s es muestreo
constructivo, no paso de un solve térmico. La demo reevalúa exteriores activos
y caras frente a futuras piezas. Las anteriores conservan T, y la nueva edad
comienza en cero. Se ensayan simultáneos, repetición y salto indebido de evento.

## Hidratación y acoplamiento exacto alcanzado

Modelo prescrito cosenoidal: ξ=[1−cos(π·clip(edad/τ,0,1))]/2 y
q_dot_h=H_vol·dξ/dt. H_vol=64,8 MJ/m³, τ=48 h; potencia volumétrica en W/m³.
La integral de la tasa y la diferencia de potencial conservan H_vol; fuera
del intervalo de liberación la tasa es cero. La curva adiabática tiene alza
potencial 30 K con rho=2400 y cp=900. Son parámetros ilustrativos, sin
calibración ni inferencia de temperatura real de la fundación.

No se implementó dependencia de temperatura. Edad real y edad equivalente no
se confunden: solo existe la primera. El test de invariancia frente a T es
la evidencia de esa limitación, no una validación de Arrhenius.

MaskedAssembly excluye vacíos e inactivos, usa contacto perfecto y resistencia
de media celda en Robin. Coincide con el solver de cajas E06 para una máscara
completa. En la demo final de colocación, capacidad activa 1367672377,5 J/K,
fuente instantánea 302944,07026 W y potencia saliente −2513,09576 W.
El signo negativo indica entrada neta del ambiente en ese estado de colocación.
Residuo de balance 7,6853e-11 W frente a 3,0295e-4 W de tolerancia.

Esto demuestra compatibilidad y balance del ensamblaje, no una historia de
temperaturas integrada. El siguiente paso es un integrador enmascarado con
fuente por edad y balance de energía de material entrante. No se declara
implementado ni se fuerza al solver de caja a simular vacío como hormigón.

## Reproducción, figuras y cierre

Instalación local y externa sin red con ruedas copiadas; pip check aprobado.
CPython 3.12.10, Windows AMD64, NumPy 2.5.4, pytest 9.1.1,
Matplotlib 3.11.2, IfcOpenShell 0.9.0.post1 y mcoc-p2 0.7.0.
No se incorporaron nuevas dependencias ni se presume portabilidad ensayada
en otras plataformas. La ruta efectiva de import se comprueba bajo la copia.

[e07_independencia](../evidencias/e07_independencia/independence.json) registra
la copia física externa, nuevo entorno, instalación offline, comandos y resultados.
La comparación local/externa confirmó idénticas las **49 huellas de entrada**,
los reportes científicos (excluyendo tiempos de ejecución y rutas de procedencia),
**34 arrays** y los bytes de las **cinco figuras**. También se verificaron
la identidad de seis caras por celda y el cierre de área orientada de la
superficie voxelizada. Constancia:
[comparacion_reproduccion.json](../evidencias/e07/comparacion_reproduccion.json).
Las rutas absolutas de los logs identifican dónde se ejecutó; los scripts no
dependen de ellas para funcionar. Las figuras vigentes se copiaron físicamente
desde la demo local final a figures/ y se revisaron visualmente: vóxeles,
volumen, superficies/interfaces, cronograma y curva. Se distingue procedencia
Python/IfcOpenShell de una captura de Bonsai.

La guía E07_DEMO.md contiene las nueve respuestas, explicación física,
funciones reales, comandos, resultados esperados y limitaciones. No se afirma
que el estudiante haya realizado ya la defensa. El contenido está preparado
para cambios de resolución, calendario, fronteras y parámetros por vertida.

No se identificaron errores técnicos bloqueantes para los entregables E07.
Persisten las limitaciones intencionales: grilla por centros, área staircase,
contacto perfecto, mallas simples, hidratación prescrita sin calibración ni
dependencia térmica y ausencia de integrador final. No se implementaron E08–E15.
E06 conserva su pendiente de commit y E07 no se presenta como publicado.
