# E14 · Conjunto científico definitivo para preparar F02

Documento técnico de continuidad. Sin diapositivas, dossier E15 o informe final.

| Plan | Colocación D [h] | Horizonte H [h] | Tmax [°C] | ΔTmax [°C] | Pf exacta | MC / IC95% |
|---|---:|---:|---:|---:|---:|---|
| unica | 12.738 | 408 | 64.8641 | 47.5922 | 100.0% | 100.00% / [99.963%; 100.000%] |
| E12_referencia | 20.770 | 408 | 65.2217 | 48.0366 | 100.0% | 100.00% / [99.963%; 100.000%] |
| protegido_rapido | 14.738 | 408 | 57.8114 | 38.8748 | 100.0% | 100.00% / [99.963%; 100.000%] |
| propuesto_6h | 36.738 | 408 | 57.9677 | 39.3424 | 100.0% | 100.00% / [99.963%; 100.000%] |
| protegido_lento_12h | 60.738 | 408 | 57.8980 | 39.5986 | 100.0% | 100.00% / [99.963%; 100.000%] |
| curado_rapido | 14.738 | 600 | 54.2919 | 32.4373 | 95.0% | 94.49% / [94.025%; 94.929%] |
| curado_frio5 | 14.738 | 744 | 51.4987 | 28.8110 | 85.0% | 84.60% / [83.877%; 85.302%] |
| etapas_templadas | 108.738 | 600 | 66.2437 | 42.9712 | 100.0% | 100.00% / [99.963%; 100.000%] |

**Ninguno de los ocho planes evaluados cumple Pf≤5%.** No se elige ni recomienda un plan factible. D es tiempo físico de colocación; H incluye hidratación, curado y enfriamiento posterior. Los cinco casos E13 ya fallaban a 408 h; ampliar su horizonte no puede borrar ese máximo previo.

192 inputs únicos: 120 reutilizados de la base y 72 calculados en E14. Esta revisión verifica resultados guardados; no repite esos solves. N=10000 por plan es remuestreo categórico emparejado, no 10000 ensayos experimentales. P(Tmax>70)=0 en todos los átomos; la falla conjunta coincide aquí con superar ΔT=20. Estados límite: gT=70−Tmax, gΔ=20−ΔTmax; OR estricto para valores negativos.

Las ocho curvas auténticas, el ensemble GFS original y sus tres historias derivadas se conservan localmente. Pesos materiales hipotéticos: SS 0,2 cada una; 22A 0,05 cada una. Pesos climáticos 15/31,12/31,4/31; independencia material/clima asumida. No hay calibración estadística de obra ni dependencia Arrhenius validada.

Los IC cuantifican muestreo condicional. El IC de curado_rapido no contiene su referencia exacta del 95%; una cobertura nominal 95% no garantiza cubrir cada muestra ni todos los planes simultáneamente. Se conserva la semilla, sin seleccionar otra para mejorar concordancia.

## Qué consultar sin recalcular

- `results/e14/official.json`: índice de integridad y correspondencia de 192 inputs a chunks originales.
- `results/e14/plans.csv`: tabla completa utilizable después en F02.
- `figures/e14_probabilidades.png`, `e14_pf_N.png`, `e14_duracion_riesgo.png`: riesgo y duración.
- `figures/e14_temperaturas.png`, `e14_diferencial.png`, `e14_secciones.png`, `e14_3d.png`: evolución espacial y temporal.
- `results/verification/numerics_e14.json`: controles de malla, paso y área staircase; sin cambios de clase observados en los casos examinados. No demuestra convergencia global.

El visor oficial muestra curado_frio5 / M4_SS_m00, 744 h: Tmax weather=51,4824°C a 213,5 h; ΔT global=28,8110°C a 642,25 h. La envolvente de 24 átomos del plan llega a 51,4987°C. El control constante 20°C es una comparación aparte, no otro átomo Monte Carlo; la escala de color es común y puede llegar a 51,574°C por ese control. El núcleo de una sonda tampoco es necesariamente el máximo global.

Al inicio puede verse ΔT ligeramente negativo: todos los centros están a 5°C y la reconstrucción S25 junto al ambiente más cálido puede superar esa temperatura. Se comparan centros y puntos subcelda aproximados; no se grafica un valor absoluto ni se altera el criterio para ocultarlo. El máximo que gobierna la falla ocurre mucho después.

## Estado de Git y publicación

E14 se incorpora bajo el prefijo **P2_E14/** al repositorio [amvaras/Proyecto-2-MCOC](https://github.com/amvaras/Proyecto-2-MCOC), rama **codex/e14**, etiqueta [entrega-e14](https://github.com/amvaras/Proyecto-2-MCOC/tree/entrega-e14/P2_E14). El commit evaluado se obtiene resolviendo esa etiqueta; no debe usarse el SHA de E13 como identificador de E14.

La base de esta publicación es E13, `9fc62cd4d5d0a4ee36810827add3ceb9e00f6527`. Se preservan los cambios ajenos a E14 del computador y se prepara exclusivamente el inventario `E14_ARCHIVOS_A_VERSIONAR.txt`. El estado del checkout antiguo descrito por el autor del ZIP se conserva como evidencia histórica dentro de `results/verification/git_e14.json`.

La publicación fue solicitada expresamente por el usuario el 18 de noviembre de 2026. [Identificación de la entrega](E14_PUBLICACION.md). La modalidad comprobada es local; no se declara JobID ni ejecución en cluster.

## Pendientes reales antes de F02

1. Confirmación académica del criterio global S25 y de los supuestos de pesos, mezcla, clima, capacidad frigorífica y juntas. Ningún resultado demuestra cumplimiento o seguridad de obra.
2. Job real en HPC y entorno Linux: pendiente de acceso autorizado; seguir `E14_HPC_PENDIENTE.md`. La emulación local no acredita clúster.
3. Identificación de publicación: etiqueta `entrega-e14`; declarar su SHA completo en Canvas y conservar esa referencia.
4. Ensayar la apertura local con las dependencias previamente instaladas y el conjunto sellado disponible. La instalación desde cero sin Internet no se promete sin paquetes previamente disponibles.

La preparación científica local queda separada de esos pendientes. La documentación de uso sin Internet está en `E14_REPRODUCCION_OFFLINE.md`; las pruebas y auditorías actuales se registran en `results/verification`.
