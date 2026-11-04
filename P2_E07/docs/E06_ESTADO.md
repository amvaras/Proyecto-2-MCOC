# E06 — Estado de entrega

**Veredicto técnico: COMPLETA Y VERIFICADA.**
**Estado formal: COMMIT E06 PENDIENTE DE PUBLICACIÓN.**
Preparación: 28 de octubre de 2026, America/Santiago.
Entrega: viernes 30 de octubre, sin actividad sincrónica, 3 puntos.

Documento evaluado: [E06_DOSSIER.md](E06_DOSSIER.md).
Extensión medida: **1.100 palabras de prosa**, incluidos títulos, listas y
pies; 1.335 palabras visibles contabilizando además tablas, fórmulas y código.
El límite oficial de 1.200 corresponde a prosa, con figuras y tablas adicionales.
No se trasladaron párrafos a imágenes ni a tablas para eludir el límite.

## Evidencia vigente

| Comprobación | Resultado real |
|---|---|
| Suite local final | 198 aprobadas; 0 fallos, errores u omisiones; JUnit 26,256 s |
| Suite en copia externa | 198 aprobadas; 0 fallos, errores u omisiones; JUnit 25,912 s |
| Batería nominal | 10/10 PASS en ambas ejecuciones |
| Variaciones adicionales | 60/60 PASS en ambas ejecuciones |
| Robin adicional | h=25, inicial 50 °C, ambiente 20 °C: PASS |
| Convergencia espacial | órdenes 1,92254 / 2,00140; contaminación temporal ≤2,037% |
| Convergencia temporal | órdenes 1,00403 / 1,00201 en malla 6×6 fija |
| Energía heterogénea | residuo máximo 4,4793e-10 J ≤3,0851e-4 J |
| Fuente uniforme | incremento 4,629629630 °C; error 2,4869e-14 °C |
| Robin nominal | enfriamiento coherente y residuo 5,5879e-9 J ≤5,401e-4 J |
| Referencias analíticas | operador y autovalores comprobados en 1D/2D/3D |
| IFC | IFC4; cinco IfcFooting; 0 incidencias de esquema; cotas correctas |
| Volumen IFC | analítico 636,88503645 m³; malla 636,87771758 m³ |
| Reconstrucción IFC | misma geometría, GUID, propiedades y jerarquía |
| Tres figuras | generadas desde datos/IFC reales y revisadas visualmente |
| Independencia | copia física externa y nuevo entorno instalado sin red: PASS |
| Entregas anteriores | E01/E02/E04/E05 intactas, incluidos tamaños, SHA256 y mtime |

Resultados: [ejecución local](../evidencias/e06/ejecucion_02/e06.json),
[independencia](../evidencias/e06_independencia/independence.json),
[auditoría](E06_AUDITORIA.md).
Las versiones verificadas fueron Python 3.12.10, NumPy 2.5.4, pytest 9.1.1,
Matplotlib 3.11.2, IfcOpenShell 0.9.0.post1 y paquete mcoc-p2 0.5.0.

## Pendiente formal y límites

No se identificaron pendientes técnicos bloqueantes dentro de E06.
Falta publicar esta entrega con autorización y consignar su SHA en el dossier.
El SHA remoto de E01 no se presenta como commit E06. La entrega formal no se
declara cerrada; el inventario SHA256 local no reemplaza ese requisito.

La geometría es docente e idealizada; sus simplificaciones están explícitas.
El IFC carece de georreferencia global y representa cinco vertidas iniciales,
sin armaduras ni anclajes. La figura es Python/IfcOpenShell, no una captura
nueva de Bonsai. Se preservaron sin cambios los descriptores históricos E01.
Las cajas térmicas no están conectadas al IFC mediante voxelización y no
predicen temperaturas de Freirina. No se implementaron E07–E15 ni se
modificaron otras entregas. P2_E03 no existe en esta raíz.

No se garantiza una puntuación: la rúbrica se contrasta con evidencias en la
auditoría y la calificación corresponde al equipo docente.
