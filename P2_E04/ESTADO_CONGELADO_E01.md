# Versión técnica congelada — E01

Proyecto 2 de Métodos Computacionales en Obras Civiles, Universidad de los Andes.
**Grupo 2 — Freirina / costa de Huasco / Sarco, Atacama.**
Coordenadas docentes: latitud -28.856102, longitud -71.421831.

**Fecha de congelación: 20 de octubre de 2026 (America/Santiago).**
Marca exacta UTC: 2026-10-20T19:18:14.806369+00:00.

Esta carpeta es la **versión técnica final, cerrada y congelada de E01**.
Se conservará sin modificaciones. No incorpora implementaciones de etapas
posteriores. El código, los tests, el modelo y la documentación existentes se
copiaron físicamente, conservando su contenido y estructura relativa.
No hay enlaces ni dependencia de archivos del directorio activo.

## Contenido y alcance

- Solver propio de difusión térmica 1D, balance conservativo, grilla uniforme,
  medias celdas de borde, condiciones Dirichlet/Neumann/Robin y fuente prescrita.
- Entorno comprobado: CPython 3.12.10, Windows AMD64. NumPy 2.5.4,
  Matplotlib 3.11.2, pytest 9.1.1 e IfcOpenShell 0.9.0.post1.
  Las 24 versiones se conservan en requirements-lock.txt. Las ruedas locales
  útiles para instalar sin red se incluyen en results/auditoria_entorno/wheelhouse/.
- geometry/foundation.ifc: IFC4, cinco IfcFooting, metros y origen local.
  Fundación octagonal de 18 m entre caras; espesor de borde 1,10 m;
  altura central 3,30 m; pedestal de diámetro 7 m y altura adicional 1 m.
- Ocho capturas originales de Blender 5.1.2 / Bonsai v0.9.0-post1,
  conservadas en evidencias/bonsai/, junto con el registro de inspección.
  El auditor inspeccionó esas capturas; no se atribuye una sesión adicional
  de interfaz a la verificación automatizada del respaldo.
- README, configuración, código fuente, tests, ejemplos, scripts, formulación,
  auditoría técnica final, resultados, datos NPZ/JSON, figuras e historial previo.
  Se conservaron los documentos existentes sin reemplazar su contenido.

## Auditoría y nueva verificación del respaldo

La última auditoría técnica concluyó **COMPLETO** y aprobó 67 pruebas, sin
fallos ni omisiones. Su informe se conserva en docs/AUDITORIA_TECNICA_E01.md.

Después de copiar, se creó otra copia física temporal y un entorno virtual
nuevo fuera de esta carpeta. La instalación se realizó sin red, utilizando
las versiones y ruedas locales incluidas. Se comprobó que el solver importado
procedía de la copia temporal, sin depender del proyecto activo.

La verificación del respaldo aprobó **67 pruebas**, 0 fallidas,
0 errores y 0 omitidas, en **12.473 s** según JUnit.
El benchmark repitió 86400 s, dt=67,5 s, 1280 pasos, Fo=0,4 y error máximo
0,0006451356521708362 °C. Se compararon todos los campos del NPZ: son idénticos.
El verificador IFC no encontró incidencias de esquema y comprobó las cinco
geometrías, propiedades y ausencia de solapamientos indebidos. Las ocho
capturas conservan su integridad y los datos observados coinciden con el IFC.

Las salidas reales de esta comprobación están en docs/evidencias/congelacion/.
VERIFICACION_RESPALDO_E01.json registra los resultados y la procedencia.
Los resultados históricos previos se mantienen en sus ubicaciones originales.

## Integridad y política de conservación

INVENTARIO_SHA256.json enumera rutas relativas, tamaños y SHA256 de contenido
para todos los archivos de esta carpeta **excepto el propio inventario**,
evitando una huella circular. También registra la estructura de directorios.
El ZIP hermano E01_ENTREGA_FINAL.zip contiene exactamente esta carpeta final,
incluida esta constancia y el inventario.

Para comprobar integridad sin escribir dentro de la carpeta:

    py -3.12 -B .\VERIFICAR_INTEGRIDAD_E01.py

No ejecutar instalaciones editables, pruebas o ejemplos directamente sobre
esta versión histórica: podrían generar metadatos o resultados. Para repetir
los comandos del README, primero hacer una copia física de trabajo en una
carpeta temporal y dirigir allí las salidas. Los registros del respaldo se
obtuvieron siguiendo precisamente ese procedimiento.

La carpeta activa conserva todos sus archivos originales, incluidos los
entornos y cachés excluidos de esta entrega. Se compararon sus 22419 archivos,
tamaños, contenidos y fechas de modificación contra el estado previo.
La separación física, el inventario y la política de no modificación son la
protección; no se imponen permisos que impidan acceder o copiar la entrega.

## Limitaciones físicas propias de E01

Un material homogéneo con propiedades constantes, dominio 1D uniforme,
fronteras constantes y fuente prescrita independiente de temperatura y tiempo.
El ejemplo es un benchmark verificable, no una predicción real de la fundación.
Los criterios del proyecto general —14 días, Tmax ≤ 70 °C y diferencial ≤ 20 °C—
se conservan como contexto y no se presentan como resultados calculados aquí.
No se incluyen clima, hidratación avanzada, voxelización, solver final 2D/3D,
Monte Carlo ni optimización constructiva.
