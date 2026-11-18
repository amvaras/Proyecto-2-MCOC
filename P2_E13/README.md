# MCOC Proyecto 2 — Grupo 2 — E13

**No se encontró un plan factible bajo la familia y el modelo de incertidumbre evaluados.**
Cinco planes, ocho fuentes auténticas y tres historias representativas GFS:
120 simulaciones de 408 h en la malla final. El límite controlante es ΔT≤20 °C.
El resultado es un análisis exploratorio con pesos hipotéticos, sin garantía
de confiabilidad real del 95% ni recomendación de un plan que no cumple.

## Abrir la demostración

Doble clic en **[Iniciar E13.bat](Iniciar%20E13.bat)** y abrir
**http://127.0.0.1:8713/**. No abrir el HTML como archivo suelto.

En **Decisión y riesgo E13** se ven los planes, D físico, máximos y probabilidades
marginales/conjuntas. Cambiar inputs avisa que la comparación requiere recálculo.
Primero validar y estimar coste; luego evaluar 24 escenarios o calcular un
diagnóstico individual con campos 3D nuevos. Ese diagnóstico no estima Pf.
El visor conserva tiempo, vertidas, corte, clipping, sondas y curvas de temperatura.
El caso oficial 3D es ilustrativo y no constituye un plan factible.

[Guía de defensa](docs/E13_DEMO.md) · [Estado técnico y límites](docs/E13_ESTADO.md).

## Instalación y verificaciones

Desde esta carpeta en PowerShell, con Python 3.12:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1
& .\.venv\Scripts\python.exe -m pip check
& .\.venv\Scripts\python.exe -X utf8 -B -m pytest tests/test_e13.py tests/test_e13_web.py -q -p no:cacheprovider
& .\.venv\Scripts\python.exe -X utf8 -B -m pytest -q -p no:cacheprovider
& .\.venv\Scripts\python.exe -X utf8 -B scripts/verify_e13.py --reproduce
~~~

Instalación local desde PyPI oficial y requirements-lock.txt, sin paquetes globales.
Node es opcional para una prueba JS; la aplicación no lo requiere. Las simulaciones
y la verificación funcionan offline con HTTP prohibido dentro del cálculo.

## Reproducir y explorar

~~~powershell
& .\.venv\Scripts\python.exe -X utf8 -B examples/run_e13.py --config configs/e13/study.json --output results/estudio_nuevo
& .\.venv\Scripts\python.exe -X utf8 -B scripts/plot_e13.py
Start-Process .\figures\e13_temperaturas.png
Start-Process .\docs\E13_DEMO.md
~~~

La enumeración principal tomó unos 20 minutos en este equipo; el tiempo depende
de malla/paso/equipo. No exporta campos/figuras por cada escenario. --resume solo
acepta una huella de inputs/código idéntica. Nunca reemplaza un destino existente.
La adquisición meteorológica es una acción separada: no se descarga de nuevo
al ejecutar ni se necesitan claves para reproducir el snapshot congelado.

## Archivos relevantes

- configs/e13/study.json: familia, recursos, incertidumbre, malla y horizonte.
- src/mcoc_p2/e13/: planes, riesgo, escenarios, evaluador, gráficos y soporte web.
- results/e13/: inputs/hashes, los 120 casos y comparación oficial.
- results/e13/representative/: un caso crítico con campos/máscaras de todos los
  pasos y curvas; permite recalcular máximos globales. No es otra solución oficial.
- data/hydration/source_terms.txt: ocho curvas originales corregidas.
- data/ensemble/: respuesta GFS original, metadata y reducción trazable.
- figures/ y vtk/e13/: evidencia calculada y estados 3D seleccionados.
- results/verification/: controles, balances, unión monolítica, regresión,
  reproducción, comprobación del navegador e integridad de E12.

Se reutiliza el integrador E08 y las condiciones E10 con las métricas E12.
Los nombres de módulos anteriores corresponden a capacidades vigentes, no a
entregas completas anidadas. Los inputs climáticos E11/E12 se conservan solo
para sus pruebas de regresión y no se mezclan con el caso E13.

## Límites y publicación

La capacidad de 50 m³/h, esperas, suministro a 12°C y pesos de material son
supuestos declarados. La colocación es térmicamente instantánea, aunque V/r
sí cuenta en D. S25 es subcelda aproximada y la superficie staircase tiene
sesgo de área ~18,21%; controles no equivalen a convergencia completa o cut-cell.
No se acredita factibilidad de obra, calibración, fisuración o seguridad.

La [etiqueta entrega-e13](https://github.com/amvaras/Proyecto-2-MCOC/commit/entrega-e13)
identifica el commit evaluado en la rama `codex/e13`.
La [auditoría de publicación](results/verification/auditoria_publicacion.json)
contrasta el paquete con el enunciado y registra el alcance de la reproducción.
El entorno activo .venv se conserva localmente y se excluye del conjunto a versionar.
