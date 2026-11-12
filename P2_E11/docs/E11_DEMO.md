# E11 — Demostración desde el navegador

Abrir con doble clic en **Iniciar E11.bat**. La URL real es
**http://127.0.0.1:8711/**. El backend escucha solamente en 127.0.0.1.
No hace falta escribir comandos durante la evaluación.

## Secuencia oral (5–7 minutos)

1. Pulsar **Restaurar nominal**. En Resumen, mostrar IFC, grilla, temperaturas,
   duración y el identificador del resultado. Inicialmente son los oficiales,
   no una simulación recién ejecutada.
2. Entrar en **Meteorología**. Mostrar curva y metadata; consultar Respuesta
   original, Metadata JSON y CSV. Pulsar **Verificar datos meteorológicos**:
   Python valida hashes, unidades, muestras y cobertura con fecha de ejecución.
3. En **Configuración**, señalar h, inicio UTC y snapshot. Explicar Robin con
   la ecuación del Resumen. El baseline no utiliza viento ni radiación.
4. Cambiar h o el ambiente de control; en **Vertidas**, cambiar colocación o
   activación. La advertencia amarilla indica que los resultados aún pertenecen
   a la configuración anterior. Los campos vacíos de propiedades particulares
   heredan los valores globales.
5. Pulsar **Ejecutar simulación**. Se calculan dos escenarios en Python:
   pronóstico y constante, manteniendo iguales los demás inputs. Esperar
   Completado; no presentar una tarea en ejecución como PASS.
6. El visor muestra el resultado nuevo. Arrastrar para rotar; rueda para zoom;
   deslizador temporal para cambiar edad/estado. Ocultar una vertida modifica
   solo el dibujo. Las futuras pueden mostrarse grises, con temperatura indefinida.
7. Pulsar **Corte / Slice** y elegir XY, XZ o YZ y posición en metros. Después
   **Recorte / Clipping**, cambiar lado y posición; **Modelo completo** restaura.
   En un corte, colorear por Vertida ID ayuda a distinguir interfaces.
8. Pulsar una celda para obtener ID y temperatura de su centro; seleccionar una
   sonda para coordenadas, tipo, valor y curva temporal. Las sondas retiradas por
   un corte no se dibujan; la lista permite consultar su definición completa.
9. En **Temperaturas**, elegir extrema, núcleo/ambiente, caras, diferencia,
   centros de vertidas o sonda. El cursor consulta muestras reales, sin
   extrapolación. Comparar pronóstico y constante y abrir la diferencia espacial.
10. En **Verificación**, reimportar VTK y reconstruir balance; ejecutar tests E11
    y web; consultar fecha y contadores. La auditoría anterior está etiquetada.
    Comprobar bloqueo externo prueba la política CSP real del navegador.
11. **Abrir este resultado en PyVista nativo** abre otra vista del mismo VTK,
    útil si el ayudante pide específicamente PyVista. No es una captura estática.
12. Terminar con **Restaurar nominal** y resultados oficiales. Cerrar mediante
    el botón **Cerrar aplicación**; no cerrar el servidor mientras se use.

## Qué cálculos y datos usa

Se amplió el HTML existente de E08, con una sola aplicación vigente.
web/servidor.py valida inputs y ejecuta examples/run_e11.py en un subproceso.
Este llama a e11.pipeline.run y al integrador e08.solver.simulate existente.
No se integran temperaturas ni hidratación en JavaScript.

La grilla y ambos campos reales se adaptan a WebGL mediante web/viewer.js.
Vacío es transparente; la máscara temporal separa hormigón activo y futuro.
La conversión coincide con las matrices verificadas contra los VTI de PyVista.
Slice toma la temperatura constante por celda atravesada; clipping recorta
geométricamente sus cajas y dibuja las caras de corte. No interpola temperatura
a nodos ni modifica capacidades o conductancias.

Se evaluó [vtk.js](https://kitware.github.io/vtk-js/docs/develop_requirement.html).
Se conservó el componente [WebGL](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API)
local existente para evitar otro motor/bundle obligatorio. PyVista sigue
exportando y reimportando VTK, y se puede abrir desde el navegador.

Snapshot auténtico Open-Meteo forecast:
forecast-20261112T115248035648Z-d4253f02dc40. Adquirido 12-11-2026 11:52:48 UTC
(08:52:48 Chile); 72 horas, 12-11 00:00 UTC a 14-11 23:00 UTC.
Coordenadas docentes −28,856102; −71,421831; no se afirma estación de obra.
Metadata y SHA256 están junto al original. El CSV distingue UTC y
America/Santiago. [Fuente y API](https://open-meteo.com/en/docs).

Inicio nominal: 12-11-2026 12:00 UTC = 09:00 Chile.
Clima = inicio UTC + tiempo transcurrido; hidratación usa edad desde cada vertida.
Interpolación lineal sin extrapolación. Todas las simulaciones CLI/API bloquean
HTTP; la adquisición se mantiene separada y nunca reemplaza el snapshot oficial.

Para caras expuestas al aire:

    q″saliente = (Tcelda − Tamb(t)) / [Δn/(2k) + Rmoldaje(t) + 1/h]

h nominal 8 W/(m² K). Flujo en W/m² y potencia por cara A·q″ en W.
Aire más frío extrae calor; aire más caliente puede aportarlo.
Se conserva suelo a 18 °C, resistencia 0,4/1,5 + 0,025 m² K/W más media celda.
Moldaje lateral: tablero y aislación; retiro nominal a 18,25 h.
Interfaz entre dos vertidas activas: conducción de contacto perfecto, sin Robin.
Una vertida futura no aporta capacidad ni conducción.

Hidratación prescrita: ξ(a)=[1−cos(π·clamp(a/τ,0,1))]/2;
q̇h = Hvol·dξ/da en W/m³. Nominal Hvol=64,8 MJ/m³ y τ=48 h.
No considera aceleración térmica. Los cinco eventos son inputs ilustrativos,
no un calendario de obra calibrado.

Núcleo es una sonda en centro de celda; las caras superior/lateral se reconstruyen:
Tcara = Tcelda − q″saliente·Δn/(2k). No confundir con cara exterior del moldaje.
El núcleo tampoco es necesariamente el máximo global.

## Evidencia, límites y problemas de inicio

Nominal: 7730 vóxeles, 36 h, pico 41,263568 °C. El error de volumen de esta malla
es 0,9675 % total y 9,8294 % en pedestal. No se hizo una nueva convergencia térmica.
Dos corridas realizadas desde formularios Chrome reproducen exactamente los
arrays del cálculo Python directo: results/verification/web_equivalence.json.
La segunda cambia simultáneamente h, ambiente de control, T inicial y activación;
no atribuir toda su diferencia exclusivamente a h o al clima.

Los límites Tmáx ≤70 °C y ΔT ≤20 °C son referencias docentes; no certifican
seguridad ni fisuración. No hay calibración de hormigón/clima de obra, suelo
transiente, viento, radiación ni cinética Arrhenius. ParaView no se ejecutó.

Si no abre: comprobar Python 3.12, conexión para la primera instalación y que
el puerto 8711 no esté ocupado por otra aplicación. El lanzador explica errores,
reutiliza un servidor E11 de esta carpeta y mantiene su proceso mientras se usa.
El navegador necesita WebGL; se indica el motor disponible. Las dependencias
Python están en requirements-lock.txt y se instalan localmente, sin paquetes
globales ni CDN. El entorno activo se conserva fuera de la lista para versionar.

Cada corrida tiene ID, inputs efectivos, fecha, hashes, campos y VTK propios.
Hay un máximo de seis; descargar antes de retirar una mediante la interfaz.
La limpieza comprueba inventario SHA y conserva archivos desconocidos y oficiales.
Para Canvas, copie el SHA de la [etiqueta entrega-e11](https://github.com/amvaras/Proyecto-2-MCOC/commit/entrega-e11).

