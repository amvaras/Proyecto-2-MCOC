# E07 — Demostración y preparación oral

Grupo 2. Revisión del miércoles 4 de noviembre de 2026, 10:30–13:20.
Los comandos se ejecutan desde la raíz de P2_E07. Elegir destinos nuevos si
ya existen: las evidencias no se sobrescriben. Esta guía corresponde al código
ejecutado, no a un solver final futuro.

## Secuencia breve de laboratorio

Con el entorno instalado como indica el README:

```powershell
$pyE07 = '.\.venv\Scripts\python.exe'
& $pyE07 -X utf8 -B examples/run_e07.py --inspect-only --output results/e07_inspeccion_oral
& $pyE07 -X utf8 -B examples/run_e07.py --output results/e07_oral
$reporteE07 = Get-Content -LiteralPath 'results/e07_oral/summary.json' -Raw | ConvertFrom-Json
$reporteE07.nominal
$reporteE07.exterior
$reporteE07.interfaces
$reporteE07.timeline
$reporteE07.hydration
$reporteE07.assembly
& $pyE07 -X utf8 -B -m pytest tests/test_e07_geometry.py tests/test_e07_construction.py tests/test_e07_cli.py -q -p no:cacheprovider
```

Primero mostrar geometry.json: cinco GUID y VertidaID; después la figura de
vóxeles, el gráfico de volumen por resolución y la sección de interfaces.
Explicar el calendario ficticio de 0,5,10,15,20 horas. Mostrar la curva
preliminar y cerrar con el alcance exacto: se ensambla potencia en la máscara,
pero no se integra aún la temperatura transiente de la fundación.

El caso nominal usa Δ=(0,275;0,275;0,1375) m, 66×66×32 celdas,
60892 ocupadas, volumen 633,18165625 m³ y error 0,58034% frente a la malla IFC.
Los porcentajes por vertida importan: el pedestal tiene aproximadamente
4,27767% de error. No presentar el error total como garantía de cada pieza.

## Cambios que puede pedir el profesor

```powershell
# Resolución cúbica distinta y calendario más rápido:
& $pyE07 -X utf8 -B examples/run_e07.py --spacing 0.3 --interval-hours 3 --output results/e07_cambio_malla
# Caja anisótropa, margen, convección y potencial diferentes:
& $pyE07 -X utf8 -B examples/run_e07.py --spacing 0.4 0.3 0.275 --margin 0.1 --h 15 --ambient 12 --heat-mj-m3 40 --duration-hours 36 --output results/e07_cambio_fisica
# Vertidas simultáneas y periodo de inspección corto:
& $pyE07 -X utf8 -B examples/run_e07.py --interval-hours 0 --t-end-hours 1 --max-step 700 --no-plots --output results/e07_simultaneas
# ERROR esperado, código 2 por resolución inválida:
& $pyE07 -X utf8 -B examples/run_e07.py --spacing 0 --output results/e07_invalida
```

Para cambiar propiedades por vertida, copiar configs/e07/demo.json a un
archivo nuevo dentro de E07 y añadir en un evento, por ejemplo:

```json
{"pour_id":2,"activation_s":18000,"initial_C":19,
 "material":{"cp":1000},"hydration":{"H_vol_J_m3":40000000}}
```

Los valores omitidos heredan los parámetros globales. Usar `--config` con
ese archivo. La CLI admite `--ifc`, `--spacing` (uno o tres valores),
`--resolutions` (al menos tres distintos), `--margin`, `--interval-hours`,
`--h`, `--ambient`, `--heat-mj-m3`, `--duration-hours`, `--t-end-hours`,
`--max-step`, `--inspect-only`, `--no-plots` y `--output`.
Las unidades JSON son SI; los flags con hours y mj convierten explícitamente
a segundos y J/m³. El resto usa metros, °C y W/(m² K).

## Nueve preguntas oficiales

Las respuestas siguientes están pensadas para unos 20–40 segundos cada una.
El comando principal al que se refieren es `run_e07.py --output results/e07_oral`.
El JSON permite demostrar las cifras sin depender de la figura.

### 1. ¿Cómo decide si un vóxel pertenece al sólido?

«Evaluamos el centro físico de la celda contra la malla triangular extraída
del IFC. La caja envolvente solo descarta candidatos. Para las piezas convexas
reales comprobamos todos los semiespacios de sus caras; si una malla es cóncava
usamos la suma de ángulos sólidos. Los puntos de frontera tienen una regla
determinista. Por eso una esquina vacía dentro de la bbox no se convierte
automáticamente en hormigón.»

Física/geometría: se aproxima una región material por muestreo de centros.
Código: geometry.ClosedMesh.classify y voxel.voxelize.
Demostración: inspección IFC y caso nominal; test
`test_concave_mesh_winding_rejects_point_inside_bounding_box`.
Observar etiquetas 0–5 y el hueco del prisma en L correctamente exterior.
Límite: la malla debe ser simple y cerrada; no hay reparación general de
autointersecciones ni fracciones subcelulares de ocupación.

### 2. ¿Qué error produce la frontera staircase?

«Una superficie inclinada o curva se sustituye por peldaños cartesianos.
Eso cambia el volumen, la posición local del borde y el área que vería una
condición de convección. En este primer voxelizador usamos celdas completas,
sin recortarlas. Una figura visualmente parecida no demuestra precisión:
medimos volumen por pieza y total. Además, el área staircase puede mantener
sesgo de orientación aunque la malla se refine.»

Código: voxel.Voxelization.report y faces.exposed_faces.
Comando: caso nominal; abrir e07_fundacion_voxelizada.png y
e07_superficies_interfaces.png. Observar escalones y áreas por orientación.
Límite: no se ha corregido área efectiva para una predicción térmica final.

### 3. ¿Cómo cambia el error de volumen con Δx?

«El refinamiento representa detalles con más celdas, pero el error por centros
oscila al cambiar la alineación con las caras y con las cotas de vertida.
Aquí los errores totales para 0,55, 0,275 y 0,1375 metros son aproximadamente
0,7062%, 0,0499% y 0,2093%. El último aumenta. No afirmamos monotonía ni orden
dos: ese orden era del solver térmico. También revisamos cada vertida porque
los errores firmados pueden compensarse en el total.»

Código: voxel.voxelize y report; examples/run_e07.py, volume_study.
Comando: `--resolutions 0.55 0.275 0.1375`; observar e07_error_volumen.png.
Límite: solo tres resoluciones no prueban un orden asintótico universal.

### 4. ¿Cómo identifica una superficie exterior?

«Para cada celda sólida miramos seis vecinos. La cara es exterior si el vecino
está vacío o fuera de la grilla. Guardamos normal saliente, área, índice y
vertida. Para la geometría terminada usamos todas las piezas; durante la
construcción solo las activas. Por eso una cara frente a una vertida futura
puede estar expuesta hoy y convertirse después en una interfaz conductiva.
La clasificación geométrica no supone automáticamente contacto con suelo.»

Código: faces.exposed_faces. Comando: caso nominal; consultar exterior y timeline.
Observar 12736 caras finales y 747,93125 m²; future_exposed_faces cambia al activar.
Límite: top/bottom/lateral describe normal geométrica; la frontera física es
una hipótesis adicional. La demo adopta Robin uniforme, sin calibración.

### 5. ¿Qué ocurre entre dos vertidas?

«Si las dos celdas están activas intercambian calor por conducción, tengan
el mismo ID o IDs distintos. Un cambio de ID identifica una interfaz de
vertidas, pero no una frontera exterior. Suponemos contacto perfecto y sumamos
las resistencias de media celda para calcular la conductancia. El intercambio
entra en una celda y sale de la otra. Si la vecina aún no existe, no aporta
capacidad ni conducción y esa cara puede recibir una condición exterior.»

Código: faces.contacts y coupling.MaskedAssembly.
Comando: tests `test_two_active_pours_have_one_internal_interface_no_robin`,
`test_future_pour_becomes_exposed_then_internal` y
`test_perfect_contact_opposite_exchange_heterogeneous_conductivity`.
Observar una interfaz contada una vez y potencias opuestas.
Límite: no se implementó resistencia de junta ni transferencia imperfecta.

### 6. ¿Cómo se inicializa una vertida nueva?

«Cada vertida tiene un evento con hora, temperatura de colocación, material
y curva de hidratación. Al alcanzar esa hora activamos solo sus celdas,
asignamos su temperatura y comenzamos edad cero. No sobrescribimos las
temperaturas anteriores ni aplicamos un evento dos veces. Los eventos
simultáneos se procesan juntos. La secuencia temporal se subdivide para llegar
exactamente a cada evento; saltar uno provoca un rechazo. Nuestro calendario
es ilustrativo, no el calendario real de obra.»

Código: construction.PourEvent, ConstructionState.advance_to, time_grid y pour_age.
Comando: caso nominal y `--interval-hours 0`; observar timeline y construction.npz.
Límite: los pasos mostrados son del calendario; falta el integrador térmico
que evolucione las temperaturas y contabilice la energía del material entrante.

### 7. ¿Qué unidades tiene Qdot_h?

«Nuestra q_dot_h es una fuente volumétrica, en vatios por metro cúbico.
El potencial H_vol está en julios por metro cúbico y la tasa de fracción
liberada tiene unidades de inverso de segundo. Su producto es energía por
volumen y tiempo. Para obtener potencia de una celda multiplicamos por su
volumen. No se puede sumar directamente ese valor a un flujo superficial
en vatios por metro cuadrado ni a la temperatura.»

Código: hydration.AdiabaticCurve.source, q_dot_h y coupling.MaskedAssembly.power.
Comando: caso nominal; observar hydration_source_W_m3 y source_power_W.
Límite: el potencial de 64,8 MJ/m³ es ilustrativo; no está medido para Freirina.

### 8. ¿Cómo se relaciona una curva adiabática con generación de calor?

«En aislamiento y con capacidad constante, el balance volumétrico da
q_dot_h=rho·cp·dT_ad/dt. Elegimos una fracción de liberación suave entre cero
y uno. Su derivada es positiva durante la liberación y cero al agotarse.
La integral entrega exactamente el potencial H_vol. Con los parámetros
ilustrativos, el incremento adiabático potencial es 30 grados. Comprobamos
la derivada de la curva y una integral numérica independiente de la fuente.»

Código: hydration.AdiabaticCurve.degree, source, released y adiabatic_temperature.
Comando: caso nominal y tests de curva/derivada/potencial; observar
e07_hidratacion_preliminar.png. Límite: una curva adiabática prescrita no es
la evolución térmica de una fundación que pierde calor al ambiente.

### 9. ¿Cómo influye la temperatura en la hidratación?

«En el modelo implementado la fuente depende de la edad real desde el
vertido y de la curva prescrita; cambiar la temperatura no cambia la tasa.
Esa independencia se prueba y se declara. No incorporamos una ley de
Arrhenius ni edad equivalente sin datos. Si más adelante se usa una ley
cinética, debe emplear Kelvin, parámetros calibrados y conservación del
calor potencial. Hoy no afirmamos que ese acoplamiento térmico esté disponible.»

Código: hydration.q_dot_h y test_prescribed_curve_is_explicitly_temperature_independent.
Comando: ejecutar ese test con pytest `-k prescribed_curve`.
Observar la misma fuente para 10 y 70 °C a igual edad.
Límite: no se predice la aceleración física por temperatura.

## Salidas y navegación

- geometry.json/npz: GUID, propiedades, placements, vértices y triángulos reales.
- voxels.npz: etiquetas, ocupación, ejes y definición de grilla.
- faces.npz: índices, normales, áreas, clases y pares de interfaces.
- construction.npz: máscara activa, temperaturas de colocación, capacidad,
  fuente y potencia instantánea; no historia térmica integrada.
- summary.json: configuración, volumen por pieza, estudio, superficies,
  interfaces, eventos, edades, checks y balance de potencia.
- figures/: cinco figuras de resultados reales; calendario y curva marcados
  como ficticios/preliminares. No son capturas Bonsai.

Secuencia del código: run_e07 → read_pours → ClosedMesh → voxelize →
exposed_faces/contacts → ConstructionState → hydration_source → MaskedAssembly.
Para repetir toda la auditoría usar scripts/verify_e07.py; para demostrar
autonomía, scripts/check_e07_independence.py.
