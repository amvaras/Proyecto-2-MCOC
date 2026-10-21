# Modelo preliminar y revisión en Bonsai

La fuente del modelo es `geometry/foundation.ifc`. Fue generado por
`scripts/create_preliminary_ifc.py` usando Python/IfcOpenShell. Posteriormente
se abrió y revisó manualmente en Blender 5.1.2 / Bonsai v0.9.0-post1. Las ocho
capturas aportadas se inspeccionaron durante esta auditoría y son coherentes
con el IFC. La autoría inicial sigue siendo Python; el auditor no operó una
sesión adicional de Blender/Bonsai.

## Geometría docente

IFC4, unidades SI en metros, origen local (0,0,0), jerarquía
IfcProject → IfcSite → IfcBuilding → IfcBuildingStorey → cinco IfcFooting.
Cada volumen tiene Name, GUID reproducible mediante UUID5, material preliminar
y propiedades `UANDES_HormigonMasivo`. No se inventan fechas de vertida ni
temperaturas de colocación. El nombre del material indica que falta definirlo;
las propiedades térmicas del benchmark no se consideran calibradas para el IFC.

| Nombre | z inferior/superior [m] | Geometría |
|---|---|---|
| Vertida_01 | 0 / 0,55 | Prisma octagonal, apotema 9 m |
| Vertida_02 | 0,55 / 1,10 | Prisma octagonal, apotema 9 m |
| Vertida_03 | 1,10 / 2,20 | Tronco octagonal, apotemas 9 → 6,25 m |
| Vertida_04 | 2,20 / 3,30 | Tronco octagonal, apotemas 6,25 → 3,5 m |
| Vertida_05 | 3,30 / 4,30 | Cilindro de radio 3,5 m y altura 1 m |

Se aplicó `R=apotema/cos(pi/8)` y giro de 22,5° para alinear caras con los ejes.
La apotema intermedia es (9+3,5)/2=6,25 m. Borde exterior: 1,10 m de espesor;
altura central de la fundación: 3,30 m, más 1 m de pedestal. La transición
termina en octágono de 7 m entre caras y el pedestal en círculo de diámetro
7 m, como simplificación docente. No es un CAD exacto del artículo de referencia
ni una secuencia constructiva optimizada. Los volúmenes comparten caras de
contacto; sus interiores ocupan intervalos z distintos y no se solapan.

Los cuatro octágonos se representan con IfcPolygonalFaceSet cerrado; el cilindro
con IfcCircleProfileDef e IfcExtrudedAreaSolid, conservando el diámetro exacto
en el IFC. La triangulación de lectura aproxima el círculo: se admiten 2 mm
en su bounding box y 0,05 % en volumen; en los octágonos las cotas se revisan
a 1e-7 m. El verificador compara además volúmenes analíticos independientes,
orientación y dos triángulos incidentes por arista de la malla cerrada. La
auditoría agregó orientación opuesta en cada arista, conectividad de la malla,
anillos octagonales superior/inferior, radio exacto del pedestal, cadena espacial
completa y correspondencia de propiedades Z con las cotas geométricas.
Se comprobaron las diez parejas de elementos: sus interiores están separados
en Z, admitiendo contacto de caras sin solapamiento volumétrico.

## Comandos

```powershell
python scripts/check_ifc.py geometry/foundation.ifc --json results/ifc_check.json
# Reconstruir en otra ruta, preservando el modelo entregado:
python scripts/create_preliminary_ifc.py --output results/foundation_rebuilt.ifc
python scripts/check_ifc.py results/foundation_rebuilt.ifc
```

El generador de línea de comandos rechaza un destino existente para proteger
ediciones posteriores en Bonsai. La prueba de reconstrucción usa una carpeta
temporal y compara el informe completo, incluidos GUID y geometría.

## Revisión humana realizada y evidencia inspeccionada

Las capturas originales se conservan en `Evidencias/bonsai/`. Se comprobaron
las ocho imágenes existentes, sin modificarlas. Se observa Blender 5.1.2 y,
en la barra inferior de las capturas de propiedades, Bonsai v0.9.0-post1.

| Archivo | Comprobación visible |
|---|---|
| vista_3d.png | foundation.ifc, esquema IFC4, geometría y cinco IfcFooting |
| vista_superior.png | Top Orthographic, octágono, pedestal y selección individual |
| vista_perfil.png | Back Orthographic y perfil escalonado con pedestal |
| propiedades_vertida_01.png | Vertida_01, IfcFooting, ID 1, z=0–0,55 m, UANDES_HormigonMasivo |
| propiedades_vertida_02.png | Vertida_02, IfcFooting, ID 2, z=0,55–1,10 m, mismo pset |
| propiedades_vertida_03.png | Vertida_03, IfcFooting, ID 3, z=1,10–2,20 m, mismo pset |
| propiedades_vertida_04.png | Vertida_04, IfcFooting, ID 4, z=2,20–3,30 m, mismo pset |
| propiedades_vertida_05.png | Vertida_05, IfcFooting, ID 5, z=3,30–4,30 m, mismo pset |

Los paneles recortan visualmente los GlobalId; sus prefijos visibles coinciden
con los valores completos verificados desde el archivo IFC. Las dimensiones
exactas se comprobaron automáticamente; no se inventan mediciones con cotas
de interfaz ausentes en las imágenes. La revisión humana confirma selección,
clasificación, propiedades y aspecto. El registro de observaciones es
`Evidencias/bonsai/revision_visual.json`; `scripts/check_bonsai_evidence.py`
contrasta identidad de archivos, dimensiones PNG y propiedades con el IFC.
Este script no interpreta automáticamente los píxeles ni ejecuta Bonsai.

No queda pendiente la apertura visual del primer modelo exigido en E01.

## Instrucciones para repetir la revisión

1. Instalar una versión compatible de Blender y Bonsai siguiendo su
   [documentación oficial](https://docs.bonsaibim.org/quickstart/installation.html).
2. En Bonsai, abrir el proyecto IFC con `File > Open IFC Project` y seleccionar
   `geometry/foundation.ifc`; los rótulos pueden variar con la versión.
3. Encuadrar la fundación; usar vistas superior y lateral. Verificar 18 m entre
   caras exteriores, borde de 1,10 m y altura total de 4,30 m.
4. Seleccionar, ocultar y mostrar las cinco vertidas por separado. Revisar el
   atributo IFC Name, clase IfcFooting, GUID, contenedor y propiedades.
5. Registrar las versiones reales y nuevas capturas si se modifica el modelo;
   conservar las actuales y actualizar el registro de inspección por separado.
6. Para comprobar modificaciones en futuras actividades, trabajar en una copia
   en `results/` y contrastar desde Python. No se exige ese ciclo de modificación
   y detección como requisito adicional para cerrar la base técnica de E01.
7. Si se modifica el IFC de entrega, guardarlo con `Save IFC Project` y ejecutar
   nuevamente el verificador. Guardar solo un `.blend` no actualiza el IFC.

La inspección de geometría desde Python sigue la
[documentación de IfcOpenShell](https://docs.ifcopenshell.org/ifcopenshell-python/geometry_processing.html).
La futura conexión IFC → discretización → solver queda como arquitectura;
el ejemplo 1D actual no utiliza la geometría IFC.
