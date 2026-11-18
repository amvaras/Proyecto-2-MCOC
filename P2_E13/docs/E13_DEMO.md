# E13 — Guía de demostración y defensa

**Conclusión:** No se encontró un plan factible bajo la familia y el modelo de incertidumbre evaluados. No se recomienda como factible el caso que se muestra en 3D. La comparación está condicionada a la familia y a los supuestos siguientes.

## Apertura y secuencia en vivo

Doble clic en [Iniciar E13.bat](../Iniciar%20E13.bat), o http://127.0.0.1:8713/. No abrir index.html directamente.

1. En **Decisión y riesgo**, explicar el objetivo: minimizar el fin físico D, sujeto al evento conjunto ≤5%. Mostrar tabla, cronogramas y diferencia entre construcción y simulación.
2. En **Configuración/Vertidas**, mostrar el IFC, GUID, cinco regiones y grilla 0,45×0,45×0,11 m. Hay 28.652 celdas ocupadas; vacíos y futuras no aportan capacidad, conducción o hidratación.
3. Mostrar las ocho fuentes Q por edad, en W/m³. Cada escenario usa una curva completa y común a todas las vertidas; no sortea fuentes entre celdas. Integrar Q·V en segundos, sin multiplicar por cemento.
4. Mostrar clima, metadata y pesos. Son historias auténticas de miembros GFS, sin sorteo horario ni desplazamiento de fechas.
5. Mostrar comparación y explicar por qué alargar una espera no garantiza bajar el diferencial: cambian la edad, las caras expuestas y el clima.
6. Abrir el caso ilustrativo 3D, elegir el instante del máximo, comparar modelo, corte XZ y clipping. Colorear por vertida y consultar una celda. Mostrar núcleo, cara reconstruida, mínimo S25 y ambiente en Temperaturas.
7. Cambiar un parámetro del plan. **Validar cronograma y estimar coste** calcula D en Python. **Calcular un escenario y mostrar 3D** produce campos nuevos, sin afirmar Pf. **Evaluar los 24 escenarios** calcula el riesgo y muestra progreso; requiere estimación vigente. Los avisos distinguen inputs nuevos de resultados anteriores.
8. Mostrar verificación, balances y controles. Reconocer los límites científicos y la ausencia de un ganador factible.

## Modelo físico y constructivo

t0 común: **jueves 19/11/2026 08:00 Chile, UTC−03 = 11:00 UTC**. Horizonte nominal 408 h, con máximos separados para las primeras 336 h y la extensión. La última vertida del plan más lento tiene ~348 h de edad al finalizar. No hay picos nominales en las últimas 24 h.

Balance por vóxel: ρcpV·dT/dt = suma Gij(Tj−Ti)+Q(edad)V−potencia exterior. Euler explícito usa estabilidad y eventos exactos. k=2, ρ=2400, cp=900 en SI. Interfaces activas: contacto perfecto; hacia una futura: superficie temporalmente expuesta.

Aire: q″=(Tc−Tamb)/[Δn/(2k)+Rm+1/h], h=8. Suelo resistivo a 18°C: R=0,4/1,5+0,025 m²K/W. Tablero+aislación dan Rm=0,76346. E12 retira laterales a 18,25 h; protegidos cubren exteriores laterales/superiores hasta 240 h, sin cubrir caras frente a vertidas futuras. Sin Arrhenius, viento o radiación explícitos.

Una bomba **hipotética de 50 m³/h**, suministro continuo con relevos y mínimo logístico 0,5 h entre capas. No son datos del profesor ni prueba de resistencia de juntas. Todos disponen de los mismos recursos; los protegidos suponen hormigón entregado a 12°C. No se modeló el equipo necesario para conseguirlo.

d_j=V_IFC,j/r; D=max(fin_j)−t0. Esperas y retraso inicial cuentan. La vertida única dura 12,738 h físicamente, aunque el solver la activa de una vez. Activar las cinco regiones a igual edad/temperatura conduce entre ellas sin convección interna y se verificó frente a su unión. La aproximación instantánea al inicio se contrasta con mitad/fin de colocación; no equivale a modelar el frente de llenado.

## Incertidumbre declarada

Se conserva [source_terms.txt](../data/hydration/source_terms.txt) auténtico y sus ocho curvas. SS tiene mejor ajuste reportado que 22A; no se acreditó que sean réplicas comparables. Se adoptan **pesos hipotéticos** 0,20 por SS y 0,05 por 22A, no probabilidades inferidas del RMSE. Se conserva el fin de registro; la cola exponencial continua τ=24 h añade calor solo a M1_SS (0,135648 MJ/m³). Se estudian τ=12/48 h. Edad cero coincide con colocación, aunque la ventana experimental comienza +2 h del registro original.

Clima: Open-Meteo, GFS 0,5°, adquirido 2026-11-17T18:42:24.021760+00:00; punto solicitado (−28,856102; −71,421831), grilla (−29; −71,5), elevación informada 145 m. Se preservan 31 miembros originales. Los null terminales se recortan: 818 horas válidas por historia, sin rellenar ni extrapolar.

Tres medoides, seleccionados por distancia L2 de temperatura en 600 h antes del cálculo térmico: **0, 13, 17**; pesos **15/31, 12/31, 4/31**. Conservan juntas las variables de cada miembro. La API interpola resolución nativa de varias horas a una hora; no es una estación local. Corrida y versión del modelo no fueron informadas. [Metadata original](../data/ensemble/metadata.json).

Se asume independencia material/clima: w=p·q. Los mismos 24 escenarios y pesos se usan en todos los planes. Falla = Tmax>70 **O** ΔTmax>20. Se suman pesos del OR, sin multiplicar marginales. Es enumeración exacta del modelo discreto, no Monte Carlo ni confiabilidad real del 95%. Se contrastan pesos uniformes, SS solamente, 22A solamente y miembros climáticos omitidos.

## Resultados realmente calculados

| Plan | D [h] | Tmax peor [°C] | ΔT peor [°C] | P(T>70) | P(ΔT>20) | Pf conjunta |
|---|---:|---:|---:|---:|---:|---:|
| unica | 12.738 | 64.8641 | 47.5922 | 0.00% | 100.00% | 100.00% |
| E12_referencia | 20.770 | 65.2217 | 48.0366 | 0.00% | 100.00% | 100.00% |
| protegido_rapido | 14.738 | 57.8114 | 38.8748 | 0.00% | 100.00% | 100.00% |
| propuesto_6h | 36.738 | 57.9677 | 39.3424 | 0.00% | 100.00% | 100.00% |
| protegido_lento_12h | 60.738 | 57.8980 | 39.5986 | 0.00% | 100.00% | 100.00% |


Los máximos son globales sobre celdas activas y todos los pasos. ΔT(t)=máxΩ T−mínS25 T en el mismo instante, incluyendo base y superficies temporales; excluye interfaces cerradas. S25 usa Tc−q″(Δn/2−0,025)/k sobre la frontera escalonada. No son dos sondas fijas ni precisión exacta a 25 mm.

Caso ilustrativo: **protegido_rapido / M4_SS_m17**, seleccionado para explicar el mecanismo, sin recomendación de cumplimiento. [Curvas](../figures/e13_temperaturas.png), [3D](../figures/e13_3d.png), [cortes](../figures/e13_secciones.png), [duración–riesgo](../figures/e13_duracion_riesgo.png).

Interfaz: API y ejecución Python verificadas; revisión manual de Chrome: **NO VERIFICADO: revisión visual manual pendiente**. No confundir PyVista offscreen con una sesión manual observada.

## Verificación, límites y consultas

No se escribió otro solver. Se conservaron las pruebas científicas previas. La superficie staircase sobreestima el área IFC ~18,21%; refinamiento y reescala de área son controles de sensibilidad, no cut-cell ni validación experimental. El modelo no acredita factibilidad constructiva, seguridad o ausencia de fisuración. [Estado y evidencia](E13_ESTADO.md).

Preguntas prioritarias al profesor:

1. ¿Son comparables las campañas SS/22A y qué pesos/distribución de material son defendibles?
2. ¿Qué capacidad, esperas por resistencia, temperaturas de entrega y protecciones se permiten realmente?
3. ¿Qué aproximación de S25/área acepta el curso para la decisión y qué verificación adicional exige?

El commit evaluado corresponde a la [etiqueta entrega-e13](https://github.com/amvaras/Proyecto-2-MCOC/commit/entrega-e13) del [repositorio del grupo](https://github.com/amvaras/Proyecto-2-MCOC).
