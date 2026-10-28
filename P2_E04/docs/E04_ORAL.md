# Preparación oral E04

Material de estudio para navegar el código. Canvas pide repositorio y SHA,
sin informe. Cada integrante debe practicar personalmente la explicación.

## Recorrido de demo

1. Abrir `src/mcoc_p2/thermal_nd.py`: grid, capacidad, conductancias y caras.
   Escribir el balance de un voxel y señalar dónde está cada término.
2. Mostrar `solve_nd`: T vieja completa, paso explícito, cota local y tiempo final.
3. Ejecutar casos `sine` 2D y 3D del README. Abrir figuras y error JSON.
4. Mostrar `robin`, `source` y `two-materials` según lo solicitado.
5. Mostrar un test de energía y `evidencias/e04/convergence.json`.
6. Abrir `geometry/foundation.ifc` en Bonsai e identificar las cinco vertidas.

Preparar entorno y ventanas antes de entrar. Todas las demos estándar usan
grillas pequeñas; los inputs se cambian sin editar el solver.

## Preguntas que se deben poder desarrollar

**Balance del voxel.** C_i dT_i/dt=sum G_ij(T_j-T_i)+q_dot_i V−sum q_out A.
C_i=rho cp V, J/K. La derecha tiene unidades W. Mostrar en `power` cómo el
mismo intercambio se suma a una celda y se resta a la vecina.

**2D frente a 3D.** Cuatro frente a seis vecinos. Se agrega conducción por
las dos caras z con sus áreas y distancia. Se mantiene el mismo balance.
En 2D se adopta espesor de 1 m en la dirección omitida.

**Derivar estabilidad.** Agrupar el coeficiente propio de Euler y exigir
1−dt*sum(G)/C>=0. Interior homogéneo: sum r_a<=1/2; con pasos iguales,
1/4 en 2D y 1/6 en 3D. La cota real se evalúa también en bordes y esquinas:
una cara Dirichlet está a dx/2 del centro.

**Flujo positivo en x-.** Sale por la normal −x y enfría, igual que flujo
saliente positivo en cualquier otra cara. No confundir componente q_x sobre
un eje fijo con flujo normal exterior q_out. La API ya incorpora la convención.

**Superficie adiabática.** `Neumann(0)`, incluidas las caras omitidas en inputs.
No intercambia calor normal. Puede representar aislación ideal o simetría
justificada. Un dominio adiabático sin fuente conserva energía, aunque un
perfil no uniforme se redistribuya.

**Convección.** Robin: h(T_s−T_inf). T_s es superficie y T_inf es aire, y
pueden diferir. El centro está a media celda de la cara. Sumar resistencia de
conducción y película convectiva. `face_temperature` permite comprobar ambas
leyes. Si T_s<T_inf, entra calor; con h=0 se recupera adiabático.

**Fuente o flujo.** q_dot [W/m³] se integra sobre V y q_out [W/m²] sobre A.
Fuente uniforme en dominio adiabático: incremento q_dot*t/(rho cp).
La radiación solar actuaría como flujo y la hidratación como generación, pero
no están modeladas aquí. La fuente de demo es prescrita y constante.

**Dos materiales.** Capacidad local y conductancia por dos resistencias de
media celda. Contacto perfecto: media armónica de k. Mostrar dos capas con
flujo exacto 64 W/m² y perfil lineal por tramos. No colocar una condición de
convección entre materiales en contacto perfecto.

**Por qué dominan los bordes.** Controlan la disipación. La superficie responde
antes que el núcleo. Más intercambio puede bajar el máximo y enfriar más la
periferia; más aislación puede reducir el contraste y retener calor. No concluir
qué efecto domina en Sarco sin el caso real y sus datos.

**Esquinas.** Sumar las potencias de cada cara antes de actualizar. La capacidad
es de una celda completa. El solver nodal 1D heredado usa medias celdas y tiene
otra ubicación de incógnitas; explicar la diferencia.

**Qué cambió desde E02.** Nuevo núcleo de centros de celda 2D/3D, bordes por
cara, propiedades por celda, contacto perfecto, demos y pruebas. Se mantiene
sin cambios la API y las pruebas del solver nodal 1D anterior.

**Cómo verificar.** Conservación, fuentes con solución conocida, analíticas
transitorias y refinamiento. Separar convergencia espacial con dt pequeño fijo
y temporal usando referencia semidiscreta. Verificar el programa no equivale
a validar el hormigón real experimentalmente.

**Refinar dx a la mitad.** En difusión homogénea, dt estable baja a un cuarto.
En 3D hay ocho veces más celdas y cuatro veces más pasos: costo aproximado x32,
sin contar IO. Guardar todos los campos también tiene costo de memoria.

**Qué sabemos del BIM.** Cinco vertidas, planta de 18 m entre caras, borde de
1,10 m, altura central 3,30 m y pedestal de diámetro 7 m/altura 1 m. Altura
total 4,30 m. Intervalos z: 0–0,55; 0,55–1,10; 1,10–2,20; 2,20–3,30; 3,30–4,30 m.
Identificar nombres, GUID y property set. El material sigue siendo preliminar.

**IFC y campo 3D.** Siguen independientes. No hay voxelización ni activación
de vertidas en E04. No presentar el campo de una caja como campo de la fundación.

**Schmidt.** Leer `E04_SCHMIDT.md` y la sección original del Anexo 4. Derivar
el promedio de vecinos a partir del stencil 1D con r=1/2. Ese paso no se
traslada directamente a un voxel 3D ni a cualquier frontera.

## Antes de Canvas

Comprobar `git status`, publicar la rama cuando el usuario lo indique y obtener
el SHA con `git rev-parse HEAD`. Declarar el mismo commit que contiene la
evidencia. No cambiarlo al comenzar la evaluación. La implementación no
sustituye la comprensión y defensa individual.
