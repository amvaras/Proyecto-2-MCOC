# Auditoría de cumplimiento F01

## Evaluación según la sección 3 de la rúbrica F01

Cotejo de los siete criterios y ponderaciones oficiales indicados en la solicitud de revisión. Los puntajes son estimaciones académicas razonadas de esta revisión del PDF final. Los descuentos reflejan brechas concretas de evidencia o alcance y pueden diferir de la evaluación docente.

| Criterio oficial | Estimación / máximo | Evidencia en el PDF final | Descuento razonado y mejora de mayor impacto |
|---|---:|---|---|
| 1. Problema, datos reales y trazabilidad | 1,10 / 1,20 | §§1–2, pp. 1–5. Fig. 1 y Tabla 1 (p. 3), Tabla 2 (p. 4), Fig. 2 (p. 5). Anexo A (p. 18), con los tres SHAs y rutas de insumos. | −0,10. Los registros brutos y el protocolo íntegro de probetas permitirían verificar la inversión, en especial las primeras dos horas. |
| 2. Continuo, ecuaciones, parámetros, bordes y fundamento | 1,85 / 2,00 | §3, pp. 4–7. Balance y Fourier, ecs. (1)–(2), p. 5. Ley de borde, Tabla 3, resistencias y advección del agua, ecs. (3)–(4), p. 6. Fig. 3, p. 7. §4 explicita la forma discreta de Robin. | −0,15. La equivalencia suelo–reservorio y las resistencias locales de tubo requieren caracterización. Prioridad alta: medir propiedades y contrastar el intercambio local con una referencia instrumental o radial. |
| 3. Discretización, algoritmos y verificación | 1,60 / 1,80 | §§4–5, pp. 7–9. Ecs. (5)–(6) de volumen finito y conductancias (p. 7), algoritmo, prueba adiabática y balance del caso gobernante (p. 8); controles separados (Tabla 4, p. 9). | −0,20. Tres escenarios con controles finos y ajuste local S25 dan evidencia parcial. Prioridad alta: resolver el borde real y extender la verificación espacial antes de certificar margen. |
| 4. Incertidumbre, evento conjunto y limitaciones | 1,40 / 1,50 | §6, pp. 9–10. Ecs. (8)–(11), p. 10. Pesos, máximos simultáneos, unión, sensibilidad y distinción entre probabilidad nominal e IC condicional. Fig. 8, p. 14. | −0,10. Los pesos de material, la independencia y la confiabilidad del equipo carecen de estimación local. Ampliar los escenarios con datos de mezcla, meteorología y operación. |
| 5. Comparación, búsqueda temporal y recomendación | 1,70 / 1,80 | §§6–7, pp. 9–14; ec. (7), p. 9; cribado de 24–96 h, p. 10; Tablas 5–6 y Fig. 4, pp. 11–12; conclusión, §9, p. 16. El contraste de h 336 se deriva de E14. | −0,10. La búsqueda probabilística se restringe a nueve planes; las esperas largas del cribado tienen un solo escenario cada una. Ampliar la búsqueda en otras particiones y combinaciones de esperas si hay capacidad y restricciones de obra definidas. |
| 6. Discusión, monitoreo y contingencias | 0,75 / 0,80 | §8, pp. 14–16. Propone responsables, sensores, adquisiciones, alertas y acciones ante desviaciones; §9, p. 16, especifica condiciones para aplicar la recomendación. | −0,05. La ubicación de sensores y los umbrales operativos siguen como propuestas. Un piloto permitiría definir cobertura, tolerancias y respuestas efectivas. |
| 7. Escritura, figuras, referencias y reproducibilidad | 0,85 / 0,90 | Portada, p. 1; Figs. 1–8 con unidades y pies; bibliografía, p. 17; anexos A–B, p. 18. Fuente, figuras, CSV y comandos bajo `P2_F01/`. | −0,05. Completar la nómina confirmada y enriquecer la referencia de laboratorio con su documento primario cuando esté disponible. |
| **Total estimado** | **9,25 / 10,00** | | |

Los criterios con mayor pérdida estimada son discretización y verificación (0,20), y modelo continuo y fundamento (0,15). La revisión resuelve con evidencia archivada la cuantificación del intercambio, el cierre numérico y la comparación de horizontes. Permanecen como trabajo adicional la verificación global de S25 y la caracterización térmica e hidráulica. La constancia del Centro de Escritura sigue pendiente.

## Lista de comprobación detallada

| Requisito | Estado | Ubicación y evidencia |
|---|---|---|
| Pregunta central, criterios docentes y alcance | OK | Resumen y §§1, 6 y 9. Criterio docente institucional identificado en los archivos E14. |
| PDF en español y fuente editable con dependencias | OK | PDF, `articulo.tex`, `figuras/` y comandos en `REPRODUCCION.md`. |
| Título, afiliación, asignatura, grupo, fecha y autoría | PARCIAL | Portada con autoría colectiva del Grupo 2. Pendiente confirmar nómina y orden de firmas. |
| Resumen de 150–250 palabras y 4–6 palabras clave | OK | Resumen de unas 190 palabras y cinco palabras clave. |
| Longitud orientativa de 4.000–6.000 palabras | OK | Aproximadamente 5.500 palabras de cuerpo según recuento de prosa, excluidas tablas, figuras, referencias y anexos. |
| Nueve secciones ordenadas, referencias y anexos | OK | §§1–9, bibliografía y anexos A–B. |
| Contexto científico, marco bibliográfico y naturaleza docente de límites | OK | §1, referencias ACI, CIRIA y E14. |
| Coordenadas, cotas IFC, volúmenes, vertidas y flujo de mallado | OK | §2, Figura 1. Coordenadas de consulta y nodo devuelto diferenciados. Las cotas del IFC son locales. |
| Tabla de parámetros con clasificación y unidades | OK | Tabla 1 y Tabla 3 para parámetros de borde. |
| Ocho fuentes, unidades, inversión, conversiones y energías | OK | §2, Tabla 2 y Figura 2. Integración trapezoidal verificada directamente en el archivo archivado. |
| Protocolo completo y series brutas de laboratorio | NO VERIFICADO | §2 registra las condiciones conocidas de la inversión. Faltan datos de laboratorio independientes y trazabilidad de las dos horas iniciales. |
| Producto meteorológico, fecha, zona, modelo, variables, cobertura y reducción | OK | §2, Figura 2. Metadatos y reducción archivados. La versión interna de GFS y hora de corrida quedan sin identificar en los metadatos. |
| Balance, Fourier, activación, bordes, suelo, interfaces e intercambio con tubos | OK | §3, Tabla 3, ecuaciones de conservación e intercambiador. |
| Volúmenes finitos, Euler, estabilidad, eventos y algoritmo de máximos simultáneos | OK | §4; capacidades, conductancias, reconstrucción S25 y pasos del algoritmo. |
| Costo computacional y entorno | PARCIAL | §4 y anexo. Se citan mediciones locales E14; no se dispone de ejecución en clúster real ni medición comparable de rendimiento de F02. |
| Caso de verificación y balance energético | OK | §5, prueba de fuente uniforme adiabática y contabilidad de 30 casos F02. |
| Refinamiento espacial y temporal separado, efecto sobre clasificación | OK | §5, Tabla 4. Controles dirigidos sobre tres escenarios de F02. |
| Cota global de error, S25 en frontera IFC y validación independiente | PARCIAL | §5. La exploración fina conserva 19,621 °C y documenta la diferencia de profundidad en el lateral IFC. Sin cota global, calibración de parámetros in situ ni validación experimental. |
| Optimización, restricciones, estados límite, unión y pesos sin redondeo | OK | §6; igualdad geométrica; supuestos de recursos, juntas y tecnología explicitados. |
| Semillas, número de casos, Monte Carlo, convergencia e intervalos | OK | §§6–7, gráfico de prefijos Monte Carlo, archivos de enumeración y banco. El intervalo se refiere al muestreo condicional. |
| Sensibilidad probabilística y alcance de optimalidad | OK | §6, cambios de indicador y masa fuera de soporte. §9 limita la selección a los planes comparados. |
| Origen temporal, cobertura y extensiones de evaluación | OK | §6 y Tabla 5. El artículo conserva los distintos horizontes de la evidencia y explica la monotonía del evento al extender la misma trayectoria. |
| Vertida única, propuesta, más rápida y más lenta | OK | §7, Tablas 5–6, nueve planes con cronogramas y fallas. |
| Curvas de núcleo y superficie, cortes, campo 3D y duración frente a Pf | OK | §7, figuras producidas desde campos y métricas publicados. Las curvas son extremos móviles simultáneos. |
| Instantes y coordenadas de los extremos | OK | §7, `extremos_por_plan.csv` y `escenarios_f02.csv`. |
| Duración, máximos, pesos y probabilidad final coherentes con defensa | OK | §§5–7 y 9; comparación de CSV F02 y resultados por átomo. Recomendación de 14,738 h con 0% nominal y control espacial de 19,621 °C. |
| Discusión física y control operativo | OK | §8, protocolo de suministros, tuberías, medición, alertas, contingencias y responsabilidades. Propuestas de campo distinguidas de condiciones simuladas. |
| Acreditación constructiva, hidráulica y operacional | NO VERIFICADO | §§8–9. Pendientes piloto, juntas, armaduras, recursos, instrumentación y confiabilidad del sistema. |
| Bibliografía y reproducción | OK | Referencias, anexo A y `REPRODUCCION.md`; SHAs, configuraciones, semillas, datos y comandos. |
| Coherencia con SHA de defensa | OK | Rama basada en `969c8141f3daf4b9e6c7778f29bfe34d937e9fe5`; cambios confinados a `P2_F01/`. |
| Discrepancia de fecha y autorización del Centro de Escritura | PARCIAL | Anexo B. «Viernes 23 de noviembre de 2026» se conserva como texto de la pauta transcrita. El día calendario es lunes. Fecha, hora y constancia de aprobación pendientes. |

## Comprobaciones de cierre

- Se ejecutó `verify_f02.py` con una copia de la evidencia publicada. El verificador devolvió `PASS` para 24 casos nominales y seis controles. Comprobó la huella del kernel, la huella de campos, la suma de pesos, 744 h de cobertura sin cola de clima, la clase de cada caso y la geometría local de los puntos de control. El residuo absoluto máximo observado fue de 0,0001793 J. Esta comprobación relee y verifica resultados archivados.
- Se compiló con pdfTeX, se revisó el PDF renderizado y se corrigieron los desbordamientos de las referencias de procedencia y la composición de las figuras.

- En la revisión se reagregó el peso excedido hasta h 336 a partir de los campos `first336_Tmax_C` y `first336_delta_C` de los 192 casos E14. Se verificó el contraste contra los 24 pesos por plan. Este análisis derivado conserva la enumeración y la tabla oficial de F02.
- Se compiló el PDF revisado, se cotejaron páginas y números contra las referencias de LaTeX y se inspeccionaron todas las páginas renderizadas. La rama conserva la autoría Grupo 2 y el SHA de defensa.
