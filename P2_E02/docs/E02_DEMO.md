# Demostración E02 — guía y defensa individual

Todos los comandos parten del interior de esta entrega. En PowerShell usar
punto decimal y Python 3.12. No abrir el modelo de otra entrega.

## Round-trip humano: PENDIENTE

1. En el computador del estudiante, obtener la carpeta P2_E02 completa desde
   la rama entregada, instalar dependencias según README y abrir Blender con
   Bonsai compatible. Registrar las versiones reales utilizadas.
2. En Bonsai, usar Open IFC Project y abrir
   geometry/e02/foundation_trabajo.ifc. Es una copia física idéntica de
   geometry/foundation.ifc. No editar el modelo base. Si la copia de trabajo ya
   contiene trabajo humano, no sobrescribirla: crear otra copia con nombre nuevo.
3. Identificar las cinco IfcFooting. Seleccionar Vertida_03; mostrar Name,
   clase y GlobalId `0l2Nmu8ZrTEQU0yg2tbkUj`. Capturar la selección y el GUID.
4. Abrir el panel de Property Sets de Bonsai (la ubicación exacta depende de
   su versión). Buscar UANDES_HormigonMasivo y activar su edición.
5. Verificar Estado original: `Preliminar E01; sin plan constructivo optimizado`.
   Cambiar SOLO Estado a `Modificado desde Bonsai para E02.` y confirmar los
   cambios con el botón de guardar/aplicar del pset. No cambiar las cotas Z.
6. Usar Save IFC Project As / Save As IFC de Bonsai, según versión. Guardar
   geometry/e02/foundation_bonsai_e02.ifc. Guardar un .blend no sustituye el IFC.
   Capturar el valor editado y la operación/ruta de guardado. Si el nombre de la
   acción difiere, consultar la documentación de la versión instalada.
7. Ejecutar:

```powershell
.\.venv\Scripts\python.exe scripts/compare_ifc_e02.py geometry/foundation.ifc geometry/e02/foundation_bonsai_e02.ifc --require-change --json evidencias/e02/roundtrip_real.json
.\.venv\Scripts\python.exe scripts/check_ifc.py geometry/e02/foundation_bonsai_e02.ifc --json evidencias/e02/ifc_editado.json
.\.venv\Scripts\python.exe -m pytest -q
```

8. Si la edición se realizó correctamente, el comparador mostrará cinco
   elementos antes/después y el cambio Estado para el mismo GUID, con su valor
   anterior y nuevo. Revisar cualquier diferencia adicional antes de aceptar.
   La verificación geométrica debe seguir pasando porque solo cambió Estado.
9. Guardar las capturas en evidencias/e02/ con nombres before/after/guardado;
   documentar en un registro la fecha, operador, versiones, rutas, comando y
   resultado real. Actualizar E02_ESTADO y E02_AUDITORIA después de comprobarlo.
   Las capturas E01 heredadas no acreditan este nuevo round-trip.

No existe aún foundation_bonsai_e02.ifc. Los fixtures de los tests son cambios
Python y se identifican como tales; no son la demostración humana requerida.

## Demo 1D reproducible

Ejecutar los cuatro comandos del README y enseñar los JSON. El problema físico
es idéntico: L=1 m, k=2 W/(m K), rho=2400 kg/m³, cp=900 J/(kg K), 24 h,
T inicial=20+10 sin(pi x), Dirichlet 20 °C y fuente nula.

- Base: nx=81, dx=0,0125 m, dt=67,5 s, Fo=0,4, 1280 pasos.
- Temporal: nx fijo; dt=33,75 s, Fo=0,2, 2560 pasos. Disminuye el error frente
  al modo semidiscreto. El error total frente a la PDE NO tiene por qué bajar:
  los errores espacial y temporal pueden compensarse. Enseñar ambas columnas.
- Espacial: nx=41 y 81 con dt=1 s admisible en ambos. dx pasa de 0,025 a
  0,0125 m. Comparar error exacto, usando el mismo tiempo final y dt.
- Inestable: ejecutar `examples/run_e02_1d.py --nx 81 --dt 100`; debe terminar
  con código 2 y explicar la cota. No presentarlo como simulación válida.

## Defensa oral individual

1. BIM contiene identidad y propiedades; IFC intercambia esa información.
   Blender es la aplicación 3D; Bonsai permite editar BIM; IfcOpenShell lee IFC.
2. Explicar el mismo GUID antes/después y el valor Estado leído desde los dos
   archivos. El comparador no certifica qué aplicación produjo el archivo.
3. dx=L/(nx-1), Fo=alpha*dt/dx² y alpha=k/(rho*cp). Reducir dx a la mitad
   exige aproximadamente dt/4 para mantener Fo. Para Robin la cota es más fuerte.
4. Euler es de primer orden temporal y el stencil de segundo orden espacial.
   Estabilidad no equivale a precisión. Las medias celdas conservan energía.
5. Explicar una prueba de conservación y otra de cambio IFC. Un test verde
   no sustituye la demostración de la edición humana.
6. Este benchmark no predice la fundación real ni verifica 70 °C/20 °C en 14 días.

Ensayo de 5 minutos: identificar IFC (1 min), editar/guardar/comparar (1,5 min),
correr base/refinamientos (1 min), explicar estabilidad y tests (1,5 min).
La comprensión individual y el tiempo real del ensayo están pendientes.

## GitHub y Canvas desde el computador del estudiante

Primero recuperar los cambios de nube: usar la publicación de rama de la UI
solo cuando autorices subirlos, o importar el bundle local entregado. Un commit
local de nube no aparece por sí solo en GitHub. No hacer merge a main.

Una vez disponible localmente la rama E02, ejecutar la demo humana y revisar:

```powershell
git status --short
git add P2_E02
git diff --cached --stat
git commit -m "E02: evidencia real Bonsai e IFC editado"
git push -u origin E02
git rev-parse HEAD
```

Ejecutar Git desde la raíz del checkout. Si hay otros cambios ajenos a E02,
no incluirlos. Revisar el commit en GitHub y entregar en Canvas su URL
`https://github.com/amvaras/Proyecto-2-MCOC/commit/<SHA_REAL>`.
No sustituir SHA_REAL por el commit base E01 ni por un commit que siga solo
en la nube. Subir una rama no requiere fusionarla con main.

### Recuperar el commit de nube mediante bundle

Descargar Proyecto-2-MCOC-E02.bundle. En la raíz de un clon local del mismo
repositorio, sin cambios sin guardar y si aún no existe una rama E02:

```powershell
git bundle verify <ruta-al-archivo>/Proyecto-2-MCOC-E02.bundle
git fetch <ruta-al-archivo>/Proyecto-2-MCOC-E02.bundle E02
git switch -c E02 FETCH_HEAD
```

Sustituir el marcador por la ubicación real del archivo descargado. Si ya
existe E02, no usar reset ni sobrescribirla: revisar ambas versiones y recuperar
el commit en una rama de revisión con otro nombre. El bundle conserva el commit
y su historial sin publicar nada. El ZIP es una alternativa para trasladar
únicamente la entrega autónoma; no contiene .git ni el entorno virtual.
