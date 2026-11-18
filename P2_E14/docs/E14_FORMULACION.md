# E14 · Modelo computacional e incertidumbres

Se reutiliza `e08/solver.py` mediante `e13/evaluator.py`: volúmenes finitos explícitos sobre centros IFC ocupados, contacto perfecto entre vecinos activos, capacidad rho·cp·V, hidratación integrada exactamente y Robin con resistencias en serie. Vacíos y vertidas futuras no aportan capacidad ni conducción. Cada activación inicializa temperatura y edad; los pasos alcanzan exactamente los eventos. `e14/model.py` adapta decisiones constructivas, sin segundo integrador.

| Variable | Unidad | Clasificación | Fuente / distribución | Dependencias y justificación | Influencia |
|---|---|---|---|---|---|
| Curva Q(edad) | W/m³; edad s | Epistemológica, categórica exploratoria | 8 curvas auténticas `data/hydration/source_terms.txt`; SS: 0,2 cada una; 22A: 0,05 cada una | Pesos hipotéticos E13, no frecuencias calibradas; una curva común a todas las vertidas de una realización | Potencia, energía y máximos |
| Historia de T aire | °C; tiempo UTC | Variabilidad predictiva representada por escenarios y error epistemológico | GFS 31 miembros, medoids 0/13/17; pesos 15/31,12/31,4/31 | Historia completa correlacionada en el tiempo; reducción L2 sobre 600 h, no selección por resultado térmico | Flujo exterior y S25 |
| Material × clima | 1 | Hipótesis epistemológica | Producto de los dos pesos; 24 átomos | Independencia asumida entre curva y miembro; no se asume independencia entre Tmax y ΔT | Pf conjunta |
| Cola de Q | h | Epistemológica, fijada | Exponencial continua, tau=24 h | Solo M1_SS termina con Q≠0; agrega 0,135648 MJ/m³; no muestreada | Energía tardía |
| Cero de edad | s | Epistemológica, fijada | Inicio de registro conservado, originalmente +2 h | No reconstruye primeras 2 h; reinicia en cada activación | Desfase de calor temprano |
| k, rho, cp | W/(m·K), kg/m³, J/(kg·K) | Epistemológicas, fijadas | 2; 2400; 900, base docente E13 | No se sustituyen por propiedades de probeta; sin distribución por falta de datos | Difusión y capacidad |
| Aire / suelo / contacto | W/(m²·K), °C, m²·K/W | Epistemológicas, fijadas | h=8; suelo 18°C; R suelo=.4/1.5+.025; contacto perfecto | Resistencias de media celda incluidas; sin radiación o viento explícitos | Pérdidas y gradientes |
| IFC / frontera / S25 | m, m², m³ | Aproximación geométrica y error numérico | IFC real; malla .45/.45/.11; reconstrucción lineal a 25 mm | Área staircase +18,2108%; sensibilidad, no distribución ni cut-cell | Superficie fría y clasificación |
| Colocación, espera, protección | °C, h, m, m³/h | Decisiones, no variables aleatorias | Configuración declarada por plan; una bomba hipotética 50 m³/h; T≥5°C; aislante≤.10 m | Recursos comunes acotados; enfriamiento y resistencia de juntas no acreditados | Calor inicial, curado y choque térmico |

No se añaden ensayos. Repetir una curva mediante Monte Carlo no crea observaciones experimentales independientes. La curva Q prescrita no depende de la temperatura del hormigón: no hay Arrhenius calibrado. Su aplicación a colocación de 5°C es una extrapolación conceptual que exige validación.

Fuente en W/m³ directamente; tiempo original en horas convertido a segundos. La integral lineal por tramos produce J/m³; no se multiplica por cemento ni por rho·cp. En SS las integrales son 88,1483 / 95,7152 / 94,1490 / 100,1661 MJ/m³. En 22A: 61,2120 / 82,4462 / 73,2888 / 73,6283. Los NaN posteriores a 163 h de 22A se conservan como fin de registro, sin interpolar datos inventados.

GFS fue adquirido realmente el 17/11/2026 18:42:24 UTC. Se usaron las 818 horas comunes válidas, sin rellenar el final nulo. t0=19/11/2026 11 UTC; hasta H=744 hay cobertura. El [API oficial de ensemble](https://open-meteo.com/en/docs/ensemble-api) distingue modelos, resolución y miembros: sus historias son predicciones, no clima observado ni evidencia específica del hormigón de Freirina.

## Estados límite y muestreo

Tmax=max sobre todos los centros activos y pasos. ΔTmax=max_t[max_Omega T(t)−min_S25 T(t)], en el mismo instante; incluye suelo y caras frente a vertida futura, excluye interfaces cerradas entre activos. No es diferencia entre dos sondas arbitrarias ni un modelo mecánico de fisuración.

gT=70−Tmax; gΔ=20−ΔTmax, ambos °C. Falla si gT<0 **O** gΔ<0; igualdad no falla. No se suman ni multiplican marginales. Enumeración: Pf=sum w_i I(falla_i), exacta dentro de los 24 átomos, sin IC Monte Carlo.

`sampling.py` utiliza PCG64 y `SeedSequence([semilla_maestra,id_realización])`. Cada ID recibe cuatro palabras uint32 distintas verificadas; su resultado no depende del orden o proceso. Un único banco se comparte entre planes para comparación emparejada. En MC se sortean átomos con los pesos declarados y se estima k/N **sin volver a ponderar**. Los resultados del mismo input determinista se reutilizan por hash físico.

`statistics.py` calcula IC bilateral Clopper–Pearson 95% para marginales y OR, mediante inversión de binomial/beta; pruebas contra sumas binomiales independientes. Siguiendo el [procedimiento exacto NIST](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm), se conservan los extremos k=0 y k=N. Para cero fallas, cota unilateral 95%=1−0,05^(1/N): N=59 permite una cota inferior al 5% bajo las hipótesis IID. No prueba Pf=0. Los IC de Pf(N) son puntuales, no una banda simultánea ni permiso para detener selectivamente cuando convenga.

Los draws son IID condicionales al modelo declarado; las historias dentro de cada draw mantienen dependencia temporal y entre vertidas. Los planes están correlacionados por banco común. Los IC no abarcan calibración de pesos, representatividad material/climática, discretización, S25 o sesgo de selección de planes; la enumeración elimina solamente error de muestreo del modelo discreto.

## Ejecución y almacenamiento

`workflow.py`: manifest inmutable, hash de configuración/kernel/versiones, mapping de realizaciones a inputs únicos y chunks disjuntos. `store.py`: cache con SHA de filas, validación de métricas y balances, locks exclusivos y reemplazo atómico. Un bloqueo persistente se informa; no se borran locks desconocidos. `io.py` reintenta brevemente lectores Windows/OneDrive sin truncar el destino. Un error numérico no es una realización segura: impide publicar Pf hasta completar/reintentar explícitamente.

Local: hasta cuatro procesos, grilla una vez por resolución/proceso, BLAS de un hilo. Web: un proceso y cancelación cooperativa después del input actual. Slurm: array de chunks, un CPU/tarea, sin MPI, outputs separados. [Job arrays](https://slurm.schedmd.com/job_array.html) y [sbatch](https://slurm.schedmd.com/sbatch.html) definen índice y envío; la emulación local no verifica un job remoto.
