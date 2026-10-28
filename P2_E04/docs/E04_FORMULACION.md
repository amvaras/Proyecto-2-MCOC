# Balance y discretización E04

## Dominio, incógnitas y unidades

Caja cartesiana uniforme por eje. La temperatura T_i está en el centro del
voxel: dx=Lx/nx, distinto del solver nodal E01 con dx=L/(nx-1). Todas las
celdas tienen volumen completo V=dx dy dz, incluidas las de borde. En 2D se
toma espesor de 1 m y en 1D sección de 1 m² en las direcciones omitidas.

| Magnitud | Unidad |
|---|---|
| k | W/(m K) |
| rho | kg/m³ |
| cp | J/(kg K) |
| alpha=k/(rho cp) | m²/s |
| C_i=rho_i cp_i V | J/K |
| G_ij, conductancia | W/K |
| q_dot, generación por volumen | W/m³ |
| q_out, flujo superficial saliente | W/m² |
| h | W/(m² K) |

T se expresa en °C y las diferencias coinciden con K. Tiempo en segundos.

## Balance de un voxel y actualización

Almacenamiento = conducción desde vecinos + generación − pérdidas externas:

```text
C_i dT_i/dt = sum_j G_ij (T_j-T_i) + q_dot_i V - sum_f q_out,f A_f

T_i_new = T_i + dt/C_i * [sum_j G_ij(T_j-T_i)
                         + q_dot_i V - sum_f q_out,f A_f]
```

`power` evalúa todas las potencias con T vieja antes de actualizar. Cada
intercambio interno se suma a una celda y se resta a su vecina. Al sumar los
balances se cancelan las caras internas, salvo redondeo. Un voxel 3D interior
tiene seis vecinos; una celda 2D, cuatro.

En material homogéneo, G_x=k dy dz/dx, y el interior recupera FTCS:

```text
T_new = T + rx*(T_x+ - 2*T + T_x-)
          + ry*(T_y+ - 2*T + T_y-)
          + rz*(T_z+ - 2*T + T_z-) + dt*q_dot/(rho*cp)
ra = alpha*dt/da²
```

En 2D se omite z. Cada incremento tiene unidades K. La fuente no se multiplica
por Fourier: se integra sobre V. Un flujo se integra sobre A. La radiación
solar actuaría como flujo superficial y la hidratación como generación interna;
ninguna está modelada aquí.

## Dos materiales

Contacto perfecto, sin resistencia de contacto adicional. Se suman las dos
resistencias desde centros hasta la interfaz:

```text
R_ij = (dx/2)/(k_i*A) + (dx/2)/(k_j*A)
G_ij = 1/R_ij = k_armonica*A/dx
k_armonica = 2*k_i*k_j/(k_i+k_j)
```

La capacidad usa rho y cp locales. Promediar k aritméticamente no reproduce
la resistencia de dos capas. Una resistencia de contacto por unidad de área
R_contacto agregaría R_contacto/A; esa extensión no está implementada.
Las interfaces deben coincidir con caras de grilla. Los campos de propiedades
siguen las reglas de broadcasting de NumPy, p. ej. k(x) con forma (nx,1,1).

El test independiente usa L1=L2=0,5 m, k1=1, k2=4, caras a 60/20 °C:
q=40/(0,5/1+0,5/4)=64 W/m². El perfil lineal por tramos permanece estacionario.

## Caras externas, signos y esquinas

Normal exterior n, q_out=-k grad(T)·n: positivo enfría, negativo aporta.
En x- la normal es -ex y en x+ es +ex. La API ya usa flujo saliente en ambas;
no invertir manualmente el signo del argumento al cambiar de cara.

**Neumann:** flujo prescrito. q_out=0 representa adiabático o simetría si esta
se justifica físicamente. Una celda adyacente a una cara adiabática puede
seguir cambiando por otras caras o por fuentes.

**Dirichlet:** T_b en la cara, a dx/2 del centro. G_b=k_i A/(dx/2) y
P_out=G_b(T_i-T_b). Se avanza la temperatura del centro sin reemplazarla por
T_b. El reservorio puede suministrar o extraer energía.

**Robin:** q_out=h(T_s-T_inf). Conducción de media celda y película convectiva
actúan en serie; T_s es superficie, T_inf es aire:

```text
R_media = dx/(2*k_i)                         [m² K/W]
g_efectivo = h/(1+h*R_media)                 [W/(m² K)]
G_b = A*g_efectivo                          [W/K]
P_out = G_b*(T_i-T_inf)
T_s = T_i - (P_out/A)*R_media
```

Así se satisfacen conducción y convección simultáneamente. h=0 recupera
adiabático; h creciente sin límite tiende a Dirichlet en la cara.
En aristas y esquinas se suman las potencias de cada cara incidente antes
de actualizar. No se sobrescribe una condición con otra ni se duplica una cara.

## Estabilidad: derivación y alcance

Agrupar los coeficientes del balance lineal:

```text
T_i_new = [1-dt*(sum_j G_ij+sum_f G_b,f)/C_i]*T_i
          + sum_j dt*G_ij/C_i*T_j + términos prescritos
```

Para tener coeficientes no negativos, una cota suficiente de monotonía es:

```text
dt <= min_i C_i/(sum_j G_ij+sum_f G_b,f)
```

Neumann constante aporta potencia pero no G_b. Una fuente prescrita tampoco
modifica los coeficientes. Con fuente dependiente de T, radiación o propiedades
variables en tiempo se debe analizar el nuevo sistema.

En interiores homogéneos: rx+ry+rz<=1/2. Con pasos iguales, r<=1/4 en 2D y
r<=1/6 en 3D. **Las caras también importan:** Dirichlet está a media celda.
Una esquina con todas sus caras Dirichlet tiene suma 3kA/dx por eje y la cota
cúbica local es dx²/(3*d*alpha). El código calcula todas las celdas y elige la
más restrictiva. Esta cota es suficiente, no necesariamente el límite espectral.

El dt solicitado debe ser admisible. Después se toma ceil(t_end/dt) y se reduce
uniformemente el paso para llegar exactamente al final. Estabilidad no garantiza
precisión. La discretización interior tiene error O(dt+dx²) para campos suaves.

## Verificación

Seno con todas las caras a T0, omitiendo ejes ausentes:

```text
T = T0 + A*prod_a sin(pi*x_a/L_a)
         *exp[-alpha*pi²*sum_a(1/L_a²)*t]
```

El estudio espacial usa dt fijo pequeño y n=6/12/24. Para aislar el error
temporal se compara contra el sistema espacial semidiscreto exacto con
lambda_h=sum_a 4*alpha/da²*sin(pi/(2*n_a))², n=6 y dt=500/250/125 s.
Se verifican por separado conservación, fuente, seis caras con Neumann,
Robin con modo coseno, calentamiento/enfriamiento y balances en esquinas.

Los ejemplos no validan un hormigón real. El IFC sigue separado del solver.
El mínimo de centros de una caja no equivale al valor a 25 mm bajo superficie
exigido por el caso final. Eso se resolverá al integrar geometría y grilla,
cuando lo exija el enunciado correspondiente.
