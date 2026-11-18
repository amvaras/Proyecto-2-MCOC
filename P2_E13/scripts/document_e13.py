"""Actualizar guía de defensa y estado solo con resultados medidos de esta entrega."""
import re
from mcoc_p2.e11.pipeline import ROOT
from mcoc_p2.e13.weather import read
def main():
    s=read(ROOT/'results/e13/summary.json');cfg=read(ROOT/'results/e13/inputs.json')['configuration'];rows=read(ROOT/'results/e13/cases.json');red=read(ROOT/'data/ensemble/reduction.json');meta=read(ROOT/'data/ensemble/metadata.json')
    controls=read(ROOT/'results/verification/controls.json') if (ROOT/'results/verification/controls.json').exists() else {'status':'NO VERIFICADO','cases':[]}
    env=read(ROOT/'results/verification/environment.json');reg=env['final_regression'];rep=read(ROOT/'results/e13/representative/summary.json')
    browser=read(ROOT/'results/verification/browser.json') if (ROOT/'results/verification/browser.json').exists() else {'status':'NO VERIFICADO'}
    table='| Plan | D [h] | Tmax peor [°C] | ΔT peor [°C] | P(T>70) | P(ΔT>20) | Pf conjunta |\n|---|---:|---:|---:|---:|---:|---:|\n'
    for p in s['plans']:table+=f"| {p['plan']} | {p['D_h']:.3f} | {p['Tmax_C']:.4f} | {p['delta_C']:.4f} | {100*p['P_T']:.2f}% | {100*p['P_delta']:.2f}% | {100*p['P_joint']:.2f}% |\n"
    demo=f'''# E13 — Guía de demostración y defensa

**Conclusión:** {s['conclusion']}. No se recomienda como factible el caso que se muestra en 3D. La comparación está condicionada a la familia y a los supuestos siguientes.

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

Clima: Open-Meteo, GFS 0,5°, adquirido {meta['retrieved_at_utc']}; punto solicitado (−28,856102; −71,421831), grilla (−29; −71,5), elevación informada 145 m. Se preservan 31 miembros originales. Los null terminales se recortan: 818 horas válidas por historia, sin rellenar ni extrapolar.

Tres medoides, seleccionados por distancia L2 de temperatura en 600 h antes del cálculo térmico: **0, 13, 17**; pesos **15/31, 12/31, 4/31**. Conservan juntas las variables de cada miembro. La API interpola resolución nativa de varias horas a una hora; no es una estación local. Corrida y versión del modelo no fueron informadas. [Metadata original](../data/ensemble/metadata.json).

Se asume independencia material/clima: w=p·q. Los mismos 24 escenarios y pesos se usan en todos los planes. Falla = Tmax>70 **O** ΔTmax>20. Se suman pesos del OR, sin multiplicar marginales. Es enumeración exacta del modelo discreto, no Monte Carlo ni confiabilidad real del 95%. Se contrastan pesos uniformes, SS solamente, 22A solamente y miembros climáticos omitidos.

## Resultados realmente calculados

{table}

Los máximos son globales sobre celdas activas y todos los pasos. ΔT(t)=máxΩ T−mínS25 T en el mismo instante, incluyendo base y superficies temporales; excluye interfaces cerradas. S25 usa Tc−q″(Δn/2−0,025)/k sobre la frontera escalonada. No son dos sondas fijas ni precisión exacta a 25 mm.

Caso ilustrativo: **{rep['illustrative_plan']} / {rep['illustrative_scenario']}**, seleccionado para explicar el mecanismo, sin recomendación de cumplimiento. [Curvas](../figures/e13_temperaturas.png), [3D](../figures/e13_3d.png), [cortes](../figures/e13_secciones.png), [duración–riesgo](../figures/e13_duracion_riesgo.png).

Interfaz: API y ejecución Python verificadas; revisión manual de Chrome: **{browser['status']}**. No confundir PyVista offscreen con una sesión manual observada.

## Verificación, límites y consultas

No se escribió otro solver. Se conservaron las pruebas científicas previas. La superficie staircase sobreestima el área IFC ~18,21%; refinamiento y reescala de área son controles de sensibilidad, no cut-cell ni validación experimental. El modelo no acredita factibilidad constructiva, seguridad o ausencia de fisuración. [Estado y evidencia](E13_ESTADO.md).

Preguntas prioritarias al profesor:

1. ¿Son comparables las campañas SS/22A y qué pesos/distribución de material son defendibles?
2. ¿Qué capacidad, esperas por resistencia, temperaturas de entrega y protecciones se permiten realmente?
3. ¿Qué aproximación de S25/área acepta el curso para la decisión y qué verificación adicional exige?

El commit evaluado corresponde a la [etiqueta entrega-e13](https://github.com/amvaras/Proyecto-2-MCOC/commit/entrega-e13) del [repositorio del grupo](https://github.com/amvaras/Proyecto-2-MCOC).
'''
    docs=ROOT/'docs';docs.mkdir(exist_ok=True);(docs/'E13_DEMO.md').write_text(demo,encoding='utf8')
    cv=controls.get('decision_controls',[]);matrix='\n'.join(f"| {r['control']} | {r['plan']} | ≥{100*r['P_joint_lower_bound']:.4f}% | {'No factible probado en este control' if r['proves_infeasible'] else 'Requiere evaluación adicional'} |" for r in cv)
    status=f'''# E13 — Estado técnico

**{s['conclusion']}**. La implementación es funcional; el resultado no autoriza afirmar un plan de 95% de confiabilidad real. La [etiqueta entrega-e13](https://github.com/amvaras/Proyecto-2-MCOC/commit/entrega-e13) identifica el commit evaluado.

## Estudio oficial

{table}

Se ejecutaron {len(rows)} casos en la malla final, con una geometría reutilizada por proceso. Tiempo de enumeración registrado: {s['elapsed_s']:.2f} s. [Inputs y hashes](../results/e13/inputs.json), [casos completos](../results/e13/cases.json), [resumen](../results/e13/summary.json).

Caso crítico ilustrativo {rep['illustrative_plan']} / {rep['illustrative_scenario']}:

- Tmax={rep['global_maximum']['temperature_C']:.6f} °C a {rep['global_maximum']['time_h']:.3f} h, {rep['global_maximum']['utc']}; V4, XYZ (−0,225; −0,225; 2,365) m.
- ΔTmax={rep['global_delta25_maximum']['value_C']:.6f} °C a {rep['global_delta25_maximum']['time_h']:.3f} h, {rep['global_delta25_maximum']['utc']}; caliente V4 en (−0,225; −0,225; 2,365) m, {rep['global_delta25_maximum']['hot_temperature_C']:.6f} °C; S25 lateral x− V2 en (−8,975; −3,825; 1,045) m, {rep['global_delta25_maximum']['cold']['temperature_C']:.6f} °C.

Los peores Tmax de la tabla pueden corresponder a otro escenario. No sustituirlos por la sonda de núcleo ni por este único campo ilustrativo.

Cada caso registra configuración efectiva, curva, historia, pesos, malla, horizonte, edad, máximos/posiciones, métricas de 336 h, balance y estabilidad. Campos completos solo del caso crítico ilustrativo: results/e13/representative; VTK seleccionados en vtk/e13. No se guardaron 120 colecciones 3D. Resultados E12 son referencia de regresión, no resultados E13.

El calendario físico usa volúmenes IFC, no el volumen voxelizado dependiente de malla. La ocupación es por centros, preserva GUID/VertidaID y el volumen/área tienen errores distintos. El plan de menor duración dentro de la familia se seleccionaría entre los que cumplen Pf≤5%; si ninguno cumple, best_feasible=null. El ilustrativo desempata por menor peor diferencial, sin convertirlo en recomendación.

## Incertidumbre y controles

Estado de controles: **{controls['status']}**, {len(controls['cases'])} corridas dirigidas. [Evidencia](../results/verification/controls.json).

| Control | Plan | Cota inferior Pf | Interpretación |
|---|---|---:|---|
{matrix}

Una sola falla M4_SS/miembro0 pesa 0,20×15/31=9,6774%, más que 5%. Esta cota prueba inviabilidad en los controles indicados sin fingir que se recalcularon allí los 24 escenarios. No es un valor exacto de Pf refinado.

Se contrastan malla 0,30×0,30×0,055 m, paso 450 s, área aire/suelo reescalada a referencia IFC, capacidad 45/60 m³/h, cola τ=12/48 h y activación monolítica a mitad/fin. La reescala mantiene posiciones/volumen y deja caras frente a futuras sin escalar: sensibilidad global, sin precisión geométrica recuperada. La vertida única se compara con la unión real de etiquetas a igual campo inicial/material/fuente; no deja Robin entre regiones activas.

Los cambios de capacidad mantienen un recurso común y V/r. Si E12 no cabe sin solapamiento, se marca no admisible; no se modifica su calendario para hacerlo pasar. Los controles meteorológicos usan miembros auténticos omitidos, elegidos por distancia/medias meteorológicas, sin atribuirles nuevos pesos oficiales.

Como no hay calibración probabilística de probetas ni sitio, el resultado es análisis de escenarios con pesos hipotéticos. La independencia es un supuesto entre material y clima, con fuente totalmente correlacionada entre las cinco regiones de un escenario. No se representa dispersión de k, ρ, cp, h, suelo o ejecución: son incertidumbres omitidas. Tampoco se aplican intervalos binomiales a una enumeración finita.

## Verificación y estado observado

Suite integrada registrada: {reg.get('tests',0)} pruebas; {reg.get('failures',0)} fallidas; {reg.get('errors',0)} errores; {reg.get('skipped',0)} omitidas. Consultar environment.json y tests.xml para código de salida y tiempos. Las pruebas anteriores se conservan; las comprobaciones documentales/de rutas apuntan a los artefactos vigentes E13. No se relajaron tolerancias ni se retiraron pruebas para reducir el contador.

La verificación independiente de riesgo usa OR y math.fsum, comprueba escenarios comunes, fuente energética, balances, posiciones, activación y horizonte. El caso crítico se recalcula desde todos los campos y máscaras con la formulación independiente de S25 heredada de E12, y se reimporta VTK. scripts/verify_e13.py --reproduce repite casos críticos/menor margen sin red. Una figura no sustituye estas comprobaciones.

La misma aplicación HTML ofrece tabla, fuentes, clima/pesos, recursos/D, estimación previa, progreso y cálculo Python. Los tests de API comparan una evaluación real con Python directo. El diagnóstico individual produce campos nuevos, sin calcular Pf; la tabla mantiene procedencia y avisa si requiere recálculo. Ver browser.json para el alcance exacto de las interacciones manuales observadas. PyVista offscreen y exportación VTK son distintos de una sesión manual en ParaView.

Estado manual Chrome: **{browser['status']}**. Windows denegó activar la ventana y se pidió habilitar el escritorio. No se presentan capturas o clics E12 como evidencia E13. La conexión API, resultados gráficos y VTK se verificaron de forma independiente.

La regresión inicial tuvo tres fallos de adaptación: dos expectativas de identidad E12 y un validador que no decodificaba %20 en enlaces. Se corrigieron y la suite final terminó con código 0. Se añadió una prueba de τ=48 h y el verificador ahora usa el τ realmente configurado, sin alterar el solver ni las tolerancias físicas. Los avisos VTK/NumPy se conservaron.

| Capacidad | Estado |
|---|---|
| Fuente, clima trazable, máscaras, solver y balance | VERIFICADO numéricamente |
| Riesgo OR y comparación con escenarios comunes | VERIFICADO para el modelo discreto |
| Recursos/esperas y probabilidades reales de material | Supuestos; factibilidad y calibración NO VERIFICADAS |
| Controles espaciales, paso, área, colas y capacidad | VERIFICADOS en el alcance de controls.json |
| S25 exacta sobre IFC y convergencia completa | NO VERIFICADO |
| Backend API, exportación VTK y PyVista offscreen | VERIFICADO |
| Interfaz completa en escritorio | PARCIALMENTE VERIFICADO: API sí; Chrome y ParaView manual NO VERIFICADOS |
| Plan factible en la familia | Ninguno encontrado; no se afirma optimalidad global |

## Limitaciones y pendientes de defensa

- Confirmar con el profesor comparabilidad/pesos, recursos/esperas/temperatura y aceptación de S25.
- El sesgo de superficie (~18,21%) no desaparece por mejorar el volumen. Falta una representación de frontera más precisa y convergencia completa; los controles no constituyen cotas rigurosas de error IFC.
- Colocación lumped: duración física incluida, frente de llenado no resuelto. La temperatura de 12°C se impone como condición de suministro; su equipo/coste/preparación no se simulan.
- Forecast GFS de grilla ~50 km con incertidumbre y resolución interpolada; no observación local ni ensemble calibrado.
- Sin Arrhenius, viento/radiación explícitos, suelo transiente, tensiones, fisuración o certificación de obra.
- No se encontró un plan factible en esta familia. No se afirma optimalidad global ni se descartaron todas las alternativas constructivas posibles.
- La referencia de publicación es `refs/tags/entrega-e13`, en la rama `codex/e13`.

## Reproducción

Desde esta carpeta, instalar con scripts/install.ps1 (PyPI oficial). Usar examples/run_e13.py --output results/estudio_nuevo para otra enumeración; --resume solo acepta huella idéntica. scripts/prepare_e13_visual.py construye el único caso ilustrativo en destino nuevo. scripts/plot_e13.py regenera las figuras. scripts/verify_e13.py --reproduce valida los resultados locales sin descargar clima.

E12_integrity.json registra antes/después. El manifiesto final excluye .venv y temporales. La limpieza conserva datos científicos únicos y archivos desconocidos. No se crearon respaldos ni ZIP.
'''
    (docs/'E13_ESTADO.md').write_text(status,encoding='utf8');print('E13_DEMO words',len(re.findall(r'\S+',demo)));print('Documentos actualizados con datos medidos')
if __name__=='__main__':main()
