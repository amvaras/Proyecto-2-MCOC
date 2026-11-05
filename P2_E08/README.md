# MCOC · Proyecto 2 · Grupo 2 · E08

> **Publicación E08 · rama codex/e08.** Los estados «pendiente de publicación»
> de las evidencias registran el momento de sus ejecuciones. Consultar la
> [constancia de publicación](docs/PUBLICACION_E08.md).

**IFC → grilla → simulación térmica por etapas**, con visualización 3D
interactiva conectada a Python. El calendario y las temperaturas de colocación
se leen de inputs; no están codificados dentro del integrador.

## Abrir la interfaz

Doble clic en **iniciar.bat**. Desde la raíz del repositorio también se puede
usar **INICIAR_E08.bat**. Abre Google Chrome, inicia Python en segundo plano
si hace falta y reutiliza el servidor existente. Dirección:
[http://127.0.0.1:8768/](http://127.0.0.1:8768/).

La referencia está precalculada. Para un nuevo escenario: editar la malla,
los inicios y temperaturas; ejecutar; mover el tiempo o reproducir. Se puede
girar la vista, acercar y mostrar/ocultar vertidas. La visibilidad es solo del
dibujo: no modifica temperaturas ni balance. El JSON avanzado conserva bordes
por orientación y propiedades particulares. Cada ejecución guarda su IFC,
inputs, temperaturas y figuras, y puede descargarse completa.

- [Guía de demo y respuestas](docs/E08_DEMO.md).
- [Formulación y verificación](docs/E08_VERIFICACION.md).
- [Evidencias de ejecución](evidencias/e08/README.md).
- [IFC real](geometry/foundation.ifc) y [inputs nominales](configs/e08/demo.json).

## Instalación desde cero, sin red

Esta carpeta funciona sin depender de entregas anteriores. Incluye 24 ruedas
para Windows x64/Python 3.12. Desde P2_E08, PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-index --find-links vendor/wheels -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-index --no-build-isolation --no-deps -e .
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -X utf8 -B web/servidor.py --open
```

En este computador también existe el entorno propio `.venv-e08` en la raíz
del repositorio; el lanzador lo detecta. Los scripts no dependen de esa ruta
para funcionar en otro computador. No se utiliza el entorno de E07.

## Consola y batería

Con el entorno activado y desde P2_E08:

```powershell
python examples/run_e08.py --output results/e08_nominal
python examples/run_e08.py --spacing 0.55 0.55 0.275 --interval-hours 3 --placement-offset 5 --output results/e08_modificado
python scripts/verify_e08.py --output results/e08_verificacion
```

Desde la raíz del repositorio: `./VERIFICAR_E08.ps1`. Elegir destinos nuevos:
se rechaza sobrescribir resultados. También se pueden usar --config, --ifc,
--max-step, --t-end-hours y --no-plots. La interfaz guarda sus escenarios en
results/interfaz_e08.

## Qué se calcula

Euler explícito sobre las celdas activas, contacto conductivo por resistencias
de media celda, fronteras de Dirichlet/Neumann/Robin y fuente de hidratación
integrada por intervalo. El paso se ajusta por estabilidad y llega exactamente
a los eventos. La colocación añade capacidad y energía sin reinicializar las
piezas anteriores. El balance comprueba hidratación, pérdidas y material entrante.

La referencia de 72 h usa activaciones 0/6/12/18/24 h y 73 fotogramas.
La suite completa aprobó **327 tests**, 60 variaciones térmicas y dos demos E08.
Los resultados son ilustrativos: no hay calibración Freirina, clima real,
Arrhenius ni resistencia imperfecta de juntas. Se conserva el área staircase.

Archivos de cada caso: inputs.json, model.ifc, voxels.npz, solution.npz,
geometry.json, summary.json y cuatro figuras. solution.npz conserva la historia
numérica en doble precisión; el visor recibe fotogramas para dibujar. Las
celdas futuras tienen NaN hasta su colocación.

## Procedencia y publicación

Copia física de P2_E07 auditada; los módulos Python heredados se preservaron.
El inventario de la base está en docs/E08_BASE_E07_INVENTARIO.json. Los documentos
E01–E07 copiados son antecedentes de sus etapas, no la descripción de E08.
Los resultados recreables no versionados y los entornos anteriores no se copiaron.

Repositorio: https://github.com/amvaras/Proyecto-2-MCOC.
Rama de entrega: [codex/e08](https://github.com/amvaras/Proyecto-2-MCOC/tree/codex/e08).
El SHA evaluado se declara en Canvas y debe corresponder al commit de E08;
el SHA de E07 no identifica esta entrega.
