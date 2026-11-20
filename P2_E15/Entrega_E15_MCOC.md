# E15 · Comparación probabilística de planes

**Proyecto 2 MCOC · Grupo 2 · viernes 20 de noviembre de 2026.**  
**Repositorio y commit de la evidencia:** [amvaras/Proyecto-2-MCOC · `969c8141f3daf4b9e6c7778f29bfe34d937e9fe5`](https://github.com/amvaras/Proyecto-2-MCOC/tree/969c8141f3daf4b9e6c7778f29bfe34d937e9fe5/P2_E14). Base E14: `f9d2faa150f9fdda007679386568326497f0d239`.

## Incertidumbres y diseño probabilístico

| Incertidumbre | Representación y fuente | Límite |
|---|---|---|
| Hidratación | Ocho curvas de potencia volumétrica, M1–M4 de las campañas SS y 22A. Peso por curva: 0,20 en SS y 0,05 en 22A. | Pesos de plausibilidad. Una curva común a todas las vertidas por realización. La cinética a 5 °C requiere validación. |
| Clima de Freirina | Tres historias enteras del ensemble GFS de Open-Meteo, representantes 0, 13 y 17 de 31 miembros. Pesos 15/31, 12/31 y 4/31. | Pronóstico de grilla sin calibración local. Conserva la dependencia temporal dentro de cada historia. |
| Dependencia material–clima | Producto de pesos, wₘₖ = pₘ qₖ, bajo independencia asumida por el grupo. | La independencia y la representatividad del conjunto requieren contraste. |
| Modelo térmico, S25 y operación | Propiedades, contacto, suelo y convección fijados. Controles separados de malla y paso. Refrigeración según parámetros nominales del ensayo. | Sin distribución para errores geométricos, parámetros fijos ni interrupciones de la refrigeración. |

Entradas y supuestos en `data/hydration/source_terms.txt`, `data/ensemble/reduction.json`, `docs/E14_FORMULACION.md` y `configs/f02/moderate_20.json`.

## Simulaciones y criterio de falla

Se verificaron **216 corridas térmicas nominales**: 192 de E14 (8 planes × 24 escenarios) y 24 de F02 para `moderate_20`. Los seis controles numéricos de F02 se contabilizan aparte. Los horizontes guardados varían entre 408 y 744 h; D mide colocación desde el inicio común hasta el fin de la última vertida. La tasa de 50 m³/h es un supuesto común de colocación.

Por corrida, Tmax es el máximo sobre el dominio activo y el tiempo. El diferencial usa el máximo activo menos el mínimo S25 del mismo instante y luego toma el máximo temporal. Se declara falla si Tmax > 70 °C **o** ΔTmax > 20 °C. Las marginales suman los pesos de sus respectivas excedencias; Pf = Σₛ wₛ · 1(Aₛ ∪ Bₛ) cuenta cada escenario fallido una sola vez. Por ejemplo, 15 de 24 casos fallidos en `curado_frio5` equivalen a 62,5 % sin ponderar y **85 %** con los pesos del proyecto.

## Comparación por enumeración ponderada

| Plan | P(Tmax>70) | P(ΔT>20) | Pf conjunta | D [h] | Impacto constructivo | Recomendación |
|---|---:|---:|---:|---:|---|---|
| `unica` | 0 % | 100 % | 100 % | 12,738 | Vertida única a 20 °C. | Descartar. |
| `E12_referencia` | 0 % | 100 % | 100 % | 20,770 | Cinco inicios cada 5 h; 18–22 °C. | Referencia. |
| `protegido_rapido` | 0 % | 100 % | 100 % | 14,738 | A 12 °C, espera de 0,5 h. | Descartar. |
| `propuesto_6h` | 0 % | 100 % | 100 % | 36,738 | A 12 °C, espera de 6 h. | Descartar. |
| `protegido_lento_12h` | 0 % | 100 % | 100 % | 60,738 | A 12 °C, espera de 12 h. | Descartar. |
| `curado_rapido` | 0 % | 95 % | 95 % | 14,738 | A 8 °C, 8 cm de aislación y retiro a 504 h. | Descartar. |
| `curado_frio5` | 0 % | 85 % | 85 % | 14,738 | A 5 °C, 10 cm de aislación y retiro a 600 h. | Referencia original de menor riesgo. |
| `etapas_templadas` | 0 % | 100 % | 100 % | 108,738 | Esperas de 24 h y colocación a 5–22 °C. | Descartar. |
| `moderate_20` | 0 % | 0 % | 0 % | 14,738 | A 5 °C, retiro escalonado y 29 ramales de agua. | Validar antes de adoptar. |

## Evolución de Pf(N) e intervalo de confianza

Se releyó el banco E14 de 10.000 sorteos categóricos por plan (semilla `20261119`), IID dentro de cada plan bajo la distribución discreta y compartido entre planes. Para cada prefijo se calculó Pf estimada como kₙ/N, sin volver a ponderar porque los pesos ya determinan el sorteo. Los sorteos reutilizan los indicadores térmicos. Para `moderate_20` se aplicó en E15 el banco guardado a sus 24 filas, sin ejecutar física nueva.

| Plan o grupo | N=100 | N=1.000 | N=10.000 | IC bilateral 95 % a N=10.000 |
|---|---:|---:|---:|---:|
| Seis planes E14 con Pf ponderada 100 % | 100 % | 100 % | 100 % | [99,9631 %; 100 %] |
| `curado_rapido` | 96 % | 93,4 % | 94,49 % | [94,0247 %; 94,9292 %] |
| `curado_frio5` | 86 % | 82,9 % | 84,60 % | [83,8775 %; 85,3023 %] |
| `moderate_20` | 0 % | 0 % | 0 % | [0 %; 0,0369 %] |

Se usó **Clopper–Pearson bilateral al 95 %**, mediante inversión binomial, con el nivel de E14 para mantener comparabilidad y tratar conteos extremos. Los intervalos son puntuales y cuantifican error de muestreo condicionado al modelo. Una realización del intervalo puede dejar fuera la referencia ponderada, como ocurre con el 95 % de `curado_rapido`. La enumeración es exacta para los 24 pesos fijados y carece de IC de muestreo. El IC de obra queda pendiente: requiere datos independientes de mezclas, clima y funcionamiento del sistema, calibrar el modelo conjunto y propagar esa incertidumbre con un diseño de validación definido de antemano.

## Recomendación provisional y decisión antes de la fecha final

Ningún plan original satisface Pf ≤ 0,05. Priorizaría **validar `moderate_20`**: es el único de los nueve planes publicados que pasa el filtro discreto. Su ΔTmax nominal es 19,158 °C y el mayor control fino dio 19,621 °C, margen de **0,379 °C**. El 0 % solo describe los escenarios evaluados. La instalación previa y el curado siguen fuera de D.

**Qué podría cambiar la decisión antes de la fecha final (TBD).** Primero, un diseño hidráulico y constructivo que confirme 20 °C y hasta 7,25 L/s, trazado entre armaduras, suministro a 5 °C y respuesta a una parada. Segundo, contrastar S25 con el IFC y refinar los casos cercanos al umbral. La falla de un solo caso SS con clima 0 pesa **9,677 %** y revertiría la clasificación. Tercero, registros locales de mezclas y clima podrían justificar nuevos escenarios o dependencias. Reponderar únicamente las 24 filas hoy sin fallas de `moderate_20` deja Pf en cero; cambiar el soporte o los indicadores sí puede cambiar la decisión.

**Trazabilidad:** `results/e14/enumeration/chunks/`, `results/e14/monte_carlo/{manifest,summary}.json` y `results/f02/{enumeration,controls,verification}.json`.
