# E10 · Entorno, moldaje y clima

Grupo 2 · Parque Eólico Sarco, Freirina · −28,856102°, −71,421831°.
La demo usa la geometría IFC, malla, hidratación y cinco vertidas de E09.
[Parámetros de borde](ambiente.json) · [Ejecución verificada](evidencia_demo.json).

El [pronóstico archivado de Freirina](data/weather/forecast-20261111T125009366080Z-3184e5a881e6/metadata.json)
se descargó el 11 de noviembre a las 09:50 de Chile. La
[corrida de 36 h con ese pronóstico](evidencia_forecast.json) verifica estabilidad,
activación de las cinco vertidas y balance de energía. La
[auditoría de cobertura de obra](cobertura_obra.json) registra 0 h de pronóstico
y 336 h de escenario para la ventana del 27 de noviembre al 11 de diciembre.

## Demo oral

Desde la raíz del repositorio en este computador:

```powershell
.\.venv-e09\Scripts\python.exe -X utf8 -B P2_E10/e10.py demo
.\.venv-e09\Scripts\python.exe -X utf8 -B P2_E10/e10.py coverage --hours 336
.\.venv-e09\Scripts\python.exe -X utf8 -B P2_E10/e10.py fetch
```

En otro clon, instale el entorno de [E09](../P2_E09/README.md#instalar-y-probar)
y use `P2_E09\.venv\Scripts\python.exe`. La demo funciona con el
[snapshot docente](data/weather/ejemplo-docente/metadata.json) versionado.
El comando `fetch` requiere Internet y devuelve una nueva ruta.
Pásela a `coverage --snapshot <ruta> --hours 336` para revisar la cobertura.
Para una simulación con ese archivo, use `demo --snapshot <ruta> --start <ISO-con-offset> --hours <duración>`.
`--strict` exige que el snapshot cubra todo el intervalo.
La corrida real archivada usa `--start 2026-11-11T10:00:00-03:00 --hours 36 --strict`
con la carpeta del pronóstico archivado. La prueba E10 se ejecuta con
`python -m pytest P2_E10/tests -q` usando el entorno de E09.

En la demo, compare `boundary_samples` justo antes y al momento del
desmolde (18 h 15 min). Se retiran las dos capas laterales y aumenta el flujo
saliente para la misma temperatura interior de 30 °C. Luego muestre
`exact_boundary_changes`, `activation_hours` y `checks`.

## Física de borde

- **Aire.** La temperatura a 2 m entra en `q_conv = h(T_s − T_aire)`. La ley
  ilustrativa `h = 5 + 4v₁₀` usa el viento en m/s y se configura en el JSON.
  Con el coeficiente de viento en cero, `h` es constante.
- **Moldaje y aislación.** Cada capa aporta `R = espesor/k`, en m²·K/W.
  En la cara exterior se suman la media celda de hormigón y las capas aplicables.
  Al desmoldar, se retiran las capas del cálculo sin reiniciar la temperatura.
  El solver termina un paso en ese instante y recalcula su cota de estabilidad.
- **Suelo.** Las caras inferiores de la primera capa ocupada intercambian
  con un reservorio a temperatura fija. Se suman `Δz/(2k_c)`, la resistencia
  de contacto y `profundidad/k_suelo`. La configuración también admite base
  adiabática. El tratamiento es una resistencia equivalente de suelo.
- **Sol.** Se absorbe `α·GHI` en caras horizontales hacia arriba. Para
  resistencia interior `R`, el flujo neto saliente es
  `[h(T_c − T_aire) − α·GHI] / (1 + hR)`. El balance usa la misma cara
  exterior para convección y absorción solar. `h` representa solo convección.
  El alcance de radiación se limita a onda corta horizontal.

Las interfaces entre vertidas activas conducen internamente. Una cara hacia
una vertida futura queda expuesta hasta su activación. Los parámetros de
convección, capas y suelo son supuestos de demostración.
[Módulo de borde](../P2_E09/src/mcoc_p2/e10/boundaries.py).

## Trazabilidad del pronóstico

Un **forecast** predice condiciones futuras con la información disponible
al emitirse. Una **observación** es una medición. Un **reanálisis** reconstruye
condiciones pasadas combinando observaciones con un modelo meteorológico.
[Forecast API](https://open-meteo.com/en/docs) · [Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api).

Cada descarga queda en su propia carpeta con el JSON original y un
`metadata.json` que registra origen, modelo solicitado, fecha de descarga
UTC, punto solicitado, celda del proveedor, unidades, intervalo válido, URL
y SHA-256. La fecha de descarga identifica cuándo se obtuvo la respuesta.
La emisión queda vacía cuando el endpoint no la informa. Los snapshots
antiguos permiten repetir el cálculo con la información disponible en cada
decisión y comparar el pronóstico a distintos plazos.

La ventana de referencia toma el 27 de noviembre a las 08:00 de Chile como
hora ilustrativa de inicio. En el ejemplo de 14 días, la serie docente cubre
24 h y la cola abarca 312 h. La cola se declara como escenario fijo de
19 °C, 3 m/s y GHI cero. Se registra su inicio y su duración. Si el pronóstico
termina antes del comienzo de obra, las 336 h quedan bajo el escenario hasta
actualizar la descarga. El modo estricto rechaza esa corrida.

La temperatura y el viento se interpolan. Para GHI se usa el promedio
reportado al final de cada intervalo horario. Los pasos respetan esos
límites y el inicio de la cola.
[Loader y snapshots](../P2_E09/src/mcoc_p2/e10/weather.py) · [Definición de radiación](https://open-meteo.com/en/docs#hourly-parameter-definition).
