# Evidencia de auditoría E07 — 4 de noviembre de 2026

- `ejecucion/verification.json`: 307 pruebas sin fallos/errores/omisiones, 60 variantes, dos demos E07 y tres resoluciones.
- `ejecucion/thermal_regression/pytest.xml` y `pytest.txt`: suite completa; incluye las diez pruebas adicionales.
- `ejecucion/demo/summary.json`: caso nominal con parámetros efectivos por vertida, volúmenes, potencia y calor prescrito.
- `ejecucion/demo/figures/`: cinco figuras nominales revisadas; el caso modificado tiene sus propias figuras en `ejecucion/modified/figures/`.
- `ejecucion/demo/*.npz`: geometría, etiquetas, caras e instantánea de estados; no temperatura transiente integrada.
- `referencias_cientificas.json`: cubo girado con volumen/área analíticos y cinco edades de hidratación.
- `pruebas_adicionales/`: corridas de los nuevos tests; el primer intento tuvo dos errores de preparación por carpeta padre ausente, subsanados antes de la suite final.
- `auditoria.json`: fuentes, alcance, inventarios y huellas de esta evidencia.

Las rutas absolutas en JSON/logs documentan la ejecución original. Los archivos
se conservan aquí con la misma profundidad relativa respecto de P2_E07; los
campos NPZ, JSON y figuras se leen sin depender de los temporales pytest.

[Auditoría completa](../../docs/AUDITORIA_E07_20261104.md).
[Guía oral](../../docs/E07_DEMO.md).
[Figura de hidratación](ejecucion/demo/figures/e07_hidratacion_preliminar.png).
[Exterior e interfaces](ejecucion/demo/figures/e07_superficies_interfaces.png).

Repetición desde la raíz del repositorio: `./VERIFICAR_E07.ps1`.
Los resultados son preliminares y sin calibración Freirina. El calor integrado
es generación prescrita, no energía sensible de una fundación resuelta.
La defensa individual y el SHA de publicación nuevo siguen pendientes.
