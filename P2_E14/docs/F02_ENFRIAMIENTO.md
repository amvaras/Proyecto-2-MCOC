# F02 · Enfriamiento interno del hormigón

`moderate_20` se evaluó con las ocho curvas, tres historias meteorológicas, IFC
y pesos E14. Los ocho planes anteriores exceden el 5 %. El plan nuevo no produjo
fallas en los 24 escenarios discretos. Esto describe el modelo condicional,
sin cuantificar la confiabilidad de los equipos ni certificar el riesgo real.
La comparación no demuestra optimalidad global.

## Modelo y datos

La [configuración explícita](../configs/f02/moderate_20.json) guarda calendario,
aislación y geometría de los ramales. La composición, propiedades y escenarios
proceden de E14. Los 5 °C de colocación, 50 m³/h, agua a 20 °C,
diámetros de 32/26 mm y 0,25 L/s por ramal son supuestos de diseño.
Los 29 ramales se trazan en cinco niveles de las vertidas 3 a 5. La longitud
activa es 198,62 m. El paso recto al moldaje necesitaría unos 119 m adicionales
de conexión térmicamente aislada, más los colectores externos.

La extensión reutiliza el integrador explícito E08. Cada segmento intercambia
calor con agua advectada según un modelo de intercambiador de flujo pistón.
La resistencia lineal suma convección interior (Gnielinski), pared cilíndrica
y conducción local al radio equivalente de la celda. Para cada segmento,
`UA = longitud / resistencia lineal` y
`Tout = Tc + (Tin - Tc) exp(-UA/(ṁ cp))`.
El término `ṁ cp (Tout - Tin)` se resta localmente del hormigón. El balance
separa el calor ganado por el agua del flujo exterior. Se añade la conductancia
a la cota de paso, con eventos exactos para horario, capas y retiro.
Se desvían ramales con intercambio neto hacia el hormigón. El techo de potencia
del ensayo es 35 kW. La demanda calculada en los controles finos llegó a 12 kW.

La enumeración usa `Tmax > 70 °C OR ΔTmax > 20 °C`, con las dos temperaturas
del diferencial tomadas en el mismo instante. La malla oficial da Tmax 49,599 °C,
ΔTmax 19,158 °C y Pf 0 %. El peor control de discretización da ΔTmax
19,621 °C, un margen de aproximadamente 0,379 °C. Se refinaron por separado
la malla y el paso en las tres historias de M4_SS. El horizonte es 744 h,
con 72 h posteriores al retiro. Los 14,738 h corresponden a la colocación
y sus esperas. La instalación anterior a t₀ y el curado quedan fuera de D.

[Tabla comparativa de los nueve planes](../results/f02/planes.csv) · [Verificación numérica](../results/f02/verification.json)

## Reproducir

Desde `P2_E14`, con Python 3.12 y las dependencias del README:

```bash
python -m pip install -r requirements-lock.txt
python -m pip install --no-build-isolation --no-deps -e '.[dev,plot,bim,viz]'
python scripts/run_f02.py --workers 4 --output results/f02_repro
python scripts/run_f02.py --workers 3 --controls --output results/f02_repro
python scripts/verify_f02.py --output results/f02_repro
mkdir -p .runtime
python -m pytest -q -p no:cacheprovider --basetemp .runtime/pytest-f02 tests
python web/servidor.py
```

El panel lee los artefactos integrados de `results/f02`. El manifiesto registra
la fecha UTC, la base E14 y una huella SHA-256 del kernel, datos y configuración.
Los campos del visor son los del escenario M4_SS_m17 de la propia simulación,
incluidos los instantes de Tmax y del diferencial máximo. La comparación
usa enumeración ponderada sin IC. Pf(N) e IC del estudio anterior siguen en E14.

## Validación pendiente en obra

El IFC acredita espacio geométrico preliminar. Se requiere diseño de armaduras,
juntas, pasadas y colectores, prueba hidráulica, control de fugas, disponibilidad
de agua y capacidad de mantener 20 °C a 7,25 L/s. El margen obliga a comprobar
variaciones de caudal, temperatura de entrada, paradas y desempeño del
aislamiento. Se necesita además validar el suministro de hormigón frío y
el enfriamiento local alrededor del tubo con instrumentación.

S25 se reconstruye bajo la frontera voxelizada. Se verificó la profundidad
respecto de los planos IFC y se repitió localmente la reconstrucción del punto
gobernante de los controles finos a 25 mm del lateral real. Esto no resuelve
globalmente la frontera curva o escalonada. El riesgo se calcula con el
criterio discreto vigente y conserva su diferencial más exigente.
