# E06 — Auditoría técnica y formal

Fecha: 28 de octubre de 2026, America/Santiago.
Alcance oficial: dossier de verificación y BIM del caso base; 3 puntos,
viernes 30 de octubre, sin actividad sincrónica.

**Técnicamente COMPLETA. Formalmente pendiente de publicación y commit E06.**
Este juicio describe comprobaciones ejecutadas; no garantiza una nota.

## Base, integridad y cambios

P2_E06 no existía al comenzar. Se inspeccionaron E05, su auditoría, scripts,
configuración, IFC y evidencia final verificacion_03. Los **28 archivos de
entrada** registrados por esa verificación mantienen exactamente sus SHA256.
Se eligió P2_E05 real como base reciente verificada, incluida evidencia
posterior del usuario. Se copiaron físicamente **899 archivos útiles**.
Se excluyeron únicamente entornos, cachés, metadatos de instalación y
temporales recreables. Las 24 ruedas bloqueadas se conservaron.

[E06_BASE_E05_INVENTARIO.json](E06_BASE_E05_INVENTARIO.json) identifica cada
archivo útil antes de los cambios. El inventario completo de E05 previo a la
copia, con tamaños, SHA256 y fechas, está en
[E05_INTEGRIDAD_PREVIA.json](../evidencias/e06/E05_INTEGRIDAD_PREVIA.json).
Se conserva README_HEREDADO_E05.md. De los archivos heredados solo cambió
README.md; ningún archivo heredado se eliminó. pyproject.toml y el lock se
mantienen intactos. La versión 0.5.0 identifica el mismo paquete técnico.

Los **25 archivos Python heredados** de src/tests/scripts/examples mantienen
su contenido exacto. Se añadieron cuatro scripts E06 para reproducir,
consolidar, comprobar el dossier y probar independencia. No se reescribió el
solver ni se implementaron E07–E15.

La comparación final confirmó sin altas, bajas ni cambios los 7579 archivos
de E01, 7660 de E02, 7722 de E04 y 8342 de E05. P2_E03 está ausente.
La prueba incluye contenido y mtime, además de nombres y tamaños:
[proteccion_entregas.json](../evidencias/e06/proteccion_entregas.json).
No se crearon commits, ramas, PR ni publicaciones.

## Matriz de la rúbrica

| Criterio oficial | Evidencia presentada | Resultado comprobado | Defecto / acción correctiva | Estado final |
|---|---|---|---|---|
| A. Cobertura y calidad — 1,1 | Dossier, matriz de diez filas, 198 tests, JSON/NPZ, variantes y referencias.json | Exactas 1D/2D/3D, fuente, energía, Neumann, Robin y estabilidad PASS | No se detectó defecto del solver; se comprobaron referencias por sustitución y operador real | CUMPLE Y VERIFICADO |
| B. Convergencia y conservación — 0,7 | Tres resoluciones, tres pasos, figuras logarítmicas, capacidad heterogénea | Orden espacial ≈2; temporal ≈1; balance ponderado satisfecho | Error temporal aislado con modo semidiscreto; contaminación espacial cuantificada | CUMPLE Y VERIFICADO |
| C. BIM y consistencia geométrica — 0,6 | IFC incluido, validador, reconstrucción, cotas, volúmenes, figura y simplificaciones | IFC4, cinco elementos, cotas docentes y volumen coherentes; sin solapamientos | Primera figura ocultaba parte del pedestal por orden de dibujo; se corrigió la colección de triángulos y se revisó la imagen nueva | CUMPLE Y VERIFICADO |
| D. Síntesis, trazabilidad y reproducción — 0,6 | Dossier de 1100 palabras de prosa, README, comandos, hashes, copia externa offline | Reproducción técnica PASS; enlaces y límite comprobados | Se corrigieron escapes LaTeX; falta identificador remoto E06, expresamente pendiente sin publicación autorizada | CUMPLE CON OBSERVACIONES |

La ausencia de commit afecta el cierre formal. No invalida la evidencia
numérica local ni se oculta usando un SHA de otra entrega.

## Ejecuciones y criterio de aceptación

Evidencia vigente: [ejecucion_02/e06.json](../evidencias/e06/ejecucion_02/e06.json).
La primera ejecución aprobó 198 pruebas en 27,554 s JUnit; la segunda,
con controles textuales y visuales corregidos, **198 en 26,256 s**.
La copia externa aprobó **198 en 25,912 s**. En todas: 0 fallos, errores u
omisiones. La suite se desglosa en 62 de diffusion_1d, 13 E02, 57 thermal_nd,
5 IFC y 61 E05: 137 heredadas anteriores a E05 y 61 de la batería E05.
No se añadieron pruebas duplicadas para aumentar el conteo.

En ambas ejecuciones finales pasaron diez casos nominales, sesenta variantes
y Robin h=25. El verificador comprueba los códigos esperados de rechazos por
dt excesivo, unidades mm y precisión insuficiente: no considera exitoso un
error arbitrario. La evidencia guarda comandos, parámetros, tolerancias,
fechas UTC, versiones, códigos de salida, duración y huellas de entradas.

La instalación E06 se reconstruyó desde ruedas incluidas, sin red.
Entorno: Windows AMD64, CPython 3.12.10, NumPy 2.5.4, pytest 9.1.1,
Matplotlib 3.11.2, IfcOpenShell 0.9.0.post1, mcoc-p2 0.5.0. pip check pasó.
No se presume portabilidad ensayada en otros sistemas.

## Referencias y resultados físicos

Las referencias sinusoidales satisfacen la PDE homogénea con caras Dirichlet
constantes y coordenadas de centros. Se derivaron independientemente los
autovalores continuo y semidiscreto y se aplicó el operador real al seno en
cajas no cúbicas 1D/2D/3D. Residuos máximos de operador: 2,626e-20,
9,487e-20 y 2,057e-19 K/s, menores que sus tolerancias proporcionales a la
tasa. No se ajustó la referencia a los resultados observados.

Caso nominal: k=2, rho=2400, cp=900, longitudes 1 m, tiempo 10000 s,
amplitud 10 °C e inicial 20 °C. Errores L∞ de exactas: 0,000670749101 °C,
0,001213820492 °C y 0,002314445944 °C, frente a 0,03 °C.

Espacio: 6×6, 12×12 y 24×24; Δt=3,125 s fijo. Errores L∞
0,032183989738, 0,008489824920 y 0,002120398681 °C. Órdenes
1,92253648 y 2,00139925, tolerancia 2±0,30. Contaminación temporal máxima
2,03641%, menor que 10%. El error grueso puede superar 0,03 °C porque el
criterio del estudio es orden y contaminación; no se lo oculta como exacta PASS.

Tiempo: malla 6×6 fija, pasos efectivos 500, 250 y 125 s. Errores L∞
0,006260256, 0,003121399 y 0,001558527 °C contra referencia semidiscreta.
Órdenes 1,00402905 y 1,00200912, tolerancia 1±0,15. Euler es de primer
orden temporal; este estudio no confunde error continuo espacial con temporal.

Energía: caja heterogénea, inicial no uniforme, sin fuente y caras aisladas.
Se usa suma de rho*cp*V*(T−20), no media simple. Residuo máximo
4,4792614e-10 J, tolerancia 3,0850171e-4 J. Cambio final 3,2412117e-10 J;
rango térmico de 19,49107 a 14,82510 °C.

Fuente: 1000 W/m³, V=1 m³, 10000 s y propiedades nominales. Incremento
4,62962962963 °C; energía esperada 10000000 J y calculada 10000000,00000005 J.
Error térmico máximo 2,4869e-14 °C. Se comprueban todos los tiempos guardados.

Neumann: −100 W/m² por z− incorpora 1000000 J, con residuo máximo
3,609e-9 J. El convenio positivo es saliente; el área se calcula físicamente.

Robin: h=12 W/(m² K), inicial 50 °C, ambiente 20 °C, seis caras.
Se incluye resistencia de media celda y película. Pérdida de energía
13455099,41544 J y residuo máximo 5,58794e-9 J ≤5,401e-4 J.
Con h=25, pérdida de 19680291,79598 J y residuo 3,72529e-9 J.
Los controles revisan signo, ley superficial, resistencias, máximo y balance;
no llaman exacta analítica a la evolución Robin general calculada.

La estabilidad utiliza capacidad/conductancias local. Cerca del límite la
solución respeta monotonía y el exceso se rechaza. No se usa Fo≤1/6 como
regla universal para caras Dirichlet/Robin o capacidades heterogéneas.
Las magnitudes nominales coinciden con E05 porque se conservaron datos y
algoritmo; se recalcularon, no se copiaron como evidencia E06.

## BIM comprobado y figura

[bim.json](../evidencias/e06/ejecucion_02/bim.json) deriva del IFC real y del
validador. Confirma IFC4 en metros, jerarquía espacial, GUID únicos,
UANDES_HormigonMasivo, cinco IfcFooting, mallas cerradas orientadas, cotas,
ausencia de intersección volumétrica en los diez pares y 0 incidencias EXPRESS.
La reconstrucción en otro destino conserva geometría, propiedades y GUID;
no exige identidad binaria del encabezado de exportación.

La planta octagonal mide 18 m entre caras; borde 1,10 m, centro 3,30 m,
pedestal circular Ø7 m y 1,00 m adicional; altura global 4,30 m.
Intervalos: 0–0,55; 0,55–1,10; 1,10–2,20; 2,20–3,30; 3,30–4,30 m.
Volumen analítico total 636,885036448 m³; malla 636,877717582 m³.
La diferencia relativa 1,1492e-5 se explica por teselación circular.
Tolerancia de volumen por pieza 5e-4 relativa; vértices octagonales 1e-7 m;
extensión del círculo teselado 2 mm. Su radio de perfil se comprueba aparte.

La figura final usa vértices/triángulos leídos por IfcOpenShell, sin sustitución
por imágenes externas. Muestra tres vistas, colores por vertida y dimensiones,
con escala geométrica sin exageración vertical. No se atribuye una nueva sesión
de Blender/Bonsai. Se inspeccionaron visualmente las tres figuras E06.

El dossier enumera octágono idealizado, borde y pedestal docentes, transición
en troncos, cinco vertidas iniciales, armaduras/anclajes/detalles omitidos y
origen local. E06_FUENTES.json conserva el extracto y SHA256 de la guía
docente; la referencia al paper es mediada por esa guía, sin inventar cotas.
Coordenadas climáticas G2: −28.856102, −71.421831; no implican georreferencia
IFC ni uso de datos climáticos en estas simulaciones.

## Documento, independencia y pendientes

El dossier tiene **1100 palabras de prosa** y 1335 visibles en total.
check_e06_dossier.py incluye títulos, listas y pies en prosa; excluye tablas,
imágenes, ecuaciones desplegadas y código solo de ese conteo. Cuenta etiquetas
de enlaces, no sus URL. Verifica cabecera exacta, contenidos obligatorios,
caracteres de control, fórmula LaTeX y todos sus enlaces locales.
Las tablas contienen métricas y cotas, sin párrafos escondidos.

La primera figura 3D presentó oclusión entre colecciones de vertidas y la
primera fórmula contenía escapes Python incompatibles con LaTeX. Se corrigieron
la colección de triángulos y la plantilla raw. Los primeros artefactos se
conservaron como borradores dentro de ejecucion_01; el dossier vigente usa
exclusivamente ejecucion_02 y figures/. No se alteró la física para obtener PASS.

La [prueba externa](../evidencias/e06_independencia/independence.json) creó una
copia física fuera de Proyecto 2, instaló otro entorno usando solo sus ruedas
y comprobó el import dentro de P2_E06_autonomo. Repitió toda E06, incluidas
referencias, reconstrucción, figuras y documento. Se compararon las entradas
de código y datos con la ejecución local. Las rutas absolutas en logs son
procedencia histórica; los scripts calculan su raíz desde su propio archivo.

La comparación final encontró idénticas las 32 huellas de entrada, los diez
reportes nominales, 36 arrays NPZ y los bytes de las tres figuras:
[comparacion_reproduccion.json](../evidencias/e06/comparacion_reproduccion.json).
Los enlaces del dossier reproducido también se comprobaron después de traer
la evidencia de vuelta, conservando su profundidad relativa.

[E06_REPOSITORIO.json](E06_REPOSITORIO.json) registra la consulta remota.
main estaba en 53a9575d19e98143e84286d73f7b81c756aa9929, una entrega E01.
Ese SHA no contiene este dossier. Se exige publicar E06 con autorización,
registrar el SHA correspondiente y revisar el marcador formal antes de entregar.
El inventario local SHA256 no sustituye un identificador Git.

**No quedan errores técnicos bloqueantes identificados. El cierre formal
permanece pendiente del commit E06.** Las cajas de prueba no son la fundación
voxelizada ni una predicción de Freirina. No se amplió el alcance a E07–E15.
