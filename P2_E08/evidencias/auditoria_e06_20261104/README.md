# Evidencia de auditoría E06 — 4 de noviembre de 2026

- `independencia/independence.json`: copia física externa, entorno nuevo e instalación sin red; PASS.
- `independencia/resultados/e06.json`: verificación final, 297 tests sin fallos/errores/omisiones y 60 variaciones; código ejecutado igual al actual.
- `independencia/resultados/thermal/`: diez casos, controles negativos, campos NPZ y métricas.
- `independencia/resultados/artifacts/`: dossier y tres figuras regenerados en la copia.
- `independencia/resultados/foundation_rebuilt.ifc`, `ifc_rebuilt.json` y `bim.json`: reconstrucción y geometría validadas.
- `independencia/resultados/referencias.json`: autovalores contrastados con el operador real.
- `ejecucion/`: primera ejecución local aprobada de esta auditoría, preservada.
- `dossier_check_actual.json`: 810 palabras bajo límite; 1015 incluyendo tablas; 16 enlaces y tres figuras del dossier canónico.
- `antes/`: fallo inicial del inventario histórico y su explicación.
- `independencia_fallida/`: primer intento externo, fallido por el nombre de la carpeta temporal protegida; logs preservados.
- `auditoria.json`: cierre, resultados, fuentes y hashes de evidencia.

La evidencia final procede de la copia independiente instalada desde las 24 ruedas
incluidas. Las rutas absolutas en logs documentan la ejecución original, no son
archivos externos requeridos para leer o repetir los ensayos. Los temporales pytest
no se incluyen; se conserva la profundidad relativa para mantener los enlaces.

Documento de entrega: [E06_DOSSIER.md](../../docs/E06_DOSSIER.md).
Auditoría: [AUDITORIA_E06_20261104.md](../../docs/AUDITORIA_E06_20261104.md).
Repetición desde la raíz del repositorio: `./VERIFICAR_E06.ps1`.
Los cambios permanecen locales: sin commit ni push de esta revisión.
