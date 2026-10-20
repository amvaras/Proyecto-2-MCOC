# Estado técnico E01 — 20 de octubre de 2026

**Veredicto: COMPLETO.** Los cinco requisitos técnicos obligatorios están
implementados y verificados. No queda trabajo técnico obligatorio pendiente
para la base E01. Este estado se refiere al código, pruebas, entorno, modelo
IFC/Bonsai y documentación técnica.

| Requisito | Evidencia actual | Resultado | Estado | Pendiente / acción correctiva |
|---|---|---|---|---|
| README mínimo | README.md, comandos desde la raíz | Instalación y ejecución coherentes con los archivos | CUMPLE Y VERIFICADO | Ninguno |
| Entorno reproducible | requirements-lock.txt, pyproject.toml, environment_rebuild.json | CPython 3.12.10 / Windows x64; entorno nuevo sin paquetes del sistema; 24 versiones coincidentes; pip check correcto | CUMPLE Y VERIFICADO | Ninguno |
| Primeros tests | tests/, pytest.txt y pytest.xml de auditoría | 67 aprobadas; 0 fallidas; 0 errores; 0 omitidas; 12,33 s | CUMPLE Y VERIFICADO | Se añadieron 13 pruebas para cerrar los hallazgos |
| Solver 1D inicial | diffusion_1d.py, formulación y benchmark | Balance conservativo, fuente, tres bordes y estabilidad; error de benchmark 0,000645135652 °C | CUMPLE Y VERIFICADO | Robustez corregida para dx entero y campos complejos |
| Primer modelo IFC/Bonsai | foundation.ifc, ifc_check.json, ocho capturas humanas | IFC4, cinco IfcFooting, esquema sin incidencias, dimensiones y propiedades coherentes; revisión visual documentada | CUMPLE Y VERIFICADO | Documentación actualizada con la evidencia humana |
| Conservación y signos | Tests de Neumann/Robin y energía | Medias celdas correctas y balances por paso | CUMPLE Y VERIFICADO | Ninguno |
| Convergencia espacial y temporal | accuracy.json y pruebas específicas | Cocientes espaciales 3,9979/4,0247; temporales 2,0040/2,0020/2,0010 | CUMPLE Y VERIFICADO | Se aisló el error temporal de la discretización espacial |
| Geometría y propiedades IFC | Verificador ampliado y pruebas negativas | Cadena espacial, anillos, cotas declaradas, mallas cerradas, volúmenes y diez pares sin solapamiento | CUMPLE Y VERIFICADO | Verificador ampliado; modelo original conservado |
| Documentación técnica y evidencias | README, formulación, IFC_BONSAI, informe y registros | Consistentes con las ejecuciones y capturas actuales | CUMPLE Y VERIFICADO | Estados anteriores preservados en docs/historico/ |
| Simulación final de 14 días y límites 70 °C/20 °C | Contexto del proyecto general | Fuera del alcance técnico de esta base | NO APLICA A E01 | Ninguno para E01 |
| Clima, hidratación avanzada, 2D/3D y optimización | Etapas posteriores | No se implementaron ni se presentan como realizadas | NO APLICA A E01 | Ninguno para E01 |

Los resultados actuales están en `docs/evidencias/auditoria/`. Las salidas de
la preparación inicial conservadas directamente en `docs/evidencias/` son
históricas y no representan esta auditoría. Una copia del estado previo está
además en `docs/historico/pre_auditoria_20261020T174429Z/`.

## Comprobaciones y procedencia

- La auditoría partió de 54 pruebas nuevamente ejecutadas: 54 aprobadas en 6,12 s.
- Se reprodujeron dos defectos de robustez y se corrigieron sin cambiar la física.
- La suite corregida pasó 67 pruebas en 11,99 s; la corrida integral desde el
  entorno reconstruido pasó las 67 en 12,33 s.
- El ejemplo conserva 86400 s, 1280 pasos, dt=67,5 s y Fo=0,4. Su NPZ se
  contrastó con una reconstrucción independiente de la solución exacta y error.
- `pip check` no encontró conflictos. Las versiones del nuevo entorno coinciden
  con las 24 entradas del archivo fijado, sin utilizar paquetes del sistema.
- La revisión humana de Blender 5.1.2 / Bonsai v0.9.0-post1 se acredita mediante
  las ocho capturas aportadas en `Evidencias/bonsai/`. El auditor inspeccionó
  dichas imágenes y contrastó sus datos; no ejecutó una sesión adicional de interfaz.
- Se comprobaron de nuevo el IFC entregado y su reconstrucción. No fue necesario
  cambiar la geometría existente para satisfacer los controles ampliados.

## Límites técnicos del modelo actual

Un material homogéneo con propiedades constantes, grilla 1D uniforme, fronteras
constantes y fuente prescrita constante en el tiempo. No se modela el caso
real ni se calibra el hormigón con mediciones. La portabilidad comprobada es
Windows x64 / Python 3.12; no se ha ensayado otro sistema operativo. Son límites
explícitos del alcance, no requisitos técnicos pendientes de E01.

Informe completo: [AUDITORIA_TECNICA_E01.md](AUDITORIA_TECNICA_E01.md).
