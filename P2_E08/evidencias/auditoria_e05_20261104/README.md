# Evidencia de auditoría E05 — 4 de noviembre de 2026

- `verification.json`: ejecución final aprobada, versiones, comandos, códigos de salida y huellas del código.
- `pytest.xml` y `pytest.txt`: 282 pruebas, sin fallos, errores ni omisiones.
- `parameter_sweep.json`: 60 combinaciones aprobadas.
- `battery/`: diez casos con referencias, criterios, figuras y campos numéricos.
- `referencias_independientes.json`: 27 registros científicos de los nuevos tests de Neumann/Robin; otras tres pruebas nuevas verifican la CLI y sus campos guardados.
- `antes/`: ejecución previa a las mejoras, 252 pruebas y 60 combinaciones.
- Carpetas de variantes: cambios de material, geometría, fronteras y fuente.
- `*_esperad*.txt`: rechazos/FAIL intencionales comprobados por motivo y código de salida.
- `auditoria.json`: alcance, SHA previo, archivos nuevos/modificados y huellas de esta evidencia.

Las rutas absolutas en logs identifican la ejecución original. Se copiaron los
artefactos desde results/auditoria_e05_20261104/final sin los temporales pytest.
No se necesita esa carpeta temporal para leer esta evidencia. Los comandos para
repetir la verificación están en ../../../E05.md y en la auditoría de docs.
El SHA previo NO incluye los cambios de esta revisión, que siguen locales.
