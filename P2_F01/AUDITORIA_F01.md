# Auditoría de cumplimiento F01

Se cotejan los requisitos transcritos en el encargo con el artículo y archivos publicados. La evaluación exacta de la pauta independiente y de los criterios internos sobre 10 puntos queda **NO VERIFICADA**. En los adjuntos disponibles se encontró la planilla F02, además del encargo F01. El anuncio de 20 puntos se conserva como referencia administrativa del encargo.

| Requisito | Estado | Ubicación y evidencia |
|---|---|---|
| Pregunta central, criterios docentes y alcance | OK | Resumen y §§1, 6 y 9. Criterio docente institucional identificado en los archivos E14. |
| PDF en español y fuente editable con dependencias | OK | PDF, `articulo.tex`, `figuras/` y comandos en `REPRODUCCION.md`. |
| Título, afiliación, asignatura, grupo, fecha y autoría | PARCIAL | Portada con autoría colectiva del Grupo 2. Pendiente confirmar nómina y orden de firmas. |
| Resumen de 150–250 palabras y 4–6 palabras clave | OK | Resumen de unas 190 palabras y cinco palabras clave. |
| Longitud orientativa de 4.000–6.000 palabras | OK | Aproximadamente 5.100 palabras de cuerpo según recuento de prosa, excluidas tablas, figuras, referencias y anexos. |
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
