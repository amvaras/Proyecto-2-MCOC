# E01 — Guía de estudio individual

Leer personalmente G00/G01/G02/G05 y ejecutar el proyecto. Este documento ayuda
a estudiar; no reemplaza esas lecturas ni demuestra comprensión individual.
Evaluación del 21 de octubre de 2026: física 1,0; BIM/IFC 0,7; explicación del
código 0,8; repositorio real y reproducible 0,5. Total 3 puntos.

En cada tema se incluye concepto, respuesta breve, ejemplo y ruta de código.
Las rutas se expresan respecto de la raíz del repositorio.

## 1. BIM

**Concepto:** método de representar y gestionar información del activo, con
objetos, propiedades y relaciones a lo largo del proyecto.
**Respuesta:** «BIM organiza información de lo que se construye; no es un programa».
**Ejemplo:** una vertida tiene nombre, GUID, material y posición, además de forma.
**Referencia:** `scripts/create_preliminary_ifc.py:create_model`.

## 2. IFC

**Concepto:** Industry Foundation Classes, estándar abierto de datos del entorno
construido; admite entidades, relaciones, geometría y propiedades.
**Respuesta:** «IFC permite intercambiar el modelo BIM sin depender de una aplicación».
**Ejemplo:** IfcFooting `Vertida_03`, con GUID y cotas.
**Referencia:** `geometry/foundation.ifc`; `scripts/check_ifc.py:inspect_model`.

## 3. Blender

**Concepto:** aplicación 3D que aporta modelado, navegación y visualización.
**Respuesta:** «Blender es la interfaz geométrica sobre la que funciona Bonsai».
**Ejemplo:** vista superior para inspeccionar el octágono.
**Referencia:** `docs/IFC_BONSAI.md`; uso de interfaz aún pendiente.

## 4. Bonsai

**Concepto:** agrega autoría BIM e interacción nativa con entidades y datos IFC
al entorno de Blender.
**Respuesta:** «Bonsai aporta identidad, clases y relaciones BIM a la geometría».
**Ejemplo:** consultar Name y clase IfcFooting de una vertida y guardar el IFC.
**Referencia:** `docs/IFC_BONSAI.md`; no afirmar que se utilizó su interfaz todavía.

## 5. IfcOpenShell

**Concepto:** biblioteca que permite leer/escribir IFC y obtener su geometría
resuelta, incluidas representaciones y transformaciones.
**Respuesta:** «Es el puente entre IFC y Python normal».
**Ejemplo:** `create_shape` devuelve triángulos para verificar dimensiones y volumen.
**Referencia:** `scripts/check_ifc.py:inspect_model` y `create_preliminary_ifc.py`.

## 6. BIM y geometría 3D

**Concepto:** una malla solo tiene forma; un elemento BIM además tiene identidad,
clase, propiedades y relaciones.
**Respuesta:** «Un cilindro dibujado no es automáticamente una entidad BIM».
**Ejemplo:** el pedestal es un IfcFooting con GUID, material y contenedor espacial.
**Referencia:** `create_model`, asignaciones de material y contenedor.

## 7. Independencia del solver

**Concepto:** separar autoría, lectura de geometría, discretización y física.
**Respuesta:** «La ecuación se resuelve con Python y NumPy, sin abrir Blender».
**Ejemplo:** los tests térmicos corren aunque no esté instalado IfcOpenShell.
**Referencia:** imports de `src/mcoc_p2/diffusion_1d.py`; extras en `pyproject.toml`.
La futura conexión IFC → solver no está implementada en E01.

## 8. Conductividad k

**Concepto:** relaciona gradiente y flujo por Fourier, q=-k grad(T), W/(m K).
**Respuesta:** «A igual gradiente, mayor k transporta más calor».
**Ejemplo:** en el benchmark se usa k=2, valor ilustrativo, no medido para Sarco.
**Referencia:** `Material.k`, cálculo `exchange` dentro de `solve`.

## 9. Densidad rho

**Concepto:** masa por volumen [kg/m³]. Influye en la capacidad térmica volumétrica.
**Respuesta:** «Más masa en la misma celda requiere más energía para calentarla».
**Ejemplo:** rho=2400 kg/m³, ilustrativo.
**Referencia:** `Material.rho`, variable `capacity` de `solve`.

## 10. Calor específico cp

**Concepto:** energía por masa por aumento de temperatura [J/(kg K)].
**Respuesta:** «cp indica cuánta energía necesita un kilogramo para subir un grado».
**Ejemplo:** cp=900 J/(kg K); un kg necesita 900 J para subir 1 K bajo esta hipótesis.
**Referencia:** `Material.cp` y test `test_material_units_and_derived_diffusivity`.

## 11. Difusividad alpha

**Concepto:** alpha=k/(rho cp) [m²/s], balance entre transporte y almacenamiento.
**Respuesta:** «Controla la rapidez con que se redistribuye una perturbación térmica».
**Ejemplo:** alpha≈9,2593e-7 m²/s; escala de difusión L²/alpha para L=1 m.
**Referencia:** propiedad `Material.alpha`, siempre calculada desde k, rho, cp.
Igual alpha no implica igual aumento de temperatura por una fuente en W/m³.

## 12. Balance de energía

**Concepto:** acumulación = entradas - salidas + generación.
**Respuesta:** «Cada celda almacena la suma de potencias que recibe».
**Ejemplo:** conducción desde vecinos, fuente interna y pérdidas hacia el aire.
**Referencia:** `solve`, variables `exchange`, `power`, `capacity`;
`docs/FORMULACION_1D.md` contiene la derivación.

## 13. Ecuación de difusión

**Concepto:** rho cp dT/dt = k d²T/dx² + q_dot, para material constante.
**Respuesta:** «La curvatura espacial y la fuente determinan el cambio temporal».
**Ejemplo:** un máximo local sin fuente se enfría hacia sus vecinos más fríos.
**Referencia:** actualización de `temperature` en `solve` y test del seno.

## 14. Condición inicial

**Concepto:** distribución T(x,0) desde la que evoluciona el sistema.
**Respuesta:** «Indica a qué temperatura parte cada posición».
**Ejemplo:** 20+10 sin(pi x/L), pico de 30 °C en el centro.
**Referencia:** argumento `initial` de `solve` y `examples/run_diffusion_1d.py`.
Si contradice un Dirichlet, se impone el Dirichlet desde t=0; está documentado.

## 15. Dirichlet

**Concepto:** temperatura superficial impuesta, intercambio ideal con reservorio.
**Respuesta:** «Fijo T en el borde, no su flujo».
**Ejemplo:** ambos extremos a 20 °C para el benchmark exacto.
**Referencia:** `Dirichlet`, imposición inicial y tras cada paso en `solve`.

## 16. Neumann

**Concepto:** flujo normal saliente prescrito [W/m²], -k grad(T)·n=q_out.
**Respuesta:** «Fijo cuánto calor atraviesa la frontera; cero es adiabático».
**Ejemplo:** Neumann(-100) agrega 100 W por cada m² de esa cara.
**Referencia:** `Neumann`; test `test_neumann_sign_and_energy_on_either_face`.
La normal cambia entre lados; la convención saliente de la API no cambia.

## 17. Robin

**Concepto:** intercambio convectivo q_out=h(T_s-T_amb).
**Respuesta:** «El flujo depende de la diferencia entre superficie y aire».
**Ejemplo:** h=12 W/(m² K), T_s=50 °C y aire a 20 °C: salen 360 W/m².
**Referencia:** `Robin`, `stable_timestep` y test de balance Robin por paso.
No se iguala T_s con T_amb; un ambiente más caliente hace entrar calor.

## 18. Discretización espacial

**Concepto:** reemplaza el continuo por nodos de distancia dx=L/(nx-1).
**Respuesta:** «Aproximo los gradientes mediante diferencias entre vecinos».
**Ejemplo:** 81 nodos en 1 m → dx=0,0125 m.
**Referencia:** `solve`, `_widths`. Extremos representan media celda; los
interiores una celda completa. La suma de sus anchos es L.

## 19. Discretización temporal

**Concepto:** Euler hacia adelante aproxima dT/dt por (T_nuevo-T_viejo)/dt.
**Respuesta:** «Avanzo la temperatura con pasos de tiempo finitos».
**Ejemplo:** dt=67,5 s para llegar a 24 h en 1280 pasos.
**Referencia:** cálculo de `steps` y `actual_dt` en `solve`; nunca se excede t_end.

## 20. Esquema explícito

**Concepto:** todos los flujos de un paso se evalúan con el estado anterior.
**Respuesta:** «Calculo directamente el siguiente estado, sin resolver un sistema lineal».
**Ejemplo:** `exchange` se calcula antes de actualizar todo el vector T.
**Referencia:** bucle de `solve`. Reutilizar temperaturas ya actualizadas en
el mismo paso cambiaría el esquema y podría romper el balance.

## 21. Número de Fourier

**Concepto:** Fo=alpha dt/dx², adimensional para el paso numérico.
**Respuesta:** «Compara difusión durante un paso con el tamaño de la grilla».
**Ejemplo:** Fo=0,4 en el benchmark. No confundir con alpha*t/L² del problema global.
**Referencia:** `Solution.fourier` y `stable_timestep`.

## 22. Estabilidad

**Concepto:** impedir la amplificación numérica no física de perturbaciones.
**Respuesta:** «El paso debe respetar la cota del balance implementado».
**Ejemplo:** Fo≤0,5 para difusión/Neumann; en Robin se exige además
Fo*(1+h dx/k)≤0,5 por la media celda superficial.
**Referencia:** `stable_timestep` y tests que rechazan dt excesivo con Robin.
Reducir dx a la mitad exige aproximadamente dt/4 para difusión. Una solución
estable puede tener mucho error; por eso se mide error frente a soluciones exactas.

## 23. Conservación de energía

**Concepto:** los intercambios internos se cancelan al sumar balances de celdas.
**Respuesta:** «Sin fuentes ni flujo exterior, la energía total se mantiene».
**Ejemplo:** perfil inicial no uniforme se suaviza sin cambiar la energía ponderada.
**Referencia:** `energy_per_area`; test `test_nonuniform_adiabatic_conserves_weighted_energy`.
Usar media aritmética de todos los nodos sería incorrecto por las medias celdas.

## 24. Unidades y generación

**Concepto:** dt*q_dot/(rho cp) tiene unidades K; q_dot no es un incremento de T.
**Respuesta:** «Convierto potencia volumétrica a variación térmica usando la capacidad».
**Ejemplo:** fuente 1200 W/m³ durante 3600 s produce 2 °C de aumento uniforme
si ambos extremos son adiabáticos y rho cp=2.160.000 J/(m³ K).
**Referencia:** `solve(q_dot=...)`, test `test_uniform_source_adiabatic_matches_exact_rise`.
La energía se mide respecto de Tref; el solver no acepta magnitudes con unidades
automáticas, por lo que el usuario debe ingresar SI.

## Funciones y datos que cada integrante debe recorrer

| Función/clase | Responsabilidad y razón |
|---|---|
| Material | Valida k/rho/cp positivos finitos; deriva alpha consistentemente |
| Dirichlet/Neumann/Robin | Datos inmutables de las tres condiciones físicas |
| stable_timestep | Cota de monotonía de difusión más convección en media celda |
| _finite | Detecta parámetros no finitos o no positivos cuando corresponde |
| _field | Convierte escalar/vector al perfil espacial y valida forma y finitud |
| _widths | Define dx interiores y dx/2 extremos para volumen y energía |
| solve | Valida, aplica condición inicial, calcula flujos con T vieja y avanza |
| Solution | Agrupa posiciones, instantes, temperaturas, dt, Fo y número de pasos |
| energy_per_area | Integra energía sensible con los pesos correctos |
| run_diffusion_1d.main | Ejecuta benchmark, calcula error, guarda figura y datos |
| octagonal_frustum | Construye cuatro volúmenes poliédricos cerrados |
| create_model | Jerarquía IFC, unidades, entidades, material y representaciones |
| stable_guid | Mantiene identidad de objetos al reconstruir la geometría docente |
| inspect_model | Valida esquema, entidades, GUID, contenedores, cotas y volumen |
| verify_e01.main | Ejecuta las comprobaciones y guarda salidas y huellas reales |

## Preguntas difíciles

- **¿Por qué aparece 2Fo en el extremo?** La capacidad corresponde a dx/2;
  la distancia al vecino sigue siendo dx. Dividir por media capacidad duplica
  el efecto de esa conducción y del flujo superficial.
- **¿Fo=0,49 siempre es estable?** No con Robin suficientemente fuerte. Hay que
  evaluar h dx/k. Tampoco se generaliza a fuente dependiente de T o material variable.
- **¿Por qué no copiar dt_diff y dt_conv por separado?** La conducción y convección
  actúan simultáneamente en el coeficiente propio: se suman sus conductancias.
- **¿Un sistema adiabático conserva T en cada punto?** Solo si era uniforme y sin
  fuente. Un perfil no uniforme cambia conservando la energía total.
- **¿Si fijo ambos extremos, se conserva energía?** Hay intercambio con reservorios;
  no es un dominio aislado. En estado estacionario la conducción puede persistir.
- **¿Qué mide el test seno?** Error frente a una solución exacta de la PDE y
  reducción de error al refinar con dt proporcional a dx².
- **¿Qué verifica el modo Robin?** Una solución exacta con convección cuyo
  parámetro h se elige mediante h=k*mu*tan(mu)/L. No se ajusta a una salida numérica.
- **¿Verificación es validación?** Verificar: resolver bien la ecuación propuesta.
  Validar: contrastar el modelo físico con mediciones del sistema real.
- **¿El IFC alimenta ya el solver?** No; E01 entrega ambos componentes por separado.
- **¿Por qué el pedestal mide 6,999 m en un bounding box?** La representación IFC
  tiene un círculo exacto de diámetro 7 m; el motor lo tesela al leer geometría.
- **¿Por qué no declarar los límites cumplidos si el máximo del gráfico es 30 °C?**
  El gráfico representa una barra ideal sin hidratación, no la fundación real.
- **¿Quién comprobó Bonsai?** Nadie todavía en esta sesión. Se debe completar
  la revisión humana y registrar las versiones y capturas sin alterar esa evidencia.
- **¿Qué commit se evalúa?** Solo el nuevo SHA publicado que incluya esta E01.
  El HEAD inicial no contiene esta implementación; no debe entregarse como tal.

## Errores frecuentes

- Llamar BIM a cualquier malla 3D o atribuir a Blender la autoría IFC sin Bonsai.
- Guardar solo `.blend` y esperar que el `.ifc` se actualice.
- Confundir radio al vértice con apotema del octágono: 18 m es entre caras.
- Confundir k con alpha, fuente W/m³ con flujo W/m², días con segundos o m con mm.
- Multiplicar la fuente física por Fo en vez de usar dt*q_dot/(rho cp).
- Igualar la superficie al aire en un Robin o invertir el signo del lado izquierdo.
- Hacer cambios in situ mezclando T vieja/nueva o sumar energía sin pesos.
- Declarar precisión porque el esquema es estable o certificar todo con un gráfico.
- Confundir un archivo preparado localmente con un commit existente en GitHub.

## Demostración de menos de dos minutos

Preparar el entorno antes de entrar; abrir el README, solver, tests, figura e IFC.
Los siguientes comandos usan el entorno ya instalado y no requieren red:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe examples/run_diffusion_1d.py
.\.venv\Scripts\python.exe scripts/check_ifc.py geometry/foundation.ifc
```

1. **0–20 s:** mostrar README, caso G2 y alcance; separar el benchmark de la predicción real.
2. **20–50 s:** abrir `solve`; explicar capacidad, intercambio por interfaces,
   fuente, medias celdas y restricción Robin. Mostrar una función de test de energía.
3. **50–75 s:** ejecutar tests y ejemplo. Leer el resultado real de pytest, Fo
   y error. Mostrar el PNG con el perfil inicial y su decaimiento.
4. **75–100 s:** ejecutar `check_ifc.py`. Identificar cinco IfcFooting, nombres,
   GUID y cotas. Abrir el modelo en Bonsai si el grupo ya completó la preparación
   humana; declarar con precisión qué se comprobó allí.
5. **100–120 s:** mostrar el SHA remoto autorizado que efectivamente contenga E01
   y copiarlo a Canvas. Si no se ha publicado aún, explicar ese pendiente.
