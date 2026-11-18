# E13 — Estado técnico

**No se encontró un plan factible bajo la familia y el modelo de incertidumbre evaluados**. La implementación es funcional; el resultado no autoriza afirmar un plan de 95% de confiabilidad real. La [etiqueta entrega-e13](https://github.com/amvaras/Proyecto-2-MCOC/commit/entrega-e13) identifica el commit evaluado.

## Estudio oficial

| Plan | D [h] | Tmax peor [°C] | ΔT peor [°C] | P(T>70) | P(ΔT>20) | Pf conjunta |
|---|---:|---:|---:|---:|---:|---:|
| unica | 12.738 | 64.8641 | 47.5922 | 0.00% | 100.00% | 100.00% |
| E12_referencia | 20.770 | 65.2217 | 48.0366 | 0.00% | 100.00% | 100.00% |
| protegido_rapido | 14.738 | 57.8114 | 38.8748 | 0.00% | 100.00% | 100.00% |
| propuesto_6h | 36.738 | 57.9677 | 39.3424 | 0.00% | 100.00% | 100.00% |
| protegido_lento_12h | 60.738 | 57.8980 | 39.5986 | 0.00% | 100.00% | 100.00% |


Se ejecutaron 120 casos en la malla final, con una geometría reutilizada por proceso. Tiempo de enumeración registrado: 1186.97 s. [Inputs y hashes](../results/e13/inputs.json), [casos completos](../results/e13/cases.json), [resumen](../results/e13/summary.json).

Caso crítico ilustrativo protegido_rapido / M4_SS_m17:

- Tmax=57.788208 °C a 196.500 h, 2026-11-27T15:30:00Z; V4, XYZ (−0,225; −0,225; 2,365) m.
- ΔTmax=38.874760 °C a 306.000 h, 2026-12-02T05:00:00Z; caliente V4 en (−0,225; −0,225; 2,365) m, 55.698696 °C; S25 lateral x− V2 en (−8,975; −3,825; 1,045) m, 16.823935 °C.

Los peores Tmax de la tabla pueden corresponder a otro escenario. No sustituirlos por la sonda de núcleo ni por este único campo ilustrativo.

Cada caso registra configuración efectiva, curva, historia, pesos, malla, horizonte, edad, máximos/posiciones, métricas de 336 h, balance y estabilidad. Campos completos solo del caso crítico ilustrativo: results/e13/representative; VTK seleccionados en vtk/e13. No se guardaron 120 colecciones 3D. Resultados E12 son referencia de regresión, no resultados E13.

El calendario físico usa volúmenes IFC, no el volumen voxelizado dependiente de malla. La ocupación es por centros, preserva GUID/VertidaID y el volumen/área tienen errores distintos. El plan de menor duración dentro de la familia se seleccionaría entre los que cumplen Pf≤5%; si ninguno cumple, best_feasible=null. El ilustrativo desempata por menor peor diferencial, sin convertirlo en recomendación.

## Incertidumbre y controles

Estado de controles: **PASS**, 29 corridas dirigidas. [Evidencia](../results/verification/controls.json).

| Control | Plan | Cota inferior Pf | Interpretación |
|---|---|---:|---|
| fine_mesh | unica | ≥9.6774% | No factible probado en este control |
| fine_mesh | E12_referencia | ≥9.6774% | No factible probado en este control |
| fine_mesh | protegido_rapido | ≥9.6774% | No factible probado en este control |
| fine_mesh | propuesto_6h | ≥9.6774% | No factible probado en este control |
| fine_mesh | protegido_lento_12h | ≥9.6774% | No factible probado en este control |
| area_rescale | unica | ≥9.6774% | No factible probado en este control |
| area_rescale | E12_referencia | ≥9.6774% | No factible probado en este control |
| area_rescale | protegido_rapido | ≥9.6774% | No factible probado en este control |
| area_rescale | propuesto_6h | ≥9.6774% | No factible probado en este control |
| area_rescale | protegido_lento_12h | ≥9.6774% | No factible probado en este control |

Una sola falla M4_SS/miembro0 pesa 0,20×15/31=9,6774%, más que 5%. Esta cota prueba inviabilidad en los controles indicados sin fingir que se recalcularon allí los 24 escenarios. No es un valor exacto de Pf refinado.

Se contrastan malla 0,30×0,30×0,055 m, paso 450 s, área aire/suelo reescalada a referencia IFC, capacidad 45/60 m³/h, cola τ=12/48 h y activación monolítica a mitad/fin. La reescala mantiene posiciones/volumen y deja caras frente a futuras sin escalar: sensibilidad global, sin precisión geométrica recuperada. La vertida única se compara con la unión real de etiquetas a igual campo inicial/material/fuente; no deja Robin entre regiones activas.

Los cambios de capacidad mantienen un recurso común y V/r. Si E12 no cabe sin solapamiento, se marca no admisible; no se modifica su calendario para hacerlo pasar. Los controles meteorológicos usan miembros auténticos omitidos, elegidos por distancia/medias meteorológicas, sin atribuirles nuevos pesos oficiales.

Como no hay calibración probabilística de probetas ni sitio, el resultado es análisis de escenarios con pesos hipotéticos. La independencia es un supuesto entre material y clima, con fuente totalmente correlacionada entre las cinco regiones de un escenario. No se representa dispersión de k, ρ, cp, h, suelo o ejecución: son incertidumbres omitidas. Tampoco se aplican intervalos binomiales a una enumeración finita.

## Verificación y estado observado

Suite integrada registrada: 428 pruebas; 0 fallidas; 0 errores; 0 omitidas. Consultar environment.json y tests.xml para código de salida y tiempos. Las pruebas anteriores se conservan; las comprobaciones documentales/de rutas apuntan a los artefactos vigentes E13. No se relajaron tolerancias ni se retiraron pruebas para reducir el contador.

La verificación independiente de riesgo usa OR y math.fsum, comprueba escenarios comunes, fuente energética, balances, posiciones, activación y horizonte. El caso crítico se recalcula desde todos los campos y máscaras con la formulación independiente de S25 heredada de E12, y se reimporta VTK. scripts/verify_e13.py --reproduce repite casos críticos/menor margen sin red. Una figura no sustituye estas comprobaciones.

La misma aplicación HTML ofrece tabla, fuentes, clima/pesos, recursos/D, estimación previa, progreso y cálculo Python. Los tests de API comparan una evaluación real con Python directo. El diagnóstico individual produce campos nuevos, sin calcular Pf; la tabla mantiene procedencia y avisa si requiere recálculo. Ver browser.json para el alcance exacto de las interacciones manuales observadas. PyVista offscreen y exportación VTK son distintos de una sesión manual en ParaView.

Estado manual Chrome: **NO VERIFICADO: revisión visual manual pendiente**. Windows denegó activar la ventana y se pidió habilitar el escritorio. No se presentan capturas o clics E12 como evidencia E13. La conexión API, resultados gráficos y VTK se verificaron de forma independiente.

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

## Revisión de publicación del 18 de noviembre

La [auditoría del paquete](../results/verification/auditoria_publicacion.json)
contrasta el enunciado recibido con los archivos y resultados de E13.
Los 120 casos pasan la auditoría independiente de riesgo, fuente, balances,
estabilidad y horizonte. Se reprodujeron exactamente el caso crítico
M4_SS/m17 y el caso de menor diferencial M1_22A/m13 del plan protegido rápido.
La suite nueva aprobó 427 pruebas y detectó una expectativa documental de
publicación pendiente. Tras admitir la etiqueta de entrega, esa prueba volvió
a pasar. Las 428 comprobaciones quedan satisfechas en esas dos ejecuciones.

El archivo de fuentes de este ZIP corresponde a la recuperación corregida
que describe su cabecera. Su SHA-256 difiere del archivo usado en E12.
La API local expone correctamente las ocho fuentes, tres historias y 24
escenarios. La comprobación visual quedó pendiente al rechazarse el acceso
del navegador a la página local durante esta revisión.
