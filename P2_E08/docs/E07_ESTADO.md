# E07 — Estado técnico

> Registro previo a las auditorías actuales. Consultar
> [AUDITORIA_E07_20261104.md](AUDITORIA_E07_20261104.md) para las correcciones,
> conteos y evidencias vigentes. La publicación original ya ocurrió; los cambios
> de auditoría nuevos permanecen locales y no tienen un SHA nuevo.

**LISTA TÉCNICAMENTE PARA LA REVISIÓN ORAL DE E07.**
Verificación realizada el 4 de noviembre de 2026. Grupo 2 — Freirina / Sarco.
Revisión 10:30–13:20, 4 puntos. No se certifica el desempeño oral individual.

## Resultados ejecutados

| Comprobación | Resultado |
|---|---|
| Suite local final | 252 aprobadas; 0 fallos, errores u omisiones; 32,038 s JUnit |
| Suite externa independiente | 252 aprobadas; 0 fallos, errores u omisiones; 31,225 s JUnit |
| Desglose | 198 heredadas y 54 nuevas E07 |
| Regresión térmica | Diez casos nominales y 60 variantes PASS, en ambas copias |
| Nuevas demostraciones | Nominal y parámetros modificados PASS, en ambas copias |
| IFC | Cinco IfcFooting; GUID/ID preservados; IFC4; metros; validación heredada PASS |
| Grilla nominal | 66×66×32 =139392 celdas; Δ=(0,275;0,275;0,1375) m |
| Ocupación nominal | 60892 vóxeles; etiquetas 0–5; cero empates de frontera en esta grilla |
| Volumen nominal | 633,18165625 m³; error 0,5803408% frente a malla IFC |
| Referencias | Malla IFC 636,877717582 m³; analítica docente 636,885036448 m³ |
| Exterior final | 12736 caras; 747,93125 m² de área staircase |
| Interfaces entre vertidas | 9032 caras; 683,045 m²; sin Robin interno |
| Calendario ficticio | Eventos a 0,5,10,15,20 h; edades reiniciadas por pieza |
| Hidratación | Curva prescrita, potencial 64,8 MJ/m³ y duración 48 h |
| Acoplamiento | Potencia/capacidad en máscara comprobadas; no integrador transiente final |
| Balance nominal de potencia | Residuo 7,6853e-11 W ≤3,0295e-4 W |

| Vertida | Vóxeles | Volumen voxel [m³] | Error frente a malla IFC [%] |
|---|---:|---:|---:|
| 01 | 14088 | 146,49318750 | 0,7671605 |
| 02 | 14088 | 146,49318750 | 0,7671605 |
| 03 | 20630 | 214,51976563 | 0,1378997 |
| 04 | 8544 | 88,84425000 | 0,0905240 |
| 05 | 3542 | 36,83126563 | 4,2776655 |

El estudio cúbico de Δ=0,55/0,275/0,1375 m dio errores totales de
0,7062435% / 0,0498896% / 0,2093049%. No son monótonos. Se informa la
compensación de errores por piezas, sin presentar el total como garantía
de precisión del pedestal o de cada espesor.

Las cinco figuras finales están en figures/. La guía
[E07_DEMO.md](E07_DEMO.md) incluye comandos y respuestas a las nueve preguntas.
[E07_FORMULACION.md](E07_FORMULACION.md) define el contrato matemático.
[E07_AUDITORIA.md](E07_AUDITORIA.md) incluye la matriz y todos los límites.

## Alcance y pendientes

Están implementados y ejecutados IFC→grilla, etiquetas, volúmenes, exteriores,
interfaces, calendario, inicialización, edad, fuente y ensamblaje enmascarado.
No se integra todavía la evolución térmica transiente de la fundación.
Este siguiente paso no es una capacidad declarada completa en E07 y no
bloquea los seis entregables previos definidos para la revisión.

La curva no depende de temperatura ni está calibrada; el cronograma es
ilustrativo. Se supone contacto perfecto. El área staircase puede sesgar Robin.
No hay clima, Arrhenius, edad equivalente ni desarrollo E08–E15.
Las pruebas externas se efectuaron en Windows x64 / CPython 3.12.10.

**COMMIT E06 PENDIENTE DE PUBLICACIÓN.** E07 no tiene commit publicado
verificado en esta tarea. No se reutilizó un SHA E01 como identificador E07,
ni se crearon commits, ramas, PR o publicaciones. Las entregas anteriores
se conservaron y sus hashes se contrastaron; P2_E03 no existe en esta raíz.
