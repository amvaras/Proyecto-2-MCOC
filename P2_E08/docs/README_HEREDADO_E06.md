# MCOC P2 · Grupo 2 · E06

**Dossier de verificación y BIM — viernes 30 de octubre de 2026.**
Estado técnico: verificado. Estado formal: **COMMIT E06 PENDIENTE DE PUBLICACIÓN**.
Repositorio: [amvaras/Proyecto-2-MCOC](https://github.com/amvaras/Proyecto-2-MCOC).
main contiene E01; su SHA no identifica E06. No se publicaron cambios.

Entrega principal: [docs/E06_DOSSIER.md](docs/E06_DOSSIER.md).
El solver y el IFC conservan su contenido de E05. El paquete continúa en
0.5.0: E06 consolida evidencia y documentación, sin otro solver.
Las cajas ideales no predicen la temperatura de la fundación de Freirina.

## Instalación sin red

Desde la raíz de P2_E06, Windows x64, CPython 3.12. Se verificó 3.12.10.
Las 24 ruedas bloqueadas están incluidas. No se requiere otra entrega.

```powershell
py -3.12 -m venv .venv
$pyE06 = '.\.venv\Scripts\python.exe'
& $pyE06 -m pip install --no-index --find-links vendor/wheels -r requirements-lock.txt
& $pyE06 -m pip install --no-index --no-build-isolation --no-deps -e '.[dev,plot,bim]'
& $pyE06 -m pip check
```

## Repetir y verificar

```powershell
& $pyE06 -X utf8 -B scripts/verify_e06.py --output results/e06_repeticion
& $pyE06 -X utf8 -B scripts/check_e06_dossier.py docs/E06_DOSSIER.md --json results/e06_palabras.json
& $pyE06 -X utf8 -B scripts/check_e06_independence.py --output evidencias/e06_independencia_nueva
```

Elegir destinos nuevos: los scripts rechazan carpetas con contenido.
El primer comando comprueba import propio, integridad, 198 tests, diez casos,
sesenta variantes, rechazos esperados, Robin h=25, IFC reconstruido,
referencias, figuras, enlaces y palabras. El dossier reproducido queda en
artifacts/ bajo el destino elegido; conserva los artefactos de referencia.
`--freeze` solo sirve para la creación inicial y rechaza un dossier existente.
El último comando realiza copia física externa, instala otro entorno sin red
y repite E06. Conserva ruta temporal efectiva y logs, sin eliminar históricos.

Comandos individuales:

```powershell
& $pyE06 -X utf8 -B -m pytest tests -q -p no:cacheprovider
& $pyE06 -X utf8 -B examples/run_e05.py --all --config configs/e05/lab.json --output results/e06_bateria_manual
& $pyE06 -X utf8 -B scripts/check_ifc.py geometry/foundation.ifc --json results/e06_ifc.json
& $pyE06 -X utf8 -B scripts/create_preliminary_ifc.py --output results/e06_foundation_rebuilt.ifc
& $pyE06 -X utf8 -B scripts/check_ifc.py results/e06_foundation_rebuilt.ifc
```

El generador rechaza destinos existentes. No reconstruir sobre el IFC de referencia.
En Blender con Bonsai habilitado, abrir geometry/foundation.ifc mediante Open
IFC Project; seleccionar Vertida_01 a Vertida_05 en el árbol espacial y revisar
cotas y UANDES_HormigonMasivo. Las etiquetas E01 preservadas indican procedencia.
El material IFC es descriptivo; no implica calibración térmica de la fundación.
La figura E06 procede del IFC real mediante IfcOpenShell y Matplotlib; no es
una captura Bonsai. Las capturas heredadas son antecedentes separados.

## Evidencia y alcance

- [Dossier](docs/E06_DOSSIER.md), [estado](docs/E06_ESTADO.md) y [auditoría](docs/E06_AUDITORIA.md).
- [Ejecución vigente](evidencias/e06/ejecucion_02/e06.json): comandos, versiones y hashes.
- [BIM comprobado](evidencias/e06/ejecucion_02/bim.json): dimensiones, volúmenes e identidades.
- [Referencias](evidencias/e06/ejecucion_02/referencias.json): autovalores y residuos del operador 1D/2D/3D.
- [Fuentes](docs/E06_FUENTES.json) y [enunciado](docs/E06_ENUNCIADO.md).
- [Inventario base](docs/E06_BASE_E05_INVENTARIO.json): 899 archivos copiados físicamente.

src/, tests/, examples/, scripts/, configs/, geometry/, vendor/wheels y
requirements-lock.txt permiten repetir los cálculos. figures/ conserva las tres
figuras finales. Los JSON/NPZ registran parámetros, métricas y tolerancias.
Los resultados anteriores son históricos. El README previo sigue en
docs/README_HEREDADO_E05.md. No se modificaron las entregas E01–E05.

La energía usa capacidades ponderadas; la convergencia espacial compara con
la PDE continua a Δt fijo y la temporal con el sistema semidiscreto en malla
fija. La estabilidad se calcula con conductancias locales, incluidas las caras.
Se resuelven cajas uniformes por eje, propiedades constantes en tiempo y
contacto perfecto. No se implementan voxelización, acoplamiento IFC, clima,
hidratación, optimización ni E07–E15. Se ensayó Windows x64/Python 3.12.

El inventario final SHA256 congela contenidos locales, excepto su propio
archivo, entornos y cachés. verify_e06 lo coteja cuando existe. No sustituye
el commit requerido. El estado formal queda pendiente de publicación autorizada.
