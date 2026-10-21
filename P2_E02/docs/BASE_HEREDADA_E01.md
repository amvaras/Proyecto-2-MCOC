# Base heredada E01

Copia física realizada el 21 de octubre de 2026 (Santiago), desde el commit
53a9575d19e98143e84286d73f7b81c756aa9929. El checkout estaba limpio antes de
crear la rama E02. El inventario E01_INVENTARIO_BASE.json registra todos los
archivos versionados originales, tamaño y SHA256 antes de la copia.

Se copiaron TODOS los archivos disponibles en Git: código src/mcoc_p2, tests,
examples, scripts, geometry/foundation.ifc, docs (incluido historial), capturas
evidencias/bonsai, configuración y dependencias. También se copiaron los
resultados científicos disponibles de la preparación de nube en results/.
Se excluyeron .git, entornos virtuales, cachés y metadatos de instalación.
No se encontraron secretos que fuera necesario copiar. No se copiaron carpetas
del computador del usuario. No se dispone del ZIP hermano ni de las ruedas
Windows del respaldo original, y no se inventaron.

La base vigente es la raíz; docs/historico contiene la versión antigua de
54 tests, no la base de esta entrega. La copia recién instalada pasó sus
67 tests antes de implementar E02. El registro se conserva en
../evidencias/e02/base_e01.txt. Python de nube: 3.12.14 / Linux x86_64.
La auditoría Windows heredada usó Python 3.12.10; esos registros son históricos.

IFC4 con cinco IfcFooting, base octagonal de 18 m entre caras, cotas de 0 a
4,30 m y pedestal de diámetro 7 m. GUID, propiedades, esquema y volúmenes
verificables con scripts/check_ifc.py. El IFC heredado se conserva sin editar.

Límites heredados: 1D uniforme, material constante, fuente y fronteras
constantes; no calibración experimental ni conexión IFC→solver. No se añaden
hidratación, clima, 2D/3D ni optimización en E02.

Adaptaciones limitadas a esta entrega: README nuevo (original preservado como
README_HEREDADO_E01.md); check_bonsai_evidence.py resuelve Evidencias/ como
evidencias/ en Linux sin modificar imágenes ni el registro histórico. Los
otros archivos heredados se conservan con su contenido original.

El inventario de congelación histórico enumera 142 archivos: en la copia de
Git faltan 37 (principalmente results y wheelhouse Windows). Hay 55 diferencias
de hash explicadas íntegramente por LF/CRLF. No se afirma equivalencia byte a
byte con el computador local. Los inventarios de E01 son referencia histórica;
no deben regenerarse para ocultar estas diferencias.
