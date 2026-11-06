# E09 — Auditoría técnica y rúbrica

Revisión técnica inicial del 5 de noviembre de 2026 y auditoría de integración del 6 de noviembre.
El dossier evaluable es E09_DOSSIER.md; este informe complementario no integra
su límite de palabras. No se asigna una nota automáticamente.

## Base y alcance real

E08 estaba disponible como P2_E08.zip. Se inspeccionaron su arquitectura,
configuración, pruebas, resultados reportados y publicación; no se descomprimió
el árbol completo ni se copió su historial. La selección explícita está en
E09_BASE_SELECCIONADA.json: código, ejemplos, tests, helpers, configuración,
lock e IFC. Los helpers de auditoría E06 permanecen porque sus pruebas siguen
comprobando límites documentales y trazabilidad; no se copian dossiers antiguos.
web/ conserva una capacidad funcional con pruebas, no resultados web históricos.

Las 327 pruebas de referencia pasaron antes de ampliar el integrador.
Se reutilizan e07/ (IFC, geometría, voxelización, caras, eventos, hidratación,
ensamblaje), e08/ (inputs, integrador y pipeline vigente) y los solvers base.
La única extensión del integrador es observer: recibe vistas de solo lectura
en cada paso. Las pruebas comparan la solución con y sin observador exactamente.
No se cambiaron conductancias, capacidades, fronteras, hidratación ni tolerancias.

e09/ incorpora selección de nueve sondas, reconstrucción de temperaturas de cara,
estadísticas por paso, exportación finita con máscaras, figuras y auditoría de datos.
No existe un segundo integrador alternativo. Antes de activar material, el estado
interno heredado usa NaN como centinela; no es una temperatura física. E09 guarda
solo números finitos y máscara activa: el cero fuera de ella es relleno.

## Matriz de cumplimiento

| Criterio | Evidencia | Prueba | Estado | Observaciones |
|---|---|---|---|---|
| Modelo 3D integrado — 0,9 | results/e09_baseline; IFC y campos de 336 h | Regresión, validate_saved_result, reproducción | CUMPLE Y VERIFICADO | 60.892 ocupados; interfaces conductivas y vacíos excluidos. |
| Hidratación y vertidas — 0,7 | Inputs JSON, source/steps/energy, calendario | Fuente analítica, activaciones, balance por etapa y potencial | CUMPLE CON OBSERVACIONES | Potencial, duración y calendario ilustrativos; sin calibración ni Arrhenius. |
| Visualización e interpretación — 0,6 | Once PNG y GIF; sondas, cortes y lámina 3D de doce tiempos | Test gráfico, metadatos SHA y cotejo con arrays | CUMPLE Y VERIFICADO | Se inspeccionaron las figuras; no son imágenes de IA ni capturas de Bonsai. |
| Comparación crítica con Ju y Lei — 0,5 | Dossier y E09_FUENTES.json, artículo original | Referencia y secciones verificadas en editorial Wiley | CUMPLE CON OBSERVACIONES | Comparación cualitativa; no ajuste ni validación contra sensores. |
| Reproducibilidad — 0,3 | README, lock, scripts y reproducción independiente | Entorno separado, pip check, regresión y 35 arrays idénticos | CUMPLE | La etiqueta entrega-e09 identifica el commit del dossier. |

## Verificación del paquete recibido

- Base E08: 327 aprobadas, cero fallos, errores u omisiones, 51,90 s.
- Suite completa E09: 341 aprobadas, cero fallos, errores u omisiones.
  Incluye las 327 anteriores y 14 nuevas; no se eliminaron pruebas ni se
  relajaron tolerancias. La corrida completa tomó 385,79 s de proceso.
  Las figuras y algunas lecturas IFC tuvieron costo variable de E/S en OneDrive;
  no se presenta ese tiempo como benchmark del solver.
- Después de corregir únicamente la eliminación visual de triángulos internos
  en la imagen BIM, las 14 nuevas volvieron a pasar en 11,82 s. El ajuste no
  cambia las mallas ni la voxelización ni los campos térmicos.
- Veintitrés invariantes de artefactos: finitud, máscaras, activaciones exactas,
  continuidad temporal, estabilidad, energía reconstruida, potencial independiente,
  máximas por paso, sondas, figuras y correspondencia SHA.
- Segunda instalación desde cero con dependencias oficiales y paquete 0.9.0:
  pip check aprobado. Recalculó 336 h y comparó exactamente 28 arrays de grid,
  temperature, statistics y steps. No leyó E08. Se descartó esa corrida temporal;
  queda únicamente reproduction.json y la evidencia breve de instalación.
- Refinamiento temporal 900 → 450 s: diferencia L∞ de campo 0,0211555 °C;
  cambio del pico −0,00451761 °C. Cumple el criterio declarado de 0,2 °C.
  Es sensibilidad temporal en la misma grilla, no error exacto ni convergencia
  espacial del problema real. No se conserva otro historial de temperatura.
- Dossier: 1.081 palabras; se cuentan tablas, código, fórmulas y pies. Once
  imágenes y catorce enlaces locales válidos. La auditoría documental también
  rechaza enlaces externos al proyecto, figuras inexistentes y exceso de texto.

## Interpretación y límites

Pico global: 51,4805215 °C a 66 h, en V5, cerca de la base del pedestal.
La sonda núcleo, definida cerca de (0,0,1,65) m, no se confunde con el punto
global más caliente. La diferencia entre esa sonda y la cara superior del mismo
eje alcanza 24,3425718 °C a 287,5 h. Es un par fijo, no el máximo de todas las
diferencias posibles del sólido. Supera la referencia de 20 °C del curso.
La temperatura global no supera 70 °C en este baseline. Ninguna de estas
observaciones certifica comportamiento ni seguridad real de obra.

La base adiabática favorece retención y redistribución prolongadas. El centro
basal todavía está cerca de 49 °C al final: 14 días no equivalen a equilibrio.
La edad, colocación, distancia a fronteras y geometría cambian entre sondas;
no se atribuye toda diferencia únicamente a la posición.
Las temperaturas de cara se reconstruyen con resistencias de media celda;
los colores de cortes y vóxeles representan centros de celda.

No hay suelo explícito, clima medido, propiedades variables, dependencia térmica
de hidratación, tensiones, fisuras ni optimización constructiva. Tampoco se
demostró convergencia térmica espacial de la fundación. El área staircase puede
sesgar las pérdidas Robin. El error del pedestal se informa separadamente;
un error volumétrico total pequeño no garantiza exactitud en cada vertida.

## Auditoría de integración del 6 de noviembre

Se comprobó que el IFC tiene el mismo SHA-256 que el de E08. La repetición
de 336 h en un entorno independiente comparó 35 arrays exactos, incluido el
control sin hidratación. Se actualizaron las huellas del código en el resumen
a las de esa reproducción. Los campos y las figuras del paquete coinciden
con la evidencia verificada. La prueba con 450 s volvió a dar una diferencia
máxima de campo de 0,02116 °C.

El dossier distingue la sonda núcleo del punto más caliente del pedestal y
contrasta su evolución y el diferencial con la fundación 1 de Ju y Lei.
Se incorporó a la interfaz E08 incluida en el paquete la corrección del
indicador de progreso en Windows. La simulación E09 usa su propio flujo CLI.

[Verificación](../results/verification/verification.json) ·
[Reproducción](../results/verification/reproduction.json) ·
[Sensibilidad temporal](../results/verification/temporal_check.json).
La inspección anterior a la publicación está en E09_REPOSITORIO.json.
El [inventario](E09_ARCHIVOS_A_VERSIONAR.txt) corresponde a P2_E09 en la rama
codex/e09. La [etiqueta entrega-e09](https://github.com/amvaras/Proyecto-2-MCOC/commit/entrega-e09)
identifica el commit evaluado.
