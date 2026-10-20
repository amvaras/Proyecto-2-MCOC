# Modelo preliminar y revisión en Bonsai

La fuente del modelo es `geometry/foundation.ifc`. Fue generado por
`scripts/create_preliminary_ifc.py` usando Python/IfcOpenShell, sin interacción
con Blender/Bonsai. No se atribuye autoría ni verificación visual a esas interfaces.

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
orientación y dos triángulos incidentes por arista de la malla cerrada.

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

## Revisión humana pendiente

1. Instalar una versión compatible de Blender y Bonsai siguiendo su
   [documentación oficial](https://docs.bonsaibim.org/quickstart/installation.html).
2. En Bonsai, abrir el proyecto IFC con `File > Open IFC Project` y seleccionar
   `geometry/foundation.ifc`; los rótulos pueden variar con la versión.
3. Encuadrar la fundación; usar vistas superior y lateral. Verificar 18 m entre
   caras exteriores, borde de 1,10 m y altura total de 4,30 m.
4. Seleccionar, ocultar y mostrar las cinco vertidas por separado. Revisar el
   atributo IFC Name, clase IfcFooting, GUID, contenedor y propiedades.
5. Registrar las versiones reales de Blender/Bonsai y capturas 3D, superior y
   lateral. Guardar esos registros en `docs/evidencias/`.
6. Para practicar G02, guardar una copia en `results/`, modificar una propiedad
   desde Bonsai, guardar como IFC y leerla desde Python. No presentar esta
   actividad como realizada antes de efectuarla.
7. Si se modifica el IFC de entrega, guardarlo con `Save IFC Project` y ejecutar
   nuevamente el verificador. Guardar solo un `.blend` no actualiza el IFC.

La inspección de geometría desde Python sigue la
[documentación de IfcOpenShell](https://docs.ifcopenshell.org/ifcopenshell-python/geometry_processing.html).
La futura conexión IFC → discretización → solver queda como arquitectura;
el ejemplo 1D actual no utiliza la geometría IFC.
