# Estado real E01 — 20 de octubre de 2026

Esta revisión corresponde al árbol local de `e01/base-termica-ifc`, aún sin un
commit nuevo autorizado. No certifica la nota, la comprensión individual ni la
aceptación del profesor. La rúbrica evalúa individualmente varios componentes.

## COMPLETADO Y VERIFICADO

- Clon real del repositorio oficial; inspección de rama remota y commit inicial.
  Se preservaron los documentos y archivos originales de la carpeta superior.
- README en español con caso G2, coordenadas exactas, alcance, arquitectura,
  instalación PowerShell, comandos de ejecución y límites del modelo.
- CPython 3.12.10 con entorno virtual, dependencias declaradas y versiones
  comprobadas en `requirements-lock.txt`. Instalación repetida en `.venv-repro`
  desde ese archivo; `pip check` sin conflictos y 54 tests aprobados allí.
- Solver 1D propio por balance de energía, material constante, condición inicial
  configurable y fuente prescrita uniforme o espacial constante en el tiempo.
- Dirichlet, Neumann y Robin con signos, medias celdas y unidades documentados.
  Cota explícita de difusión y restricción adicional por Robin.
- 54 pruebas pytest aprobadas: balances, signos, estabilidad, datos inválidos,
  soluciones exactas, refinamiento e IFC entregado/reconstruido.
- Ejemplo ejecutado: 24 h, dt=67,5 s, Fo=0,4, error máximo frente a solución
  exacta de 0,000645135652 °C. Figura, JSON y NPZ existentes y revisados.
- IFC4 existente y legible, cinco IfcFooting, GUID estables, jerarquía y material,
  unidades en metros, planta de 18 m y cotas hasta 4,30 m. Validación EXPRESS
  sin incidencias; cotas, mallas cerradas y volúmenes analíticos comprobados.
- Vista 3D, planta y lateral generadas desde la geometría IFC con IfcOpenShell
  y Matplotlib e inspeccionadas como figura; no son capturas de Bonsai.
- Guía de preparación oral con 24 temas, respuestas, ejemplos y referencias al
  código; preguntas difíciles, funciones y demostración de dos minutos.
- Evidencias de ejecución con salidas reales, versiones y huellas SHA256 de
  código, dependencias y modelo; comandos de regeneración disponibles.
- Permisos de GitHub consultados para cuenta conectada y credencial Git local:
  ambas tienen lectura y `push=false` sobre el repositorio oficial.

## IMPLEMENTADO PERO NO VERIFICADO

- Instrucciones de apertura y revisión humana en Bonsai preparadas, pero su
  recorrido en interfaz no fue realizado en esta sesión.
- Portabilidad fuera de Windows x64 / Python 3.12 no ensayada. No es una promesa
  de soporte para otras versiones de Python o motores de geometría.

## INCOMPLETO

- Uso efectivo y comprobación visual en Blender/Bonsai: registrar versiones,
  abrir IFC, revisar objetos y guardar capturas. El archivo generado desde
  Python no se presenta como evidencia de autoría desde Bonsai.
- Lectura personal de G00/G01/G02/G05 por cada integrante y práctica oral.
- Commit nuevo E01: pendiente de autorización explícita del usuario antes de
  crearlo, según su instrucción. El trabajo permanece revisable en archivos.
- URL de commit evaluable para Canvas: todavía no existe para esta implementación.
- Fuentes oficiales adicionales ausentes: ver `FUENTES.md`. El enunciado E01
  sí fue proporcionado en la solicitud y se utilizó como referencia principal.

## BLOQUEADO

- Publicación directa al repositorio oficial con las credenciales verificadas:
  `push=false`. La propietaria debe dar escritura a la cuenta que publique, o
  revisar una propuesta enviada desde un fork. No se creó un fork ni un PR ni
  se publicaron datos; se requiere la autorización explícita solicitada antes
  de cualquier commit/publicación.

## Lista de aceptación

- [x] README suficiente.
- [x] Entorno Python reproducible probado en dos entornos locales.
- [x] Tests realmente ejecutados.
- [x] Solver 1D funcional con verificaciones físicas y analíticas.
- [x] Ecuación, balance y esquema numérico documentados.
- [x] Estabilidad explícita controlada para fronteras soportadas.
- [x] Condiciones iniciales y de borde documentadas y comprobadas.
- [x] IFC preliminar existente, legible y verificado desde Python.
- [x] Relación Blender/Bonsai/IFC/Python explicada.
- [x] Evidencias de ejecución registradas.
- [x] Código organizado y material para preparación individual disponible.
- [x] Estado Git inspeccionado, sin alteración del historial compartido.
- [ ] Revisión visual e interacción real en Bonsai documentadas.
- [ ] Lectura y comprensión individual confirmadas por cada integrante.
- [ ] Commit nuevo E01 autorizado y creado.
- [ ] Commit publicado verificado y declarado en Canvas.

Por estos pendientes no se declara E01 completamente lista ni certificada.
Los límites de 70 °C, 20 °C y el horizonte de 14 días se mantienen como requisitos
del proyecto general: no se evaluaron para la fundación en esta E01.
