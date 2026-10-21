# Formulación y contrato del solver E01

## Hipótesis y unidades

`src/mcoc_p2/diffusion_1d.py` resuelve un único material homogéneo con propiedades
constantes, sección transversal constante y grilla uniforme. Temperatura en °C,
tiempo en s, longitud en m, `k` en W/(m K), `rho` en kg/m³, `cp` en J/(kg K).
Las diferencias de temperatura en °C y K coinciden. No se calculan radiación ni
propiedades que dependan de temperatura absoluta.

`rho*cp` tiene unidades J/(m³ K); `alpha=k/(rho*cp)` tiene m²/s. La fuente `q_dot`
es potencia por volumen [W/m³], independiente de T y del tiempo; admite escalar
o vector espacial de largo `nx`. Un flujo de borde tiene W/m², no W/m³.
La API valida valores finitos y signos físicos; no puede detectar si alguien
ingresa milímetros donde el contrato exige metros.
Los campos complejos se rechazan explícitamente; no se descarta su parte
imaginaria. Los anchos internos se representan como flotantes, por lo que
`energy_per_area(..., dx=1)` admite un paso espacial entero con medias celdas.

## Balance y diferencias finitas

Nodos: `x_i=i*dx`, `dx=L/(nx-1)`, desde 0 hasta L incluidos. Cada nodo representa
una celda de volumen por área `w_i=dx`, salvo los extremos con `w_0=w_N=dx/2`.
Por tanto `sum(w_i)=L`. No son centros de celdas de ancho completo en los bordes.
Se trabaja por unidad de área transversal.

```text
capacidad por área: C_i/A = rho*cp*w_i                   [J/(m² K)]
conducción desde vecino j: k*(T_j-T_i)/dx               [W/m²]
fuente por área: q_dot_i*w_i                            [W/m²]
balance: rho*cp*w_i*dT_i/dt = sum_j k*(T_j-T_i)/dx
                             + q_dot_i*w_i - q_out,i
```

Cada interfaz interna transfiere exactamente la misma potencia con signos
opuestos a los dos vecinos. Al dividir por `rho*cp*w_i` y usar Euler hacia
adelante, para un nodo interior resulta:

```text
T_i^(n+1) = T_i^n + Fo*(T_(i+1)^n - 2*T_i^n + T_(i-1)^n)
                   + dt*q_dot_i/(rho*cp)
Fo = alpha*dt/dx²
```

Es el mismo stencil de diferencias finitas centrales (FTCS). La ecuación
continua es `rho*cp*dT/dt = k*d²T/dx² + q_dot`. Error global esperado:
`O(dt + dx²)` para soluciones suficientemente suaves. Refinando con `dt~dx²`
se espera aproximadamente un factor cuatro en error al dividir dx por dos.

## Bordes y signos

La normal exterior es -x en la izquierda y +x en la derecha. En ambos lados se
define `q_out = -k*grad(T)·n`, positivo cuando el dominio pierde calor.

- `Dirichlet(temperature)`: fija T en el extremo desde t=0, aun si `initial`
  da otro valor. Es un reservorio ideal; su intercambio no se prescribe como
  flujo. No se exige conservación de energía del sólido aislado en este caso.
- `Neumann(outward_flux)`: prescribe `q_out` [W/m²]. Cero significa aislación;
  un valor negativo calienta. No se cambia el signo de la API entre caras.
- `Robin(h, ambient)`: `q_out=h*(T_surface-ambient)`; h [W/(m² K)] no negativo.
  Si la superficie está más fría que el aire, el calor entra automáticamente.
  h=0 equivale a adiabático; `ambient` no se impone sobre la superficie.

En el extremo izquierdo, para Neumann o Robin:

```text
T_0^(n+1) = T_0^n + 2*Fo*(T_1^n-T_0^n)
                  - 2*dt*q_out,0/(rho*cp*dx)
                  + dt*q_dot_0/(rho*cp)
```

En el derecho se reemplaza el vecino por `T_(N-1)`. El factor dos procede de
la media celda, no de duplicar arbitrariamente el flujo.

## Restricción de paso

`stable_timestep` impone una cota suficiente de monotonía: coeficientes no
negativos en Euler explícito. Para interiores y Neumann constante:
`Fo <= 1/2`. En cada Robin, el coeficiente propio es
`1-2*Fo*(1+Bi_dx)`, donde `Bi_dx=h*dx/k`, y se exige:

```text
Fo*(1+Bi_dx) <= 1/2
dt <= dx² / (2*alpha*(1+h*dx/k))
```

Se toma la menor cota de difusión y de los Robin presentes. Es una cota
suficiente conservadora, no una afirmación de necesidad para toda malla.
El solver rechaza el dt solicitado si excede la cota (holgura relativa 1e-12
para redondeo). Luego usa `nsteps=ceil(t_end/dt)` y `dt_real=t_end/nsteps`;
solo lo reduce para terminar exactamente en `t_end`. Si `t_end=0`, devuelve
el estado inicial compatible con los Dirichlet, sin pasos y con Fo=0.

Una fuente prescrita constante no modifica los coeficientes del sistema
homogéneo. Una reacción dependiente de T, h variable, materiales heterogéneos
o una frontera con capacidad propia necesitarían otra derivación. No están
soportados; `Fo<=0.5` no es un criterio universal. Estabilidad tampoco garantiza
precisión: el ejemplo y los tests contrastan soluciones exactas y refinamiento.

## Energía y verificación

`energy_per_area` calcula `E/A=rho*cp*sum(w_i*(T_i-Tref))` [J/m²]. No es energía
absoluta; las diferencias son energía sensible respecto de Tref. Con Neumann o
Robin en ambas caras se satisface discretamente:

```text
Δ(E/A) = dt * (sum(q_dot_i*w_i) - q_out,left^n - q_out,right^n)
```

Sin aportes ni pérdidas permanece constante incluso con perfil no uniforme.
Promediar nodos con pesos iguales produciría un balance incorrecto por las
medias celdas. Los tests verifican este balance a tolerancia de redondeo.

Con fuente uniforme y adiabático: `T(t)=T_initial+q_dot*t/(rho*cp)`.
Con Dirichlet iguales: `T=20+10*sin(pi*x/L)*exp(-alpha*(pi/L)²*t)`.
Con Neumann izquierdo cero y Robin derecho se verifica el modo
`T=20+10*cos(mu*x/L)*exp(-alpha*(mu/L)²*t)`, con
`h=k*mu*tan(mu)/L`, `mu=pi/4`. Son verificaciones del programa, no validación
experimental del hormigón ni predicciones de la fundación.

La auditoría agregó verificaciones independientes de orden. Con dt=1 s fijo,
nx=11/21/41 y t=10000 s, los errores espaciales fueron 0,00683600,
0,00170988 y 0,000424847 °C (cocientes 3,9979 y 4,0247). Para aislar tiempo,
se mantuvo nx=21 y se comparó con la solución exacta del sistema semidiscreto:
`lambda_h=4*alpha*sin(pi/(2*(nx-1)))²/dx²` y amplitud `exp(-lambda_h*t)`.
Con dt=1000/500/250/125 s y t=100000 s, los cocientes de error fueron
2,0040, 2,0020 y 2,0010, coherentes con primer orden temporal. Estas pruebas
complementan el refinamiento conjunto dt~dx². Comando reproducible:

```powershell
python scripts/check_diffusion_accuracy.py --benchmark docs/evidencias/auditoria --json results/accuracy.json
```

El ejemplo usa propiedades ilustrativas (k=2, rho=2400, cp=900) y simula una
barra ideal de 1 m durante 24 h. No representa los 14 días ni evalúa los límites
70 °C/20 °C del caso final.
