# Auditoría E02

## Alcance y procedencia

Se trabajó en rama E02 sobre la copia completa de E01 disponible en el commit
53a9575d19e98143e84286d73f7b81c756aa9929. Únicamente se añaden archivos bajo
P2_E02 en Git. La raíz conserva E01 y no se reorganiza. No se creó un worktree.

La copia inicial pasó 67 pruebas antes de cualquier mejora E02. Luego se
incorporaron el comparador por GUID y la demo CLI sin alterar el solver ni
los tests heredados. El comparador omite IDs STEP y OwnerHistory; su alcance
son atributos seleccionados y psets de IfcElement, no geometría. Un cambio de
GUID se informa como baja/alta, sin inventar una identidad equivalente.

La corrección Linux del comprobador de evidencias solo afecta a la copia:
resuelve Evidencias/ como evidencias/. No altera capturas ni el registro de
inspección heredado. El README anterior se conserva por separado.

## Verificaciones observadas

- Instalación nueva: Python 3.12.14, Linux x86_64, todas las versiones fijadas.
- Base heredada: 67 pruebas aprobadas, ninguna omitida, 12,76 s.
- Suite ampliada: 80 pruebas aprobadas, ninguna omitida, 17,50 s.
- Verificación integral: siete etapas con exit 0 (dependencias, tests, ejemplo,
  precisión, IFC, render y evidencia histórica Bonsai).
- IFC: cinco elementos, IFC4, metros, validación sin incidencias; mismos GUID,
  cotas, volúmenes y ausencia de intersección de interiores.
- Capturas E01: ocho archivos conservados; su integridad se comprobó. Esto no
  constituye una nueva sesión humana ni el round-trip E02.
- dt=100 s con nx=81: rechazado con exit 2, cota 84,375 s.

Registros: evidencias/e02/base_e01.txt, base_e01.xml, integral/ y
simulaciones.json. Los archivos históricos bajo docs/evidencias no se
reemplazaron. Las salidas actuales de E02 se guardan por separado.

| Caso | nx | dx [m] | dt efectivo [s] | Fo | Pasos | Error exacto [°C] |
|---|---:|---:|---:|---:|---:|---:|
| Base | 81 | 0,0125 | 67,5 | 0,4 | 1280 | 0,000645135652 |
| Temporal | 81 | 0,0125 | 33,75 | 0,2 | 2560 | 0,000092135360 |
| Espacial grueso | 41 | 0,025 | 1 | 0,00148148 | 86400 | 0,001826445143 |
| Espacial fino | 81 | 0,0125 | 1 | 0,00592593 | 86400 | 0,000444326703 |

Todos representan el mismo problema y tiempo final 86400 s. El error temporal
contra el modo semidiscreto baja de 0,001105840505 a 0,000552840213 °C. El
refinamiento espacial reduce el error en factor 4,11. El error total contiene
contribuciones de signos distintos; no se generaliza monotonía para todo dt.

## Rúbrica y límite de la auditoría

Round-trip (1,0): IMPLEMENTADO, PENDIENTE DE DEMO REAL. Solver (0,8): CUMPLE Y
VERIFICADO. Tests/evidencia numérica (0,5): CUMPLE Y VERIFICADO. Defensa oral
(0,7): NO VERIFICADO; se proporciona material de ensayo, no una nota.

No se atribuyen los fixtures de Python a Bonsai. Falta la acción humana
obligatoria indicada en E02_DEMO. No se afirma entrega completa, publicación
remota ni aceptación del profesor.

## Independencia y conservación finales

CUMPLE Y VERIFICADO: se copió la entrega fuera del checkout, se creó un venv
nuevo desde requirements-lock.txt y se instaló el paquete de esa copia. Se
comprobó que mcoc_p2.__file__ pertenecía a la copia temporal y se eliminó
PYTHONPATH del entorno de la prueba. Pasaron las 80 pruebas de la suite, los
siete pasos integrales, la demo CLI temporal y el comparador con IFC idéntico
y con un fixture Python modificado (explícitamente NO Bonsai). Todas las
operaciones devolvieron exit 0. Los logs y el resumen de la reconstrucción
están en evidencias/e02/independencia/. Luego se eliminó únicamente esa copia
temporal, tras conservar sus evidencias. No se dependió del paquete E01 activo.

Se compararon los 106 archivos versionados E01 con el inventario previo:
ninguno cambió ni falta; geometry/foundation.ifc es idéntico byte a byte a su
base heredada y a la copia de trabajo inicial. Dentro de E02 únicamente se
adaptaron dos archivos heredados: README y el comprobador de rutas Bonsai.
Todos los demás archivos heredados conservan sus hashes iniciales. No hay
symlinks en la entrega técnica (los del venv recreable quedan excluidos).
El inventario histórico de Windows no se sustituyó.
