# E14 · Estado técnico comprobado

Infraestructura local implementada y verificada. No existe un plan factible entre los ocho evaluados. Clúster real NO VERIFICADO. Versión de entrega: [entrega-e14](https://github.com/amvaras/Proyecto-2-MCOC/tree/entrega-e14/P2_E14). La evidencia manual de navegador incluida en el ZIP corresponde a su autor: `results/verification/browser_e14.json`; las revisiones de este computador constan en la auditoría y la guía de demostración local.

| Plan | D [h] | H [h] | Tmax envolvente [°C] | ΔTmax [°C] | Pf exacta | MC / IC95% |
|---|---:|---:|---:|---:|---:|---|
| unica | 12.738 | 408 | 64.8641 | 47.5922 | 100.0% | 100.00% / [99.963; 100.000]% |
| E12_referencia | 20.770 | 408 | 65.2217 | 48.0366 | 100.0% | 100.00% / [99.963; 100.000]% |
| protegido_rapido | 14.738 | 408 | 57.8114 | 38.8748 | 100.0% | 100.00% / [99.963; 100.000]% |
| propuesto_6h | 36.738 | 408 | 57.9677 | 39.3424 | 100.0% | 100.00% / [99.963; 100.000]% |
| protegido_lento_12h | 60.738 | 408 | 57.8980 | 39.5986 | 100.0% | 100.00% / [99.963; 100.000]% |
| curado_rapido | 14.738 | 600 | 54.2919 | 32.4373 | 95.0% | 94.49% / [94.025; 94.929]% |
| curado_frio5 | 14.738 | 744 | 51.4987 | 28.8110 | 85.0% | 84.60% / [83.877; 85.302]% |
| etapas_templadas | 108.738 | 600 | 66.2437 | 42.9712 | 100.0% | 100.00% / [99.963; 100.000]% |

P(Tmax>70)=0 en los 24 átomos de todos los planes; la falla conjunta coincide aquí con exceder ΔT. No se modificaron umbrales, pesos, fuentes, suelo o conductividad para forzar cumplimiento.

El IC95% de curado_rapido [94,025%; 94,929%] no contiene su enumeración 95%. Es una realización posible con cobertura nominal del 95%, no una garantía para cada muestra; tampoco son intervalos simultáneos entre planes. Se mantuvieron N y semilla declarados. La inversión se comprobó además mediante sumas binomiales independientes a N=10000, sin reutilizar beta_cdf. La decisión usa la enumeración exacta del modelo de 24 átomos.

Ejecución: 120 casos base reutilizados, 72 nuevos a malla final en 601.927 s con dos procesos. Seis exploraciones previas dirigidas; 13 controles numéricos; seis solves de equivalencia secuencial/paralela; dos soluciones del caso ilustrativo (clima variable/control constante). MC: 10000 draws/plan, 80000 evaluaciones de indicadores, 192 inputs únicos reutilizados, cero solves térmicos adicionales en esa fase. No confundir draws con ensayos o solves nuevos.

Regresión integrada: **447 aprobadas, 0 fallidas, 0 errores, 0 omitidas**; 198.35 s. Se conservan las 428 pruebas heredadas y se añaden 19. pip check correcto. VTK genera 305 avisos de deprecación por asignación shape con NumPy 2.5; se documentan sin relajar pruebas o modificar dependencias instaladas. Campos del caso crítico: 2986 estados de integración y eventos, máximos y S25 recalculados desde arrays; fuente integrada independientemente y VTK verificados.

Malla final: 28652 celdas ocupadas, volumen 638,2233 m³. IFC 636,877718 m³; analítico 636,885036 m³. Área staircase 758,88 m² frente a 641,971763 m² IFC (+18,2108%). Refinamiento .30/.30/.055 m y dt 450 s dirigidos; reescala global de área separando aire/suelo. No se observó cambio de clase en los 13 controles, incluidos los tres más próximos al límite. Las definiciones cara 0 mm/centro de borde se guardan como diagnóstico, no sustituyen S25. No se demuestra convergencia global ni se obtiene una cota completa del error.

Caso crítico ilustrativo: curado_frio5/M4_SS_m00, H=744 h, retiro=600 h, máximo 51,4824°C a 213,5 h y ΔT=28,8110°C a 642,25 h (interior caliente frente a lateral frío). El balance global weather tiene residuo −4,20e−5 J frente a tolerancia 0,6393 J. Máximos globales del plan y de un escenario se distinguen en la tabla y el visor.

Figuras: 15 PNG, todas regeneradas desde datos locales, con pies y metadata de procedencia; `results/e14/figures.json` registra SHA. Campos completos solo para un caso E14 y la base E13 vigente. No cientos de exportaciones repetidas.

Mecanismo y decisiones: prolongar esperas con vertidas frías puede elevar el criterio global al añadir hormigón nuevo a 8°C frente al ya caliente. Curado prolongado y más aislación mejoran el diferencial antes del retiro, pero el enfriamiento exterior posterior sigue dominando. Se exploró suministro acotado 5–22°C, aislante existente 25–100 mm, esperas y retiro; sin recursos ilimitados. La literatura técnica [USBR](https://www.usbr.gov/damsafety/TechDev/DSOTechDev/DSO-12-02.pdf) describe control térmico mediante protección/enfriamiento; no calibra los espesores ni acredita la capacidad frigorífica usada en estos escenarios.

La búsqueda fue dirigida, no exhaustiva: ocho planes no prueban imposibilidad global. Quedan por contrastar con el profesor: significado global de S25/umbral, comparabilidad y pesos de SS/22A, mezcla real, dependencia térmica de hidratación, clima y capacidad de enfriamiento, juntas y contacto con suelo. No se recomienda un plan de obra sobre estas hipótesis.

Slurm: Bash -n y wrapper array real emulado localmente pasan; campos/semillas/métricas secuenciales y paralelos son exactamente iguales en tres inputs, seis solves sin cache. No hay host/cuenta/job/sacct remoto ni instalación Linux verificados. Esa ejecución requiere acceso al centro.

Integridad de la preparación original: 222 archivos de E13 comparados SHA256 antes/después, sin cambios; E01–E12 no recibieron escrituras. E14 importa su propio src y contiene físicamente datos/IFC/código, sin enlaces o rutas obligatorias a otra entrega. La preparación del ZIP no incluía publicación. La versión actual se identifica mediante la etiqueta `entrega-e14` y la rama `codex/e14`, con autorización del usuario. No se crearon ZIP o respaldos durante esta publicación.

Incidencias resueltas: agregación inicial duplicaba claves de extremos y falló después de completar los 192 inputs. Se corrigió el merge y se reagregaron filas verificadas sin repetir térmica; migración de huellas documentada en `aggregation_fix.json`. Un lector concurrente de progreso en Windows/OneDrive produjo WinError 5: se añadió reintento atómico acotado. La limpieza de un job QA encontró una carpeta vacía readonly de OneDrive: se corrigió el retiro individual con preflight y se completó el inventario. Una regresión intermedia tuvo 1 fallo/442 aprobadas por WinError 10053 en un rechazo HTTP: se consume el cuerpo acotado antes de validar origen/sesión, sin interpretar ni ejecutar inputs; los controles se conservan y la regresión final se repite. No se trataron estos fallos como casos térmicos seguros.

HTML: un lote real de 200 draws desde la interfaz obtuvo Pf=83%, 23 inputs únicos todos reutilizados. Un diagnóstico nuevo a .9/.9/.275 m y 744 h produjo dos soluciones en 17,985 s y pasó balance/VTK. Se observaron tabla exacta, advertencias de inputs, semillas, curvas, activación a t=0, slice y clipping; Chrome mostró WebGL sin error en el instante crítico 642,25 h. Los dos jobs propios se retiraron tras conservar inputs, métricas, checks y SHA en browser_e14/browser_cleanup; no se versionan variantes gráficas duplicadas. El conjunto oficial no se alteró.

Documentación técnica de continuidad: `E14_FORMULACION.md` y `E14_OPERACION.md`. Sin diapositivas, informe final ni dossier definitivo E15. Evidencia íntegra: `results/verification/closure_e14.json`, JUnit, fields_e14, numerics_e14, parallel, hpc y E13_integrity.
