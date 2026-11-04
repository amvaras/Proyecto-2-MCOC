# E05 — Auditoría técnica final y matriz de cumplimiento

Fecha: **28 de octubre de 2026**. Veredicto: **COMPLETA**.
Se inspeccionó la base real E04, se preservaron sus antecedentes y se ejecutó
E05 de forma incremental, incluidos cambios de parámetros y una instalación
externa independiente. El alcance corresponde al laboratorio E05 del 29 de
octubre, no a etapas posteriores.

## Procedencia e integridad

P2_E05 no existía al empezar. Se comparó P2_E04 con P2_E04.zip: código,
pruebas, configuración y documentación coincidían; la carpeta tenía además
tres resultados de una demo que no estaban en el ZIP. Se eligió la carpeta y
se copiaron físicamente **281 archivos útiles**, excluyendo entornos, cachés
y metadatos generados. La versión original no se modificó.

Antes de copiar se registró el inventario de las entregas existentes.
P2_E01, P2_E02 y P2_E04 mantienen exactamente 7579, 7660 y 7722 archivos,
respectivamente, comparando contenido SHA256, tamaños y fechas de modificación.
No se encontró P2_E03 en la raíz; no se inventa una entrega independiente ni
se atribuyen pruebas a una carpeta ausente. Se heredó toda la suite real de E04.

El código, tests, scripts y ejemplos Python heredados suman **20 archivos**:
ninguno cambió. Los dos solvers y el IFC siguen intactos. E05 agrega una capa
de casos, referencias y criterios; no sustituye el núcleo funcional.
El README previo se conserva en docs/README_HEREDADO_E04.md y los resultados
históricos continúan presentes. Los inventarios E01 anteriores son históricos,
no inventarios del contenido ampliado de E05.

## Matriz oficial

| Requisito | Archivo | Prueba ejecutada | Evidencia | Estado | Pendiente |
|---|---|---|---|---|---|
| Base E04 funcional | thermal_nd.py, diffusion_1d.py y tests heredados | 137 tests de base y suite final | pytest_base.txt y verificacion_03 | CUMPLE Y VERIFICADO | Ninguno |
| Exacta 1D | verification_e05.py: sine_mode/eigenvalues/run_case | exact_1d y geometría modificada | battery/exact_1d; JUnit E05 | CUMPLE Y VERIFICADO | Ninguno |
| Seno 2D | mismo módulo | exact_2d y caja no cuadrada | battery/exact_2d; pruebas nuevas/heredadas | CUMPLE Y VERIFICADO | Ninguno |
| Seno 3D | mismo módulo | exact_3d y 8×10×12 celdas en 1,2×0,9×1,6 m | exact_3d_modificado/ | CUMPLE Y VERIFICADO | Ninguno |
| Coordenadas y Dirichlet correctos | CartesianGrid.coordinates, face_temperature | centros iniciales distintos de caras y cara a T0 | test_configured_exact_modes y checks de caras | CUMPLE Y VERIFICADO | Ninguno |
| Errores y tolerancias | _check y métricas de run_case | L∞, L2 RMS/integral y FAIL deliberado | summary.json y precision_fail/ | CUMPLE Y VERIFICADO | Ninguno |
| Orden espacial | run_convergence | tres resoluciones, control temporal y tres dimensiones | parameter_sweep.json, spatial/ | CUMPLE Y VERIFICADO | Ninguno |
| Orden temporal | run_convergence | malla fija, pasos efectivos y referencia semidiscreta | temporal/ y JUnit | CUMPLE Y VERIFICADO | Ninguno |
| Energía adiabática | CartesianSystem.energy/power, caso energy | perfiles no uniformes y propiedades heterogéneas 1D/2D/3D | barrido de parámetros y battery/energy | CUMPLE Y VERIFICADO | Ninguno |
| Fuente uniforme | caso source | q_dot positivo, cero y negativo; cambios de rho/cp, volumen y tiempo | tests, barrido y fuente_negativa/ | CUMPLE Y VERIFICADO | Ninguno |
| Neumann | boundary_heat_rates y rama neumann | ambos signos en todas las caras, áreas no unitarias | tests heredados y 24 casos del barrido | CUMPLE Y VERIFICADO | Ninguno |
| Robin | resistencias centro-cara/película y rama robin | frío/caliente, h=0, cambios de h, superficies y esquina triple | JUnit, barrido y bordes_modificados/ | CUMPLE Y VERIFICADO | Ninguno |
| Estabilidad local | CartesianSystem.stable_dt, solve_nd | cerca del límite, exceso rechazado y diferentes h | stability/, inestabilidad_esperada.txt | CUMPLE Y VERIFICADO | Ninguno |
| CLI por caso/categoría/total | examples/run_e05.py | listar, selección, parámetros y protección de resultados | listar.txt, batería y pruebas CLI | CUMPLE Y VERIFICADO | Ninguno |
| Configuración editable y unidades | CaseConfig, load_configuration, lab.json | JSON, BOM, unidades, formas, NaN, claves y tipos inválidos | tests E05 y unidades_invalidas_esperadas.txt | CUMPLE Y VERIFICADO | Ninguno |
| Respuesta ante cambios | run_case y configuración | 60 combinaciones más variantes CLI | parameter_sweep.json | CUMPLE Y VERIFICADO | Ninguno |
| Reproducción y dependencias | pyproject.toml, lock y vendor/wheels | instalación vacía y pip check | logs de instalación y copia externa | CUMPLE Y VERIFICADO | Ninguno |
| Carpeta autónoma | check_e05_independence.py | copia física externa, entorno propio y verificación completa | e05_independencia_02/ | CUMPLE Y VERIFICADO | Ninguno |
| IFC heredado | geometry/foundation.ifc | lector y validador IFC | ifc_check.json, cinco IfcFooting/0 incidencias | CUMPLE Y VERIFICADO | Ninguno |
| Guía de laboratorio y preguntas | README y E05_DEMO.md | comandos y funciones contrastados con el código | documentación y ejecuciones CLI | CUMPLE Y VERIFICADO | Ninguno técnico |
| Simulación final/clima/hidratación/voxelización | Fuera del alcance | No se desarrollaron | Limitaciones declaradas | NO APLICA | Ninguno para E05 |

## Ejecuciones y conteos reales

- Base E04 recién instalada en E05: **137 aprobadas en 20,66 s**.
- Primera suite nueva: **59 aprobadas y 1 fallida en 5,27 s**. El XML se
  conserva en evidencias/e05_primeros_tests/pytest.xml.
- Se corrigió la selección temporal y la suite nueva pasó 60 pruebas en 5,13 s.
- Se añadió una regresión para parámetros de refinamiento y costo antes de
  asignar arrays: **61 pruebas E05**.
- Verificación final local: **198 aprobadas en 26,02 s**, 0 fallidas, 0 errores,
  0 omitidas. XML: 26,021 s.
- Repetición externa final: **198 aprobadas en 25,41 s**, sin fallos ni omisiones.
  XML: 25,414 s. También pasó toda la CLI y otro barrido de 60 combinaciones.

Desglose de la suite: test_diffusion_1d 62; test_e02 13; test_ifc 5;
test_thermal_nd 57; test_e05_verification 61. Se mantuvieron las 137 heredadas.
Las pruebas nuevas cubren la interfaz configurable, cajas no cúbicas, parámetros
reales, fuentes negativas y controles de rechazo, complementando la física ya
cubierta. No se infló la suite copiando tests de E04 con otro nombre.

Las propiedades JUnit de los tests científicos incluyen su reporte numérico:
geometría, configuración, pasos, Fourier, error, criterio y checks calculados.
Los JSON de casos conservan las referencias y tolerancias usadas. No se dedujo
PASS de la existencia de una figura o de que el proceso terminara sin excepción.

## Resultados científicos

Para cajas de 1 m por eje, 12 celdas/eje, k=2, rho=2400, cp=900,
amplitud 10 °C y tiempo final 10000 s, errores L∞: **0,000670749101 °C (1D)**,
**0,001213820492 °C (2D)** y **0,002314445944 °C (3D)**, frente a 0,03 °C.
La PDE continua se evalúa en centros y los valores de cara son Dirichlet T0.
El error L2 RMS también queda por debajo de L∞ en estos casos.

El estudio temporal no llama exacta continua a una referencia semidiscreta:
la usa exclusivamente para aislar el orden de Euler. En el barrido no cúbico:

| Dimensión | Órdenes espaciales | Órdenes temporales |
|---|---|---|
| 1D | 1,8973 / 1,9954 | 1,00030 / 1,00015 |
| 2D | 1,9170 / 1,9815 | 1,00046 / 1,00023 |
| 3D | 1,8801 / 1,9714 | 1,00055 / 1,00027 |

Son coherentes con órdenes aproximados 2 y 1, incluyendo efectos de la malla
gruesa. Se cuantifica contaminación temporal en spatial; errores a nivel de
redondeo o pasos efectivos que no disminuyen producen rechazo controlado.

La prueba adiabática heterogénea 3D conserva energía con residuo máximo
4,4793e-10 J. La fuente uniforme de 1000 W/m³ durante 10000 s en 1 m³ produce
**4,62962963 °C** y **10 millones de J**, con error térmico 2,4869e-14 °C.
Neumann −100 W/m² en z− aporta 1 millón de J, con error del orden de 3e-9 J.
Robin frío registra pérdida de 13455099,4154 J, respetando el balance con
residuo máximo 5,59e-9 J. Esas cifras son resultados del caso nominal concreto,
no valores impuestos como referencia de otros casos.

El barrido abarca 1D/2D/3D, cajas no cúbicas, cambios de k/rho/cp,
heterogeneidad, q_dot=−900/0/+900 W/m³, flujos ±135 W/m² en todas las caras,
h=0/12/250 y ambientes fríos/calientes. Las variantes CLI cambian además
resoluciones, duración, amplitud, inicial y paso. Los resultados responden a
esos cambios sin reescribir el solver.

Los controles deliberados **no son tests pytest fallidos**: la inestabilidad
debe retornar 2, la etiqueta de unidades mm debe retornar 2 y la precisión
insuficiente debe retornar 1 con un JSON marcado FAIL. El verificador confirma
el motivo y los códigos esperados; no cuenta un error arbitrario como éxito.

## Hallazgos y correcciones

| Hallazgo | Causa | Corrección y evidencia |
|---|---|---|
| Instalación offline inicial imposible | E04 no incluía el directorio de ruedas supuesto | Se descargaron las 24 versiones declaradas a vendor/wheels y se instalaron localmente; se conserva primer_intento.txt |
| Estudio temporal colapsaba a un paso | dt admisible era mayor que una duración corta al cambiar alpha/L² | Paso automático limitado a t_end/20, órdenes con dt efectivos y regresión que originalmente falló |
| Malla de convergencia no seguía n/shape | El primer borrador tenía tamaño de refinamiento separado | El refinamiento parte de cfg.shape y duplica todos sus ejes; prueba de 5×7 → 10×14 → 20×28 |
| Riesgo de reservar malla refinada excesiva | El costo se comprobaba después de construir el nivel fino | Se valida su número de celdas antes de construir arrays; caso n=64 3D rechazado en regresión |

No se detectó necesidad de corregir el esquema E04. Todos los cambios están
en P2_E05, sin reemplazar código funcional heredado ni modificar E04.

## Independencia y trazabilidad

La prueba externa creó una copia física de 681 archivos útiles en una carpeta
temporal fuera de Proyecto 2, sin enlaces, entornos ni cachés copiados. Instaló
un entorno nuevo usando exclusivamente las 24 ruedas de esa copia. El import
se comprobó bajo P2_E05_autonomo/src/mcoc_p2 y la verificación completa pasó.
La ruta temporal exacta y las salidas están en
`evidencias/e05_independencia_02/independence.json` y resultados/.

Las rutas absolutas que aparecen en logs históricos identifican dónde se
obtuvieron; no son archivos que E05 lea para funcionar. Los scripts y tests
calculan su raíz desde su propio archivo. No existe una dependencia de
P2_E04 para resolver, probar o regenerar resultados.

Referencias de evidencia vigente: **evidencias/e05/verificacion_03/** y
**evidencias/e05_independencia_02/**. Las corridas anteriores, incluida la
fallida, permanecen disponibles. Los JSON incluyen versión, comandos,
códigos de salida, fechas UTC y huellas de contenido.

## Cierre y limitaciones

**No quedan pendientes técnicos obligatorios identificados para E05.**
La guía está preparada para demostrar y modificar los casos; no certifica
el desempeño individual durante una actividad futura.

El modelo sigue limitado a cajas uniformes por eje, propiedades constantes
en tiempo, fuentes prescritas, condiciones constantes por cara y contacto
perfecto. Las referencias exactas son homogéneas. El IFC se conserva como
modelo separado y sus ocho capturas son antecedentes humanos, no una nueva
sesión Bonsai. No se implementaron funcionalidades de E06 ni del caso final.
La instalación se verificó en Windows x64/Python 3.12, sin afirmar portabilidad
ensayada en otros sistemas.
