# MCOC — PROYECTO 2 — GRUPO 2
## E06 — DOSSIER DE VERIFICACIÓN + BIM DEL CASO BASE
### IMPLEMENTACIÓN, REPRODUCCIÓN, AUDITORÍA Y PREPARACIÓN FINAL
### Viernes 30 de octubre de 2026

Actúa como un equipo especializado en ingeniería civil, transferencia de calor, métodos computacionales, verificación numérica, Python, BIM/IFC, documentación científica y reproducibilidad.

Tu misión es preparar íntegramente la entrega E06 del Proyecto 2 de Métodos Computacionales en Obras Civiles, utilizando la base técnica ya desarrollada y verificada en E05.

Debes inspeccionar los archivos reales, ejecutar las comprobaciones necesarias, producir el dossier Markdown, generar o seleccionar figuras científicas correctas y auditar el cumplimiento de todos los requisitos del enunciado.

No debes limitarte a escribir recomendaciones.

Debes entregar archivos reales y verificar que funcionen.

PRINCIPIOS FUNDAMENTALES:

1. Corrección científica.
2. Trazabilidad.
3. Reproducibilidad.
4. Claridad del documento.
5. Cumplimiento estricto del enunciado.
6. Conservación de las entregas anteriores.
7. Independencia completa de la carpeta E06.
8. No inventar datos ni resultados.
9. No crear commits ni publicar cambios sin autorización expresa.

# 1. DIRECTORIO DEL PROYECTO

Directorio raíz:

C:\Users\javie\OneDrive\Escritorio\Universidad\9no semestre\MCOC\Proyecto 2

Entrega anterior:

P2_E05

Nueva entrega obligatoria:

P2_E06

Ruta final:

C:\Users\javie\OneDrive\Escritorio\Universidad\9no semestre\MCOC\Proyecto 2\P2_E06

Antes de comenzar:

- Inspecciona P2_E05.
- Comprueba su estructura y archivos.
- Identifica la versión técnica más reciente y verificada.
- Revisa las auditorías anteriores.
- Comprueba los resultados de E05.
- Registra un inventario de integridad de la entrega anterior.

Crear P2_E06 mediante una copia física independiente de P2_E05.

No utilizar enlaces simbólicos, junctions ni dependencias hacia carpetas anteriores.

Cada entrega debe contener absolutamente todo lo necesario para reproducir su trabajo.

Se permite duplicar información entre entregas.

No modificar:

P2_E01
P2_E02
P2_E03, si existe
P2_E04
P2_E05

No borrar archivos históricos ni alterar resultados de entregas anteriores.

Si P2_E06 ya existe, inspeccionar su contenido antes de cualquier escritura y no sobrescribir trabajo existente sin autorización.

# 2. ESTRUCTURA AUTÓNOMA DE E06

P2_E06 debe conservar:

- README.md.
- pyproject.toml.
- requirements-lock.txt.
- src/.
- tests/.
- examples/.
- scripts/.
- geometry/.
- configs/.
- docs/.
- Resultados científicos.
- Figuras.
- Evidencias de verificación.
- Modelo IFC.
- Archivos necesarios para reconstruir el entorno.

Conservar las dependencias locales empaquetadas en E05 cuando sean necesarias para la reproducción sin red.

Excluir únicamente entornos virtuales, cachés y archivos temporales recreables.

No eliminar archivos técnicos relevantes.

Toda la implementación debe utilizar rutas relativas a P2_E06.

# 3. ENUNCIADO OFICIAL E06

E06 — Semana 2 / viernes — Dossier de verificación + BIM del caso.

Fecha: viernes 30 de octubre de 2026.

Puntaje: 3 puntos.

OBJETIVO:

Congelar la evidencia de que el solver básico está verificado y completar el modelo BIM base de la fundación.

ANTES DE LA ACTIVIDAD:

Tener la batería de tests ejecutada y el modelo BIM del caso base en una versión coherente.

DURANTE LA ACTIVIDAD:

No hay actividad sincrónica.

ENTREGA:

Un documento Markdown con máximo 1.200 palabras, más figuras y tablas.

Debe contener:

1. Repositorio y commit.
2. Matriz de verificación.
3. Convergencia espacial.
4. Convergencia temporal.
5. Test de energía.
6. Test de fuente.
7. Test de condición Robin.
8. Imagen y dimensiones del BIM base.
9. Lista explícita de simplificaciones geométricas.

Tabla mínima:

| Test | Qué verifica | Error/métrica | Resultado |

El IFC utilizado debe estar versionado o ser descargable mediante instrucciones reproducibles.

RÚBRICA:

- Cobertura y calidad de verificación: 1,1 puntos.
- Convergencia y conservación: 0,7 puntos.
- BIM base y consistencia geométrica: 0,6 puntos.
- Síntesis, trazabilidad y reproducibilidad: 0,6 puntos.

Total: 3,0 puntos.

# 4. ESTADO PREVIO E05

E05 fue desarrollada y auditada técnicamente.

Resultados reportados y posteriormente comprobados en el computador del usuario:

- 198 tests aprobados.
- 137 pruebas heredadas.
- 61 pruebas nuevas E05.
- Batería de 10 casos: todos PASS.
- Soluciones exactas 1D, 2D y 3D.
- Conservación adiabática.
- Fuente volumétrica uniforme.
- Neumann.
- Robin.
- Convergencia espacial.
- Convergencia temporal.
- Estabilidad explícita.

Se comprobaron además modificaciones reales de parámetros:

- Caja 3D no cúbica con 8×10×12 celdas y longitudes 1,2×0,9×1,6 m.
- Robin 3D con h=25 W/(m²·K), temperatura inicial 50 °C y ambiente 20 °C.

Ambos casos terminaron en PASS.

Estos resultados son antecedentes.

No asumir que siguen siendo válidos sin repetir las verificaciones necesarias desde P2_E06.

# 5. OBJETIVO ESPECÍFICO DEL DESARROLLO

Esta entrega no requiere un nuevo solver.

Debes:

1. Consolidar la evidencia de las verificaciones existentes.
2. Repetir las pruebas principales.
3. Validar las referencias analíticas.
4. Generar figuras de convergencia claras.
5. Documentar conservación de energía.
6. Documentar generación volumétrica.
7. Documentar Robin.
8. Verificar el modelo BIM completo.
9. Preparar un dossier científico de máximo 1.200 palabras.
10. Demostrar reproducibilidad.

No reescribir el solver E05 ni introducir funcionalidades correspondientes a E07–E15.

Solo corregir errores técnicos demostrados que impidan cumplir E06.

# 6. DOSSIER PRINCIPAL

Crear:

P2_E06/docs/E06_DOSSIER.md

Este archivo será el documento principal de entrega.

Debe ser completamente legible por sí mismo.

No debe exigir que el evaluador lea documentación adicional para comprender las conclusiones principales.

Estructura recomendada:

1. Identificación y alcance.
2. Repositorio y commit.
3. Matriz de verificación.
4. Convergencia espacial.
5. Convergencia temporal.
6. Conservación de energía.
7. Fuente volumétrica.
8. Robin.
9. BIM base.
10. Simplificaciones geométricas.
11. Reproducibilidad y conclusiones.

El documento principal debe tener MÁXIMO 1.200 PALABRAS de contenido en prosa.

Las figuras y tablas están permitidas adicionalmente según el enunciado.

No utilizar esta excepción para ocultar párrafos extensos dentro de tablas o imágenes.

Apuntar preferentemente a unas 900–1.100 palabras para mantener margen.

Preparar un verificador automático que cuente palabras y reporte el resultado.

No declarar que cumple el límite sin contar realmente las palabras.

# 7. REPOSITORIO Y COMMIT

El enunciado exige identificar:

Repositorio:
Commit evaluado:

Repositorio oficial conocido:

https://github.com/amvaras/Proyecto-2-MCOC

Debes comprobar el estado real del proyecto.

RESTRICCIÓN:

No crear commits, no hacer push, no abrir PR y no modificar GitHub sin autorización expresa.

Si existe un SHA remoto verificable que realmente contenga E06, incluirlo.

Si no existe, dejar en el dossier un marcador visible:

COMMIT E06 PENDIENTE DE PUBLICACIÓN

No reutilizar un SHA antiguo de E01/E02/E05 como si identificara E06.

Registrar este pendiente en la auditoría.

No declarar la entrega formal completamente cerrada mientras falte el identificador exigido.

No permitir que la ausencia de commit bloquee la elaboración y verificación técnica del resto del dossier.

# 8. MATRIZ DE VERIFICACIÓN

Incluir obligatoriamente una tabla con las columnas exactas:

| Test | Qué verifica | Error/métrica | Resultado |

Como mínimo, considerar:

- Solución exacta 1D.
- Solución exacta 2D.
- Solución exacta 3D.
- Convergencia espacial.
- Convergencia temporal.
- Conservación adiabática.
- Fuente uniforme.
- Neumann.
- Robin.
- Estabilidad.

Usar exclusivamente resultados reales de ejecución.

Para cada caso:

- Identificar la referencia.
- Informar la métrica correspondiente.
- Informar tolerancia.
- Señalar PASS o FAIL.
- Facilitar trazabilidad hacia la evidencia generada.

No considerar que una prueba es válida simplemente porque no produjo una excepción.

# 9. CONVERGENCIA ESPACIAL

Reproducir un estudio de refinamiento espacial.

Debe:

- Comparar al menos tres resoluciones.
- Utilizar referencia analítica válida.
- Controlar el error temporal.
- Calcular error y orden observado.
- Identificar si el orden se aproxima al esperado.
- Mostrar cómo cambia el error al refinar la malla.

Preparar una figura profesional:

figures/e06_convergencia_espacial.png

Mostrar en ejes adecuados:

- Resolución espacial.
- Error numérico.
- Orden esperado y observado, si es útil.

Evitar gráficos que exageren artificialmente la calidad del resultado.

# 10. CONVERGENCIA TEMPORAL

Reproducir un estudio manteniendo fija la malla espacial.

Reducir el paso temporal progresivamente.

Comparar contra una referencia semidiscreta exacta o referencia justificada que permita aislar el error temporal.

Calcular:

- Paso temporal efectivo.
- Error.
- Cocientes.
- Orden observado.

Generar:

figures/e06_convergencia_temporal.png

Explicar que el esquema explícito Euler presenta primer orden temporal en condiciones apropiadas.

No confundir convergencia temporal con refinamiento espacial simultáneo.

# 11. TEST DE CONSERVACIÓN DE ENERGÍA

Repetir al menos un caso:

- Dominio adiabático.
- Fuente cero.
- Perfil inicial no uniforme.

Demostrar:

E_final - E_inicial ≈ 0.

La energía debe calcularse desde las capacidades térmicas y temperaturas del modelo.

No usar simplemente una media no ponderada de temperaturas para demostrar conservación si las capacidades son diferentes.

Incluir:

- Magnitud del residuo energético.
- Tolerancia.
- Resultado PASS/FAIL.
- Interpretación física.

Preferentemente documentar también un caso con materiales heterogéneos.

# 12. TEST DE FUENTE VOLUMÉTRICA

Repetir un caso:

- Temperatura inicial uniforme.
- Dominio adiabático.
- Fuente volumétrica constante.

Verificar:

T(t) = T_inicial + q_dot*t/(rho*cp).

Y:

ΔE = q_dot*V*t.

Registrar:

- q_dot en W/m³.
- Tiempo.
- Propiedades térmicas.
- Incremento de temperatura esperado.
- Incremento calculado.
- Error.
- Resultado.

No confundir fuente volumétrica con flujo superficial.

# 13. TEST ROBIN

Ejecutar un caso con intercambio convectivo.

Verificar:

- Signo del flujo.
- Temperatura ambiente.
- Coeficiente h.
- Resistencia térmica de media celda.
- Balance energético.
- Respuesta de enfriamiento o calentamiento.
- Cumplimiento de tolerancias.

Modelo:

R'' = Δn/(2k) + 1/h.

q'' = (T_celda - T_ambiente)/R''.

Explicar brevemente que Robin representa convección hacia el ambiente y que la temperatura superficial no es necesariamente igual a la temperatura ambiente.

Generar una figura adicional si mejora el dossier y no introduce información redundante.

# 14. MODELO BIM DEL CASO BASE

Modelo:

geometry/foundation.ifc

Grupo:

G2 — Freirina / Parque Eólico Sarco.

Coordenadas climáticas oficiales:

Latitud -28.856102.
Longitud -71.421831.

Verificar que el IFC corresponda a la geometría docente:

- Planta exterior octagonal.
- 18 m entre caras.
- Espesor en borde 1,10 m.
- Espesor central 3,30 m.
- Pedestal de diámetro 7 m.
- Altura adicional del pedestal 1,00 m.
- Altura global 4,30 m.
- Cinco vertidas identificables.

Rangos:

Vertida_01: 0,00–0,55 m.
Vertida_02: 0,55–1,10 m.
Vertida_03: 1,10–2,20 m.
Vertida_04: 2,20–3,30 m.
Vertida_05: 3,30–4,30 m.

Volumen total aproximado:

636,89 m³.

Comprobar todas estas cifras desde el IFC real.

No copiar resultados anteriores si la geometría ya cambió.

# 15. FIGURA BIM

Incluir una imagen clara y representativa del modelo.

Archivo recomendado:

figures/e06_bim_fundacion.png

Preferentemente mostrar:

- Vista isométrica.
- Identificación de vertidas.
- Geometría octagonal.
- Pedestal.
- Cotas globales.

Puedes reutilizar una captura real de Bonsai o generar una visualización geométrica mediante IfcOpenShell, diferenciando su procedencia.

No presentar una imagen generada desde Python como captura de Bonsai.

Incluir un pie de figura adecuado.

No utilizar imágenes de referencia externas en sustitución del modelo real.

# 16. SIMPLIFICACIONES GEOMÉTRICAS

Incluir una lista explícita y técnicamente correcta.

Como mínimo, revisar:

- Geometría octagonal idealizada respecto de la fundación original del paper.
- Espesor de borde adoptado para ejercicio docente.
- Transición inclinada representada mediante troncos octagonales.
- División en cinco vertidas iniciales.
- Pedestal de altura docente adoptada.
- Omisión de armaduras.
- Omisión de pernos y elementos de anclaje.
- Omisión de detalles menores no definidos por la publicación.
- Ausencia de georreferenciación global en el IFC.

No presentar las dimensiones adoptadas como si todas hubieran sido medidas directamente en el paper.

Distinguir geometría docente de geometría experimental original.

No inventar simplificaciones que no correspondan al modelo existente.

# 17. CONSISTENCIA ENTRE BIM Y SOLVER

Comprobar y documentar que:

- El IFC representa la geometría constructiva.
- El solver E05 resuelve casos ideales de verificación.
- La integración real mediante voxelización todavía no está implementada.
- Los resultados de las cajas de prueba no representan la predicción térmica de la fundación de Freirina.

Esta distinción es obligatoria para evitar conclusiones engañosas.

# 18. REPRODUCIBILIDAD DEL IFC

El IFC utilizado debe encontrarse dentro de P2_E06:

geometry/foundation.ifc

La documentación debe permitir:

- Localizarlo.
- Abrirlo en Blender/Bonsai.
- Inspeccionar sus cinco elementos.
- Leerlo desde Python.
- Verificar esquema, unidades, geometría y propiedades.

Proporcionar el comando exacto del verificador IFC.

Si existe un generador reproducible, documentar cómo reconstruirlo sin reemplazar el archivo de referencia accidentalmente.

No confiar únicamente en capturas de pantalla.

# 19. TRAZABILIDAD DE RESULTADOS

Organizar la evidencia de E06 en una carpeta propia, por ejemplo:

evidencias/e06/

Registrar:

- Fecha/hora de ejecución.
- Versión Python.
- Bibliotecas.
- Comandos.
- Parámetros.
- Resultados.
- Tolerancias.
- Estado PASS/FAIL.
- Rutas de datos y figuras.

Mantener resultados históricos anteriores separados.

No sobrescribir evidencias originales de E05.

Si se recalculan valores y difieren de E05, explicar la diferencia.

# 20. VERIFICACIÓN COMPLETA

Antes de finalizar:

1. Reconstruir o comprobar el entorno.
2. Ejecutar la suite completa de tests.
3. Ejecutar la batería E05.
4. Ejecutar convergencia espacial.
5. Ejecutar convergencia temporal.
6. Ejecutar conservación adiabática.
7. Ejecutar fuente uniforme.
8. Ejecutar Robin.
9. Verificar IFC.
10. Comprobar dimensiones y volúmenes.
11. Generar figuras.
12. Comprobar referencias a figuras dentro del Markdown.
13. Comprobar que las rutas relativas funcionen.
14. Contar palabras del dossier.
15. Comprobar que el documento esté dentro del límite.
16. Comprobar que no haya datos contradictorios.
17. Verificar que P2_E06 sea autónoma.
18. Confirmar que entregas anteriores permanecen intactas.

# 21. DOCUMENTACIÓN ADICIONAL

Además del dossier principal, crear solamente documentación útil:

docs/E06_ESTADO.md
docs/E06_AUDITORIA.md

El dossier principal debe seguir siendo conciso.

No trasladar explicaciones extensas innecesarias al documento evaluado.

El README de P2_E06 debe explicar cómo reproducir los resultados principales.

# 22. AUDITORÍA FINAL DE LA RÚBRICA

Evaluar:

A. Cobertura y calidad de verificación — 1,1 puntos.

B. Convergencia y conservación — 0,7 puntos.

C. BIM base y consistencia geométrica — 0,6 puntos.

D. Síntesis, trazabilidad y reproducibilidad — 0,6 puntos.

Para cada criterio:

- Evidencia presentada.
- Resultado comprobado.
- Defectos encontrados.
- Acción correctiva.
- Estado final.

Distinguir entre:

CUMPLE Y VERIFICADO.
CUMPLE CON OBSERVACIONES.
NO VERIFICADO.
NO CUMPLE.

No asignar puntuaciones máximas garantizadas.

# 23. INFORME FINAL DE EJECUCIÓN

Al terminar, informa:

1. Ruta de P2_E06.
2. Ruta exacta del dossier Markdown.
3. Cantidad de palabras.
4. Figuras generadas.
5. Matriz de pruebas.
6. Tests ejecutados y resultados.
7. Convergencia espacial.
8. Convergencia temporal.
9. Conservación.
10. Fuente uniforme.
11. Robin.
12. Estado BIM.
13. Simplificaciones incluidas.
14. Reproducibilidad.
15. Pendientes formales o técnicos.
16. Veredicto final.

# RESTRICCIONES FINALES

No crear commits.
No hacer push.
No publicar en GitHub.
No modificar carpetas anteriores.
No implementar E07 ni etapas posteriores.
No inventar evidencias.
No reutilizar resultados incompatibles.
No exceder 1.200 palabras en el dossier.

# CRITERIO FINAL DE ACEPTACIÓN

E06 estará técnicamente COMPLETA solamente cuando:

- Exista el dossier Markdown.
- Su extensión cumpla el límite.
- Incluya los nueve contenidos obligatorios.
- La matriz de verificación esté respaldada por resultados reales.
- Los estudios de convergencia sean correctos.
- La conservación y las fuentes se comprueben.
- Robin esté verificado.
- El modelo BIM sea coherente y esté documentado.
- La figura BIM corresponda al IFC real.
- Las simplificaciones estén explícitas.
- El IFC esté disponible y sea reproducible.
- P2_E06 sea una carpeta autónoma.
- No existan errores técnicos bloqueantes.

El estado de publicación y el commit deben registrarse por separado. No declarar formalmente cerrada la entrega si falta alguno de los identificadores exigidos.

Comienza ahora inspeccionando P2_E05 y preparando la carpeta autónoma P2_E06.