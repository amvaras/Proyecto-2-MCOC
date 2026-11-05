# E07 — Formulación e implementación

Grupo 2, Freirina / Parque Eólico Sarco. Revisión oral del miércoles
4 de noviembre de 2026, 10:30–13:20, 4 puntos.

## Alcance y arquitectura

E07 conecta el IFC real con una grilla 3D etiquetada. Implementa lectura,
pertenencia geométrica, voxelización, superficies, interfaces, eventos de
construcción, hidratación prescrita y ensamblaje térmico enmascarado de potencia
y capacidad. **No integra todavía la temperatura transiente de la fundación**.
Los ejemplos presentan estados de colocación y edades, sin hacerlos pasar por
temperaturas calculadas tras el calentamiento. No se introducen parámetros
ficticios para convertir celdas vacías en hormigón.

| Responsabilidad | Implementación |
|---|---|
| Triángulos cerrados y pertenencia | src/mcoc_p2/e07/geometry.py: ClosedMesh |
| Extracción IFC mundial SI | src/mcoc_p2/e07/ifc.py: read_pours, PourSolid |
| Grilla y etiquetas | src/mcoc_p2/e07/voxel.py: VoxelGrid, voxelize, Voxelization |
| Exterior e interfaces | src/mcoc_p2/e07/faces.py: exposed_faces, contacts |
| Hidratación preliminar | src/mcoc_p2/e07/hydration.py: AdiabaticCurve, q_dot_h |
| Eventos y edades | src/mcoc_p2/e07/construction.py: PourEvent, ConstructionState |
| Potencias/capacidades en máscara | src/mcoc_p2/e07/coupling.py: MaskedAssembly |
| Figuras y demostración | plots.py y examples/run_e07.py |

## IFC, unidades y transformaciones

read_pours procesa una sola geometría por IfcFooting mediante create_shape.
Extrae GUID, nombre, VertidaID, propiedades, Estado, matriz mundial,
vértices, triángulos, bbox, elevaciones y volumen. Exige unidad de longitud
explícita y GUID/VertidaID únicos. No suma otra vez representaciones del mismo
elemento. Se guarda geometry.json y geometry.npz.

Se configura use-world-coords=True y convert-back-units=False. El motor entrega
vértices mundiales en metros y aplica placements/mapped items: no se vuelve a
transformar la malla. La matriz get_local_placement se conserva como metadato;
su traslación se convierte con la escala IFC→m. Las propiedades con sufijo _m
se interpretan como cotas globales SI y se contrastan con la geometría.
Si otro IFC usa esas propiedades con una convención local distinta debe
corregirse el contrato de metadatos, sin adivinar su significado.

Se probaron un IFC convertido a milímetros y una pieza rotada/trasladada.
La configuración se apoya en la [documentación geométrica de IfcOpenShell](https://docs.ifcopenshell.org/ifcopenshell-python/geometry_processing.html)
y la [escala de unidades](https://docs.ifcopenshell.org/autoapi/ifcopenshell/util/unit/index.html),
además de comprobar el comportamiento de la biblioteca instalada.

El validador heredado check_ifc.py comprueba para el modelo real: IFC4,
cinco piezas, metros, orientación octagonal, espesor de borde 1,10 m,
altura central 3,30 m, pedestal Ø7 m y altura adicional 1 m, total 4,30 m.
La referencia analítica docente es 636,885036448 m³; la malla del IFC mide
636,877717582 m³. Su diferencia proviene principalmente de teselar el cilindro.
La voxelización utiliza como referencia directa el volumen de esa malla real;
ambas referencias se distinguen en la auditoría.

## Validación de mallas y pertenencia

ClosedMesh verifica índices, valores finitos, triángulos no duplicados ni
degenerados, aristas con dos incidencias opuestas, conectividad y volumen no
nulo. El volumen firmado se calcula después de trasladar a un origen cercano:

    V = abs(sum(a · (b × c))/6)

Si la orientación global es inversa se invierten los triángulos y se registra.
Se presupone una superficie simple, sin autointersecciones. No se implementa
un detector general de autointersecciones ni un reparador de mallas. En las
cinco piezas reales también se comprueba convexidad mediante todos sus
vértices y planos; son sólidos convexos.

Para una pieza convexa, el punto está dentro si satisface todos los
semiespacios n·p−d≤ε definidos por sus triángulos orientados. La bbox solo
filtra candidatos. No se recrea un octágono o cilindro para decidir pertenencia.
Si no es convexa se suman ángulos sólidos orientados:

    Ω_tri = 2 atan2(a·(b×c), |a||b||c|+(a·b)|c|+(b·c)|a|+(c·a)|b|)

Los vectores a,b,c van del punto a los tres vértices. Para una superficie
cerrada simple, la suma interior tiene magnitud 4π y la exterior cero;
se usa |ΣΩ|>2π. Una prueba previa de distancia al plano y coordenadas
baricéntricas detecta puntos sobre triángulos, aristas o vértices. No se
disparan rayos: sus coincidencias con aristas no generan dobles conteos.
La tolerancia geométrica es max(1e-10 m, 1e-9 × extensión máxima de la pieza).
Se prueban cubos, rotaciones, escala, inversión de orientación y un prisma
cóncavo en L cuyo hueco está dentro de la bbox pero fuera del sólido.

## Grilla y regla de ocupación

Arrays [i,j,k] corresponden a X,Y,Z; las operaciones aplanadas usan orden C.
El origen es la mínima bbox mundial menos el margen solicitado. Se calcula
shape=ceil((bbox_max−bbox_min+2·margen)/spacing), conservando el paso pedido;
el borde superior puede superar la bbox. Los centros son
origen+(índice+0,5)·spacing, y las caras origen+índice·spacing.
Δx,Δy,Δz están en metros y V_celda=ΔxΔyΔz en m³.

Se rechazan grillas de más de dos millones de celdas antes de reservar sus
centros. La clasificación se procesa en bloques de 256 puntos. No requiere
otras bibliotecas geométricas ni nuevas dependencias respecto de E06.

Un centro interior o de frontera se considera ocupado. Si pertenece
estrictamente a una pieza y solo a la frontera de otra, prima el interior.
Si está en una interfaz compartida por fronteras, gana el menor VertidaID,
independientemente del orden de lectura. Un solapamiento de interiores
detectado en centros produce error; esta comprobación discreta no sustituye
una operación booleana general para detectar solapes subcelulares.

0 representa vacío; 1–5 corresponden a Vertida_01–05. Se guarda
occupation_mask=(vertida_id>0), coordenadas, origen, pasos y GUID↔ID.
Una vertida sin centros se rechaza con indicación de refinar, especialmente dz.
No se reetiquetan vóxeles para forzar volúmenes teóricos.

## Error geométrico y costo

V_voxel=N_ocupados·V_celda. Se informa por pieza y total: referencia,
diferencia firmada, diferencia absoluta y error relativo. La frontera staircase
representa superficies inclinadas o curvas con caras cartesianas y altera
volumen, localización y área. El estudio compara Δ=0,55; 0,275; 0,1375 m.
No impone convergencia monótona ni espera el orden dos del solver térmico.

Un error total pequeño puede esconder cancelación entre errores por vertida.
Las piezas delgadas y el pedestal requieren revisar también dz y alineamiento.
La precisión geométrica no se certifica con un único porcentaje total.
summary.json registra shape, celdas, ocupación y costo medido de voxelización.

Las áreas sumadas son áreas de caras staircase. En superficies oblicuas,
refinarlas no asegura por sí solo convergencia al área euclídea: la suma puede
conservar un sesgo por orientación. Aplicar Robin directamente a esa área es
una hipótesis preliminar que podría sesgar pérdidas. Una predicción posterior
requiere revisar resolución, área efectiva y tratamiento de frontera.

## Exterior, interfaces y potencia térmica

exposed_faces examina los seis vecinos. Guarda índice, eje/signo, normal,
área, ID y clase top/bottom/lateral, definidas por orientación, sin inferir
automáticamente suelo o encofrado. Una celda activa frente a una vertida futura
se marca future_pour. La superficie final usa toda occupation_mask; la
superficie constructiva usa únicamente active_mask(t).

contacts recorre solo direcciones positivas para contar cada contacto una vez.
Si ambos lados están activos y tienen IDs distintos es interfaz interna;
si tienen el mismo ID es conducción interna de la misma vertida. Ninguna de
esas caras recibe Robin. Frente a una pieza futura no hay conducción: esa
cara queda expuesta y admite la frontera constructiva escogida.

MaskedAssembly reutiliza las clases Material/Dirichlet/Neumann/Robin y el
balance de E06. Su conductancia de contacto perfecto es:

    G_ij = A / (Δn/(2k_i) + Δn/(2k_j))      [W/K]
    C_i = rho_i cp_i V_celda               [J/K]
    P_i = sum G_ij(T_j−T_i) + q_dot_i V − sum q_out A   [W]

Vacíos e inactivos tienen capacidad cero y no forman contactos; no participan
en divisiones por capacidad. Su temperatura puede ser NaN y no se lee para
calcular intercambios. Robin exterior incluye Δn/(2k)+1/h, igual que E06.
Se registra cota local C_i/sum(G), balance de potencia y energía sensible.
En una máscara completa, potencia, energía y cota coinciden con CartesianSystem
para campos no uniformes y Robin/adiabático. En dos materiales, los intercambios
internos son iguales y opuestos. **Este ensamblaje no contiene un solve transiente.**

## Activación y edad

PourEvent admite ID, tiempo [s], colocación [°C], Material y AdiabaticCurve.
El JSON permite modificar propiedades e hidratación por evento; si se omiten
usa los valores globales. Cada ID tiene un evento. Se ordenan por (tiempo,ID)
y los simultáneos se activan juntos. Los eventos de t=0 se procesan al crear
ConstructionState; los posteriores con advance_to. No se aplican dos veces.

Al activarse se inicializan únicamente las celdas nuevas. Las anteriores
mantienen su temperatura, incluso si un futuro integrador ya la modificó.
El material recién colocado aporta capacidad y energía: esa entrada no debe
confundirse con calor de hidratación ni con conservación en un sistema cerrado.
La edad real es t−t_activación; antes del evento pour_age devuelve None.
active_mask(t) puede consultar el calendario, pero no inicializa temperaturas;
para un estado físico se debe avanzar hasta ese tiempo.

time_grid divide intervalos en los eventos exactos y produce pasos no mayores
que max_step. advance_to rechaza saltar un evento intermedio o retroceder.
Es un calendario de demostración, no un integrador térmico: max_step no se
presenta como paso térmico estable. Las superficies se reclasifican al activar.

## Hidratación preliminar y unidades

Se eligió una curva prescrita con potencial finito y derivada continua nula
en inicio y agotamiento. Para edad a y duración τ, con u=clip(a/τ,0,1):

    ξ(a) = [1 − cos(πu)]/2
    q_dot_h(a) = H_vol π/(2τ) sin(πa/τ), si 0<a<τ; cero fuera.
    T_ad(a) = T_colocación + H_vol ξ(a)/(rho cp)

ξ representa la fracción liberada de calor potencial del modelo; no una
medición del grado químico real del hormigón. H_vol [J/m³] por dξ/dt [1/s]
produce q_dot_h [W/m³]. Su integral total es exactamente H_vol; released
calcula H_vol[ξ(a1)−ξ(a0)] sin sobrepasar el calor disponible.
Las pruebas usan integral trapezoidal independiente y derivada de T_ad para
comprobar q_dot_h=rho·cp·dT_ad/dt. Esa relación supone aislamiento y capacidad
constante apropiada, con edad medida desde la colocación.

Valores ilustrativos: H_vol=64,8 MJ/m³, τ=172800 s, rho=2400 kg/m³,
cp=900 J/(kg K), aumento adiabático potencial 30 K. No son una calibración
de Freirina. Una fuente uniforme arbitraria de E05 no es esta curva por edad.

q_dot_h(t,T,material,estado) usa HydrationContext(curva,activación). Devuelve
cero antes de activación y después de agotar el potencial. La nueva vertida
reinicia su propia edad; no reinicia la anterior. **No se implementa dependencia
de temperatura, Arrhenius ni edad equivalente.** Cambiar T, manteniendo edad,
no cambia la fuente. Se valida Celsius físico; no hay exponentes con Kelvin.
Una extensión cinética deberá convertir T_K=T_C+273,15 y justificar parámetros
antes de activar una dependencia térmica. No se declara implementada esa extensión.

## Límites y siguiente paso

La integración BIM→grilla, la clasificación de contactos y el ensamblaje están
implementados y probados. Falta el integrador transiente enmascarado con
fuente por edad, sincronización de eventos y balance de inserción térmica.
Su implementación queda fuera de lo que E07 presenta como ejecutado.
Tampoco se implementaron clima, calibración de hidratación, resistencias de
contacto, optimización constructiva ni etapas E08–E15. El commit formal E06
permanece pendiente y E07 no se presenta como repositorio publicado.
