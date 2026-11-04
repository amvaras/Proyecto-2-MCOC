# E05 — Guía de laboratorio y parámetros

Jueves 29 de octubre de 2026, 10:30–12:30. Entrar en P2_E05 e instalar según
README. En esta consola PowerShell puede abreviarse el ejecutable:

```powershell
$pyE05 = '.\.venv\Scripts\python.exe'
& $pyE05 examples/run_e05.py --list
& $pyE05 examples/run_e05.py --all --config configs/e05/lab.json
& $pyE05 examples/run_e05.py --category boundary --dim 3 --n 8
& $pyE05 -m pytest tests/test_e05_verification.py --collect-only -q
& $pyE05 -m pytest tests -k robin -q
& $pyE05 -m pytest tests/test_thermal_nd.py::test_anisotropic_stability_limit_and_rejection -q
```

Para un nodo parametrizado concreto, copiar su nombre desde collect-only y
encerrarlo entre comillas. `pytest -m e05` selecciona la capa nueva; ejecutar
`pytest tests -q` conserva también la cobertura heredada.

## Siete casos mínimos

| Caso | Comando después de definir pyE05 | Parámetros relevantes | Referencia y aceptación |
|---|---|---|---|
| A. Exacta 1D | `& $pyE05 examples/run_e05.py --case exact_1d --n 12` | n, L, k/rho/cp, inicial, amplitud, dt, duración | Seno continuo en centros y caras Dirichlet a T0; L∞≤0,03 °C |
| B. Exacta 2D | `& $pyE05 examples/run_e05.py --case exact_2d --shape 12 12 --lengths 1 1` | También nx≠ny y Lx≠Ly | Dos senos, lambda=(pi/Lx)²+(pi/Ly)²; mismo umbral |
| C. Exacta 3D | `& $pyE05 examples/run_e05.py --case exact_3d --shape 12 12 12` | Tres longitudes y resoluciones | Tres senos y suma de curvaturas en los tres ejes |
| D. Adiabático | `& $pyE05 examples/run_e05.py --case energy --dim 3 --n 8 --heterogeneous` | Dimensión, geometría, propiedades y amplitud | Perfil no uniforme: E constante y cancelación de intercambios internos |
| E. Fuente | `& $pyE05 examples/run_e05.py --case source --dim 3 --q-dot 1000` | q_dot positivo/cero/negativo, rho/cp y tiempo | T=T_ini+q_dot*t/(rho cp), ΔE=q_dot*V*t |
| F. Neumann | `& $pyE05 examples/run_e05.py --case neumann --dim 3 --face z- --flux -100` | Cara, signo, intensidad y áreas | ΔE=−q_out*A*t; positivo pierde energía y negativo la aporta |
| G. Robin | `& $pyE05 examples/run_e05.py --case robin --dim 3 --h 12 --initial 50 --ambient 20` | h, ambiente, inicial, cara o todas | Resistencias en serie, balance, ley superficial y máximo |

Cada ejecución produce un destino nuevo con fecha UTC bajo results/e05.
`--output` permite otra carpeta **vacía**; se rechaza sobrescribir evidencia.
summary.json identifica geometría, propiedades, condiciones por cara,
resoluciones, dt solicitado/efectivo/máximo, pasos, Fourier, errores y tolerancias.
solution.npz conserva campos y coordenadas. Las figuras se generan desde esos
campos; los estudios de convergencia tienen JSON y figura log-log.

## Cambios y precedencia de configuración

Las referencias exact_1d/2d/3d fijan su propia dimensión. `--dim` afecta los
otros casos. `--n N` usa N celdas por eje; `--shape nx ny nz` define la malla
explícita. Si se dan ambos, shape prevalece. Cambiar n por CLI sin shape
descarta la shape del JSON. Para spatial, n/shape es la malla inicial y se
duplica por eje; temporal mantiene esa malla y reduce dt.

`--lengths L` repite un valor por eje; una lista debe tener la dimensión exacta.
En una ejecución --all conviene un solo valor o geometrías por caso en JSON.
CLI prevalece sobre cases y cases sobre defaults. Ejemplo editable:

```json
{
  "units": {"length":"m", "time":"s", "q_dot":"W/m^3"},
  "defaults": {"n":12, "k":2.0, "rho":2400.0, "cp":900.0},
  "cases": {
    "exact_3d": {"shape":[8,10,12], "lengths_m":[1.2,0.9,1.6]},
    "energy": {"dimension":3, "heterogeneous":true},
    "robin": {"dimension":3, "initial_C":50.0, "ambient_C":20.0},
    "spatial": {"n":6}, "temporal": {"n":6}
  }
}
```

El archivo completo es configs/e05/lab.json. Se rechazan claves desconocidas,
JSON ilegible y etiquetas incompatibles como mm, min o fuente W/m². Se acepta
UTF-8 con/sin BOM. Sin etiquetas, los números se interpretan en SI; no se puede
detectar que un número declarado en metros fue pensado como milímetros.

Unidades: k [W/(m K)], rho [kg/m³], cp [J/(kg K)], q_dot [W/m³], flux [W/m²],
h [W/(m² K)], temperaturas [°C], tiempos [s]. `--heterogeneous` solo se admite
en energy: cambia k/rho/cp por factores 3/1,15/0,8 en la mitad superior de x,
sin usar una referencia homogénea inválida. Es una prueba, no un hormigón real.
En 1D se supone sección de 1 m²; en 2D, espesor de 1 m.

## Referencias y tolerancias científicas

El núcleo cartesiano usa centros, no nodos en los extremos:
dx=L/n, x_i=(i+1/2)dx. La referencia continua se evalúa allí. Todas las caras
de los casos exactos tienen Dirichlet T0, sin sobrescribir los centros:

```text
T_exact = T0 + A*producto(sin(pi*x_a/L_a))*exp(-alpha*lambda*t)
lambda = suma((pi/L_a)²), alpha=k/(rho*cp)
```

- **L∞:** máximo absoluto de T_num−T_exact en centros [°C].
- **L2 RMS:** sqrt(sum(error²*V)/sum(V)) [°C]; con celdas de volumen igual
  coincide con la raíz de la media de cuadrados.
- **L2 integral:** sqrt(sum(error²*V)). Interpretada en d dimensiones tiene
  unidad °C·m^(d/2); sección/espesor de direcciones omitidas son unitarios.
- **Exactos:** 0,03 °C por defecto, 0,3 % de la amplitud nominal 10 °C.
  Es un umbral explícito de laboratorio, no una tolerancia de la fundación.
  No se calcula a partir del error observado. `--atol-c` admite otro criterio
  si se justifica y queda registrado.
- **Fuente uniforme:** tolerancia de redondeo 1e-11*max(1,abs(T_exact)) °C,
  contrastando todos los tiempos guardados, más el balance energético.
- **Energía:** 1e-7 J + 5e-12*escala_energética. La escala combina capacidad
  total, magnitud de temperatura y energía generada; no depende del residuo.
  El término absoluto cubre cancelaciones cerca de cero y el relativo cubre
  sumas y pasos repetidos en doble precisión.
- **Órdenes:** espacial 2±0,3 con contaminación temporal menor al 10 %;
  temporal 1±0,15. Se permiten efectos preasintóticos de mallas gruesas.
  No se impone un cociente exactamente 4 o 2.

El solver nodal 1D heredado conserva dx=L/(nx−1) y medias celdas de extremos;
no se confunde con la discretización cartesiana E04 usada en estos casos E05.

## Energía, fuente y fronteras

E=sum(rho_i cp_i V (T_i−Tref)). Cada conducción G(T_j−T_i) se suma a i y se
resta a j. La suma de intercambios internos se cancela. La batería comprueba
esa cancelación y el balance de cada paso, incluidos los bordes.

Adiabático sin fuente conserva E; el perfil no uniforme puede suavizarse.
Fuente uniforme adiabática da pendiente q_dot/(rho cp): duplicar q_dot duplica
el incremento y duplicar rho cp lo reduce a la mitad. Una fuente negativa
representa extracción prescrita. No es flujo superficial ni hidratación.

Neumann integra q_out por el área completa de cara. Las longitudes no tienen
por qué ser 1 m: la batería usa también cajas no cúbicas y verifica las áreas.
La normal cambia entre caras, pero el signo de la API sigue siendo saliente.

Robin combina media celda conductiva y película convectiva:

```text
R''=dx_normal/(2*k)+1/h
q_out=(T_cell−T_ambient)/R''
P_out=q_out*A_face
T_surface=T_cell−q_out*dx_normal/(2*k)
```

Para h=0 se usa h/(1+h*dx/(2k)), sin dividir por cero. Al aumentar h el flujo
crece hasta quedar limitado por la conducción centro-cara; no se impone el
ambiente en el centro. En esquinas se suman todas las caras incidentes.
La comparación de h*(T_surface−T_ambient) incluye la amplificación del redondeo
cuando h es enorme; también se contrasta el flujo directamente con resistencias.

## Convergencia y estabilidad

```powershell
& $pyE05 examples/run_e05.py --case spatial --dim 2 --shape 5 7
& $pyE05 examples/run_e05.py --case temporal --dim 3 --n 6
& $pyE05 examples/run_e05.py --case stability --dim 3 --n 8
```

Spatial usa tres mallas, paso fijo de 0,01 veces la cota de la más fina por
defecto y referencia continua. Temporal usa una malla fija, tres pasos y el
modo semidiscreto exacto para eliminar el error espacial de la medición:

```text
lambda_h=alpha*suma(4*sin(pi/(2*n_a))²/dx_a²)
T_semi=T0+A*producto(sin(pi*x_a/L_a))*exp(-lambda_h*t)
```

El paso automático temporal grueso no supera t_end/20; así no colapsan varios
refinamientos a un solo paso cuando cambian k, rho, cp, L o duración. Se usan
los pasos efectivos al calcular el orden. Errores cercanos a redondeo, pasos
que no se refinan y estudios excesivamente costosos se rechazan explícitamente.

En interiores homogéneos, suma(Fo_a)≤1/2. La cota aplicada es siempre
min(C_i/sum(G_i)), con caras y capacidades locales. Dirichlet a media celda
puede ser más restrictivo que el límite interior. Robin aporta conductancias
que se suman en bordes y esquinas. Un paso estable todavía puede ser impreciso.

Controles deliberados:

```powershell
# ERROR por estabilidad, código 2:
& $pyE05 examples/run_e05.py --case exact_3d --dt 1e20
# FAIL de precisión, código 1:
& $pyE05 examples/run_e05.py --case exact_2d --n 3 --atol-c 1e-12
```

Código 0=PASS, 1=FAIL numérico, 2=entrada rechazada. Un cambio extremo puede
invalidar la referencia, superar el costo de laboratorio o incumplir precisión.
Se informa el motivo; no se relaja silenciosamente el criterio para lograr PASS.

## Respuestas breves y navegación por el código real

| Pregunta | Respuesta y referencia |
|---|---|
| ¿Qué verifica el seno? | Difusión transiente y curvaturas por eje con Dirichlet; sine_mode, eigenvalues y run_case |
| ¿Qué son L∞ y L2? | Mayor error puntual y medidas cuadráticas del campo; métricas error_Linf_C, error_L2_rms_C e integral |
| ¿Por qué se conserva E? | Conducciones internas iguales/opuestas; CartesianSystem.power y energy |
| ¿Por qué una fuente constante es lineal? | Potencia y capacidad constantes sin pérdidas; rama source de run_case |
| ¿Neumann frente a Robin? | Flujo impuesto frente a intercambio por temperaturas/resistencias; boundary_heat_rates |
| ¿Qué pasa al aumentar h? | Se aproxima al límite conductivo de media celda; constructor de CartesianSystem |
| ¿Qué pasa al bajar dx? | Baja el error espacial pero dt estable disminuye aproximadamente como dx²; run_convergence |
| ¿Qué pasa al subir dt? | Aumenta el error temporal y puede superar C/sum(G); solve_nd |
| ¿Estabilidad asegura precisión? | No; por eso se necesitan soluciones exactas y refinamientos |
| ¿Cómo se decide PASS? | Checks sobre magnitudes calculadas, referencias y tolerancias explícitas; _check y retorno CLI |
| ¿Dónde se aplica cada frontera? | Constructor calcula G, boundary_heat_rates calcula potencia y face_temperature reconstruye superficie |
| ¿Dónde cambiar parámetros? | JSON/CLI → make_config/load_configuration → _system; no reescribir el solver |

Recorrido: examples/run_e05.py → verification_e05.run_case/checks →
thermal_nd.power/solve_nd → test_e05_verification.py. test_thermal_nd.py
mantiene pruebas de seis caras, materiales y Robin analítico. La capa E05
añade la configuración, las referencias no cúbicas y los resultados PASS/FAIL.
