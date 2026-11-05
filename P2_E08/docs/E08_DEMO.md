# E08 — Demo de laboratorio

> Publicación actual: [codex/e08](PUBLICACION_E08.md). Las referencias a un
> commit pendiente al final de esta guía describen la preparación previa.

## Abrir y ejecutar

Desde la raíz del proyecto, doble clic en INICIAR_E08.bat. Desde esta carpeta
también se puede usar iniciar.bat. Ambos abren Chrome, reutilizan el servidor
si está activo y muestran la referencia calculada. Dirección local:
http://127.0.0.1:8768/.

La configuración de referencia es configs/e08/demo.json. El cálculo sucede
en Python; el navegador recibe la geometría y temperaturas calculadas.
No hay cálculo térmico sustitutivo en JavaScript ni bibliotecas descargadas
desde internet.

## Secuencia solicitada por el ayudante

1. Mostrar el IFC real y la vista 3D. La referencia usa cinco IfcFooting,
   Δ=(0,275;0,275;0,1375) m y volumen voxelizado 633,18165625 m³.
2. Reportar error total 0,58034% frente a la malla IFC y errores por pieza.
   El pedestal alcanza 4,27767%; el total no garantiza igual precisión por pieza.
3. Pulsar **Rápida** para cambiar Δ a (0,55;0,55;0,275) m. Ejecutar y explicar
   el nuevo volumen/error: son estimaciones de la geometría, no errores del
   esquema térmico. El estudio cúbico conserva tres resoluciones.
4. Cambiar el inicio de una vertida en su fila, o escribir un intervalo y
   pulsar **Aplicar intervalo**. Cambiar una temperatura de colocación.
   Los valores se reflejan en el JSON; se guardan con cada ejecución.
5. Pulsar **Ejecutar en Python**. Esperar a que termine. El historial permite
   volver a la referencia o al caso modificado sin perder los resultados.
6. Llevar el selector temporal al inicio: solo están activas las vertidas
   ya colocadas. Avanzar a una hora de colocación para mostrar que la nueva
   vertida entra con su temperatura, sin reinicializar las anteriores.
7. Pulsar reproducir. La geometría activa crece y cambia el campo térmico.
   Las medias/máximas y los términos de energía se actualizan por fotograma.
8. Desmarcar una vertida y volver a marcarla. Se revela la geometría debajo;
   el resultado térmico y el balance no cambian. La visibilidad es solo del dibujo.
9. Cambiar **Temperatura / Vertida**, girar arrastrando y acercar con la rueda.
   La leyenda térmica solo aparece cuando los colores representan temperatura.
10. Descargar el escenario completo: inputs, IFC, solución NPZ, grilla,
    geometría del visor, reporte y cuatro figuras científicas.

## Comandos alternativos

Desde P2_E08, con su entorno Python activado:

```powershell
python examples/run_e08.py --output results/e08_nominal
python examples/run_e08.py --spacing 0.55 0.55 0.275 --interval-hours 3 --placement-offset 5 --output results/e08_modificado
python examples/run_e08.py --config configs/e08/demo.json --ifc geometry/foundation.ifc --output results/e08_otro
python scripts/verify_e08.py --output results/e08_verificacion
```

Usar carpetas nuevas: se rechaza sobrescribir resultados. --max-step limita
el paso solicitado; el integrador lo reduce según la estabilidad y los eventos.
--t-end-hours cambia la duración. El JSON controla también save_interval_s,
safety, fronteras por orientación y material/hidratación por evento.

## Qué explicar del código

Recorrido: examples/run_e08.py → e08.inputs → e08.pipeline → extracción IFC y
voxelización E07 → e08.solver.simulate → e07.coupling.MaskedAssembly.

El solver recibe una lista de eventos: no conoce IDs concretos, número de
vertidas, horas de inicio ni temperaturas del caso docente. Reconstruye las
conductancias al cambiar la máscara activa y conserva las temperaturas previas.
Las celdas futuras no aportan capacidad, conducción ni generación.

Entre eventos se usa Euler explícito para conducción y fronteras. La hidratación
se integra exactamente desde la curva prescrita en cada intervalo. Por tanto,
el calor acumulado no cambia artificialmente al variar el paso temporal.

El balance incluye el material que entra: ΔE=Q_h−Q_out+E_colocación. Si se
omitiera el último término, cada activación parecería crear energía. La
referencia energética es 0 °C por defecto; es un dato de referencia, no una
afirmación de energía termodinámica absoluta.

Hidratación funcional no significa calibrada: la fuente depende de la edad
real desde cada colocación. No hay dependencia de temperatura, Arrhenius,
clima real ni resistencia térmica de juntas. Los resultados son ilustrativos.
La máxima mostrada se obtiene de los fotogramas guardados; aumentar su frecuencia
permite observar mejor los máximos y los cambios rápidos.

## Evidencia y entrega

Referencia y caso modificado: evidencias/e08/nominal y modified. La interfaz
también fue probada con Δ más grueso, intervalo 3 h y una colocación de 27 °C.
El escenario y las capturas están en evidencias/e08/ui/.

Canvas solicita repositorio y commit. No se requiere informe ni texto adicional.
El SHA anterior de E07 no incluye esta entrega. La nueva publicación debe
declararse cuando se autorice el commit y push. La comprensión oral individual
la debe demostrar cada integrante.
