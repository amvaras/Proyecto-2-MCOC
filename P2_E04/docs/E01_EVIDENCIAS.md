# Evidencias técnicas E01 — auditoría del 20 de octubre de 2026

Los registros actuales se encuentran en `docs/evidencias/auditoria/`. Su corrida
integral terminó el **2026-10-20 a las 17:52:31 UTC**, 14:52:31 en Santiago.
La copia previa se preservó en `docs/historico/pre_auditoria_20261020T174429Z/`;
las salidas iniciales directamente bajo `docs/evidencias/` siguen conservadas.
No se sustituyen resultados históricos por resultados fabricados.

## Entorno efectivamente reconstruido

Windows AMD64, **CPython 3.12.10**, entorno nuevo `.venv-audit` con
`include-system-site-packages = false`. Dependencias principales:

| Biblioteca | Versión |
|---|---|
| NumPy | 2.5.4 |
| Matplotlib | 3.11.2 |
| pytest | 9.1.1 |
| IfcOpenShell | 0.9.0.post1 |

Las **24 entradas** de `requirements-lock.txt`, incluidas las transitivas y
herramientas de instalación, coinciden con lo instalado. `pip check` devolvió
`No broken requirements found.` El motor geométrico y el validador EXPRESS de
IfcOpenShell se ejecutaron, no solo sus imports.

Se instaló sin consultas de red desde ruedas disponibles localmente. En el
primer intento faltaba en el almacén local la rueda de setuptools 84.2.0;
la instalación se detuvo con código 1 antes de instalar. Se exportó esa rueda
desde la distribución local comprobada, contrastando 349 archivos con su RECORD,
y se repitió la instalación: código 0. Esto fue una limitación del almacén local,
no un conflicto del proyecto. Las demás ruedas procedieron de la caché local
y del paquete ensurepip. No se cambió ninguna versión fijada.

La prueba demuestra reconstrucción local desde las versiones declaradas y los
paquetes disponibles. No afirma una nueva descarga desde un índice remoto,
ni portabilidad a otros sistemas operativos. Las instrucciones generales de
instalación están en README; el suministro local de ruedas permitió comprobarlas
sin acceder a servicios externos.

Comandos ejecutados en esta auditoría, desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --junitxml=results/auditoria_inicial/pytest.xml
.\.venv\Scripts\python.exe -m pytest -q --junitxml=results/auditoria_corregida/pytest.xml
py -3.12 -m venv .venv-audit
.\.venv-audit\Scripts\python.exe -m pip install --no-index --find-links results/auditoria_entorno/wheelhouse -r requirements-lock.txt
.\.venv-audit\Scripts\python.exe -m pip install --no-index --no-build-isolation --no-deps -e '.[dev,plot,bim]'
.\.venv-audit\Scripts\python.exe scripts/verify_e01.py
```

`verify_e01.py` ejecutó con el Python del nuevo entorno:

```powershell
python -m pip check
python -m pytest -q --junitxml=docs/evidencias/auditoria/pytest.xml
python examples/run_diffusion_1d.py --output docs/evidencias/auditoria
python scripts/check_diffusion_accuracy.py --benchmark docs/evidencias/auditoria --json docs/evidencias/auditoria/accuracy.json
python scripts/check_ifc.py geometry/foundation.ifc --json docs/evidencias/auditoria/ifc_check.json
python scripts/render_ifc_preview.py --output docs/evidencias/auditoria/foundation_preview.png
python scripts/check_bonsai_evidence.py --json docs/evidencias/auditoria/bonsai_evidence.json
```

Todos devolvieron código 0. Los logs `instalacion.txt`,
`instalacion_editable.txt`, `pip_check.txt` y `environment_rebuild.json`
conservan el detalle del entorno.

## Suite de pruebas

| Momento | Total | Aprobadas | Fallidas/errores | Omitidas | Tiempo de pytest |
|---|---:|---:|---:|---:|---:|
| Inicio de la auditoría | 54 | 54 | 0 | 0 | 6,12 s |
| Tras correcciones y nuevos casos | 67 | 67 | 0 | 0 | 11,99 s |
| Corrida integral en entorno reconstruido | 67 | 67 | 0 | 0 | 12,33 s |

El XML de la última corrida registra 12,323 s y la salida resumida redondea a
12,33 s. `verification.json` extrae del XML los conteos, no los supone.
Los defectos de dx entero y campos complejos se reprodujeron con sondas antes
de corregirlos; la suite anterior no los cubría. No hubo fallos de pytest en
las tres corridas listadas.

Las 13 pruebas agregadas cubren energía con dx entero, rechazo de campos
complejos y perfiles energéticos inválidos, calentamiento Robin, convergencia
temporal aislada, refinamiento espacial con dt pequeño fijo y rechazo de IFC
con cotas de propiedades o jerarquía incorrectas. Las pruebas previas de
conservación, fuente, signos, estabilidad, soluciones analíticas y reconstrucción
IFC permanecen activas.

## Benchmark reproducido e inspección de figuras

L=1 m; nx=81; dx=0,0125 m; k=2 W/(m K); rho=2400 kg/m³;
cp=900 J/(kg K); alpha=9,259259259259259e-7 m²/s. Condición inicial
20+10 sin(pi x/L) °C; Dirichlet 20 °C en ambos extremos; fuente nula.

Resultado real: **86400 s, dt=67,5 s, 1280 pasos, Fo=0,4**.
Solución exacta válida para este problema:
`20+10*sin(pi*x/L)*exp(-alpha*(pi/L)^2*t)`.
Error máximo final: **0,0006451356521708362 °C**, igual al valor anterior.
Las correcciones no modificaron el esquema para estas entradas reales.

Se revisó el código del error, se recalcularon la analítica y el error desde
el NPZ y se verificaron tiempo, condición inicial, extremos y Fo contra JSON.
La figura regenerada se inspeccionó visualmente: perfiles inicial/intermedios/
final, curva del centro y extremos a 20 °C, puntos de solución exacta final.
Es un benchmark de barra ideal; no es la simulación real de Freirina.

## Convergencia independiente

| nx espacial | dx [m] | dt [s] | Error a 10000 s [°C] |
|---:|---:|---:|---:|
| 11 | 0,1 | 1 | 0,006836002272 |
| 21 | 0,05 | 1 | 0,001709884970 |
| 41 | 0,025 | 1 | 0,000424847181 |

Cocientes: **3,997931** y **4,024706**, coherentes con segundo orden espacial
cuando domina ese error.

| nx temporal fijo | dt [s] | Error frente al modo semidiscreto a 100000 s [°C] |
|---:|---:|---:|
| 21 | 1000 | 0,016773061972 |
| 21 | 500 | 0,008369701687 |
| 21 | 250 | 0,004180658684 |
| 21 | 125 | 0,002089283189 |

Cocientes: **2,004021**, **2,002006**, **2,001001**, coherentes con primer orden
de Euler. La referencia semidiscreta elimina el error espacial de esta medición.
Detalles y tolerancias: `accuracy.json`, `FORMULACION_1D.md` y tests.

## Validación IFC automatizada

`geometry/foundation.ifc`, esquema **IFC4**, metros, jerarquía única
IfcProject → IfcSite → IfcBuilding → IfcBuildingStorey. Cinco IfcFooting,
Name Vertida_01–Vertida_05, GlobalId únicos, material preliminar y
UANDES_HormigonMasivo con ID, cotas, procedencia y estado individualizados.
Validación EXPRESS: **0 incidencias**.

| Vertida | Intervalo Z [m] | Volumen analítico [m³] |
|---|---|---:|
| 01 | 0–0,55 | 147,625713630 |
| 02 | 0,55–1,10 | 147,625713630 |
| 03 | 1,10–2,20 | 214,224350900 |
| 04 | 2,20–3,30 | 88,924748282 |
| 05 | 3,30–4,30 | 38,484510006 |

Caja global: (-9; -9; 0) a (9; 9; 4,30) m. Se comprobaron anillos octagonales
inferiores y superiores, radio circular exacto 3,5 m, posición, propiedades Z,
conectividad, no degeneración de triángulos, cierre y orientación consistente.
Las diez parejas tienen interiores separados en Z; se admite contacto de caras.
El cilindro teselado tiene volumen 38,477191141 m³, aproximadamente 0,019 %
menor que el volumen exacto; está dentro de la tolerancia de 0,05 % declarada.
La representación IFC conserva el radio exacto. La tolerancia de bounding box
del círculo es 2 mm, la de cotas octagonales 1e-7 m.

No se cambió la geometría entregada. El verificador y las pruebas ampliadas
controlan más propiedades de la misma geometría existente. Su vista previa
regenerada se inspeccionó como figura de IfcOpenShell/Matplotlib, separada de
las capturas humanas.

## Evidencia humana de Blender/Bonsai

Existen y se inspeccionaron las ocho capturas en `Evidencias/bonsai/`:
`vista_3d.png`, `vista_superior.png`, `vista_perfil.png` y
`propiedades_vertida_01.png` a `propiedades_vertida_05.png`.

Muestran **Blender 5.1.2 / Bonsai v0.9.0-post1**, foundation.ifc/IFC4, cinco
IfcFooting, selección individual, nombres, GlobalId, pset e intervalos Z.
Se observan vistas 3D, Top Orthographic y Back Orthographic. Los prefijos
visibles de GUID coinciden con el IFC; los valores completos están comprobados
automáticamente porque la interfaz los trunca en estas capturas.

`Evidencias/bonsai/revision_visual.json` registra qué se observó en cada imagen.
`check_bonsai_evidence.py` comprueba que los archivos inspeccionados permanecen
idénticos y que los datos transcritos coinciden con el IFC. No sustituye la
inspección visual por reconocimiento automático ni opera la aplicación.
**El auditor inspeccionó las capturas; no realizó una sesión adicional en Blender.**
La apertura y revisión humana ya realizadas quedan acreditadas; no son pendientes.

## Repetición y trazabilidad

```powershell
.\.venv\Scripts\python.exe scripts/verify_e01.py
# O una salida independiente sin cambiar el registro principal:
.\.venv\Scripts\python.exe scripts/verify_e01.py --output results/verificacion_independiente
```

Al reutilizar una carpeta, el verificador preserva sus archivos previos en
`historial/` con fecha UTC antes de generar nuevos resultados. Los estados de
corrida son running, failed o passed y las salidas se derivan de procesos reales.
Las limitaciones actuales son las hipótesis 1D, propiedades constantes y fuente
prescrita; no falta implementar ninguna etapa posterior para cerrar E01.
