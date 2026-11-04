# MCOC — PROYECTO 2 — GRUPO 2
## E07 — VOXELIZACIÓN, VERTIDAS E HIDRATACIÓN
### Desarrollo técnico completo y preparación de revisión oral
### Miércoles 4 de noviembre de 2026 — 4 puntos

Actúa como ingeniero civil experto en transferencia de calor, construcción de hormigón masivo, modelación BIM/IFC, IfcOpenShell, geometría computacional, métodos numéricos, Python y verificación científica.

Tu misión es desarrollar completamente la entrega E07 sobre la base técnica verificada de E06, integrando por primera vez la geometría real IFC con una grilla térmica cartesiana 3D.

Debes inspeccionar archivos reales, implementar código, ejecutar pruebas, generar resultados y documentar la evidencia.

No te limites a proponer ideas.

No inventes resultados y no declares completadas funciones que no hayas ejecutado.

# 1. CARPETAS Y PROTECCIÓN DE ENTREGAS

Directorio raíz:

C:\Users\javie\OneDrive\Escritorio\Universidad\9no semestre\MCOC\Proyecto 2

Base verificada:

P2_E06

Nueva entrega:

P2_E07

Crear:

C:\Users\javie\OneDrive\Escritorio\Universidad\9no semestre\MCOC\Proyecto 2\P2_E07

P2_E07 debe ser completamente independiente.

Copiar físicamente desde E06 los archivos útiles: código, IFC, pruebas, dependencias, ejemplos, configuraciones, documentación y evidencias necesarias.

No copiar entornos virtuales ni cachés recreables.

No utilizar enlaces simbólicos ni rutas externas obligatorias.

No modificar E01–E06.

Registrar inventarios SHA256 antes y después para comprobar integridad.

Si E07 ya existe, inspeccionarla y preservar su trabajo.

No crear commits, ramas, PR ni hacer push sin autorización.

IMPORTANTE: E06 mantiene pendiente su commit formal. No afirmar que el problema está resuelto ni reutilizar un commit E01 como identificador E07.

# 2. ENUNCIADO OFICIAL

E07 — Semana 3 / miércoles — Revisión oral: voxelización, vertidas e hidratación.

Fecha: miércoles 4 de noviembre de 2026, 10:30–13:20.

Puntaje: 4 puntos.

Objetivo:

Conectar el BIM real con la grilla térmica y formular la construcción por vertidas.

Antes de la actividad, el repositorio debe incluir:

1. Extracción de geometría IFC.
2. Primer voxelizador.
3. vertida_id.
4. Estimación de volumen.
5. Diseño del modelo de hidratación.
6. Estructura para activación temporal.

Durante la actividad pueden preguntar:

- ¿Cómo decide el código si un vóxel pertenece al sólido?
- ¿Qué error produce la frontera staircase?
- ¿Cómo cambia el error de volumen con Δx?
- ¿Cómo identifica una superficie exterior?
- ¿Qué ocurre en una interfaz entre dos vertidas?
- ¿Cómo se inicializa una vertida nueva?
- ¿Qué unidades tiene Qdot_h?
- ¿Cómo se relaciona una curva adiabática con generación volumétrica de calor?
- ¿Cómo influye la temperatura en la hidratación si el modelo la considera?

Debes preparar evidencia técnica y respuestas que correspondan al código realmente implementado.

# 3. BASE TÉCNICA E06

E06 reportó:

- 198 pruebas aprobadas.
- Soluciones exactas 1D, 2D y 3D.
- Convergencia espacial de orden aproximado 2.
- Convergencia temporal de orden aproximado 1.
- Conservación adiabática.
- Fuente uniforme.
- Neumann y Robin.
- Estabilidad explícita.
- Modelo IFC4 con cinco vertidas.
- Volumen analítico total 636,885036448 m³.

El IFC de referencia está en:

geometry/foundation.ifc

Contiene cinco elementos IfcFooting con propiedades UANDES_HormigonMasivo.

Vertida_01: z=0,00–0,55 m.
Vertida_02: z=0,55–1,10 m.
Vertida_03: z=1,10–2,20 m.
Vertida_04: z=2,20–3,30 m.
Vertida_05: z=3,30–4,30 m.

Geometría docente:

- Octágono exterior de 18 m entre caras.
- Espesor de borde de 1,10 m.
- Espesor central de 3,30 m.
- Pedestal circular de diámetro 7 m.
- Altura adicional del pedestal de 1,00 m.
- Altura total de 4,30 m.

Estas cifras deben comprobarse desde el IFC real antes de utilizarlas como referencias.

# 4. INSPECCIÓN Y PLAN DE IMPLEMENTACIÓN

Antes de modificar:

1. Revisar la arquitectura del paquete mcoc_p2.
2. Revisar thermal_nd.py.
3. Revisar el lector y generador IFC existentes.
4. Revisar la representación geométrica obtenida mediante IfcOpenShell.
5. Revisar las pruebas actuales.
6. Revisar las 198 pruebas heredadas.
7. Revisar las convenciones de coordenadas y unidades.
8. Revisar resultados de E06.

Diseñar módulos claros y testeables.

Evitar modificar el solver E06 salvo necesidad justificada.

Mantener separadas:

- Lectura IFC.
- Geometría.
- Voxelización.
- Etiquetado de vertidas.
- Detección de superficies.
- Modelo de hidratación.
- Activación temporal.
- Simulación y ejemplos.

# 5. EXTRACCIÓN IFC REAL

Leer el IFC mediante IfcOpenShell.

Por cada IfcFooting:

- Identificador IFC GUID.
- Nombre de elemento.
- VertidaID.
- Estado si existe.
- Transformación local/global.
- Vértices.
- Triángulos.
- Bounding box.
- Volumen.
- Elevación inferior y superior.
- Propiedades relevantes.

Respetar las transformaciones de ubicación y las unidades IFC.

No asumir que todas las coordenadas ya se encuentran en el mismo sistema.

Verificar orientación y cierre de mallas.

Evitar contar dos veces geometría o utilizar representaciones duplicadas.

Preparar una estructura de datos explícita para las cinco vertidas y sus sólidos.

Comprobar unicidad de identificadores y coherencia de elevaciones.

Registrar geometría extraída en formatos reproducibles.

# 6. GRILLA CARTESIANA Y VOXELIZACIÓN

Crear un primer voxelizador 3D para la fundación real.

Definir explícitamente:

- Origen de la grilla.
- Ejes X, Y, Z.
- Resoluciones Δx, Δy, Δz.
- Dimensiones nx, ny, nz.
- Centros de vóxel.
- Bounding box.
- Posible margen exterior.
- Convención para vóxeles ocupados.

Emplear inicialmente un esquema basado en centros de vóxel: una celda pertenece al sólido si su centro está dentro del sólido IFC.

Debe funcionar sobre las geometrías extraídas, no sobre una fundación recreada a mano.

Implementar una prueba punto-en-sólido robusta para mallas cerradas, por ejemplo mediante un método geométrico verificado.

Si se utiliza ray casting, manejar degeneraciones de rayos, triángulos, aristas y vértices.

Documentar las decisiones para centros exactamente sobre fronteras.

No utilizar exclusivamente las cajas envolventes como criterio de pertenencia.

La bounding box sirve para acelerar; no reemplaza el sólido verdadero.

Si existen bibliotecas geométricas adicionales, justificar su uso y asegurar instalación reproducible.

# 7. VERTIDA_ID

Cada vóxel debe tener una etiqueta inequívoca:

0 = vacío.
1 = Vertida_01.
2 = Vertida_02.
3 = Vertida_03.
4 = Vertida_04.
5 = Vertida_05.

Si conviene otra convención interna, documentarla claramente y mantener una correspondencia inequívoca.

Entregar:

- occupation_mask.
- vertida_id.
- Coordenadas de centros.
- Volumen por celda.
- Propiedades de grilla.
- Correspondencia GUID ↔ VertidaID.

Comprobar que:

- Ninguna celda tenga dos identificadores.
- No existan identificadores desconocidos.
- El número de celdas ocupadas sea coherente.
- Cada vertida tenga volumen positivo.
- Se conserven los identificadores IFC.

Para casos en que el centro caiga justo en una interfaz, utilizar una convención determinista y documentada.

# 8. VOLUMEN Y ERROR STAIRCASE

Estimar el volumen mediante:

V_voxel = N_ocupados × Δx × Δy × Δz.

Calcular:

- Volumen voxelizado total.
- Volumen IFC o analítico de referencia.
- Diferencia absoluta.
- Error relativo.
- Volumen por vertida.
- Error por vertida.

Ejecutar al menos tres resoluciones de grilla razonables y reproducibles.

Analizar cómo cambia el error con Δx.

No asumir que el error siempre disminuye monótonamente en cada refinamiento de una voxelización por centros.

Distinguir tendencia general de convergencia frente a oscilaciones por alineamiento de grilla.

Explicar staircase:

La frontera curva o inclinada se representa por caras escalonadas de celdas cartesianas, introduciendo errores de volumen, posición de superficie y área superficial.

Registrar costo computacional, resolución y número de vóxeles.

No ejecutar refinamientos que agoten memoria innecesariamente.

Preparar gráfico:

figures/e07_error_volumen.png

El gráfico debe mostrar error volumétrico frente a tamaño de celda o resolución.

# 9. SUPERFICIES EXTERIORES

Implementar identificación de caras expuestas del sólido voxelizado.

Para una celda ocupada, examinar sus seis vecinos cartesianos.

Una cara corresponde a superficie exterior si:

- La celda es sólida.
- Su vecino en la dirección normal es vacío o está fuera del dominio.

Guardar, como mínimo:

- Índice de vóxel.
- Dirección de cara.
- Área.
- Normal saliente.
- VertidaID.
- Clasificación geométrica.

Calcular:

- Número de caras exteriores.
- Área exterior aproximada.
- Área por orientación.
- Área por vertida.

No confundir superficie exterior del sólido completo con superficies temporalmente expuestas durante la construcción.

Preparar ambas nociones cuando sea pertinente:

1. Superficie exterior geométrica del sólido completo.
2. Superficie expuesta de la geometría activa en un instante.

# 10. INTERFACES ENTRE VERTIDAS

Identificar caras vecinas donde:

- Ambos vóxeles pertenecen al sólido.
- Tienen vertida_id distintos.

Estas son interfaces internas entre vertidas.

No clasificarlas como superficies exteriores del sólido completo.

No imponer Robin automáticamente sobre interfaces internas.

Documentar la conducción entre vertidas mediante conductancia térmica apropiada cuando ambas están activas.

Si se supone contacto térmico perfecto, declararlo como simplificación.

Si una vertida vecina todavía no se ha activado, no tratarla como material sólido activo.

En ese instante la cara de la vertida existente puede quedar expuesta al ambiente o a otra condición de borde según la hipótesis constructiva.

Preparar tests para distinguir estos tres casos:

- Misma vertida.
- Dos vertidas activas.
- Vertida activa frente a vertida futura.

# 11. ESTRUCTURA DE ACTIVACIÓN TEMPORAL

Diseñar e implementar una estructura de datos con eventos de construcción.

Cada vertida debe admitir:

- VertidaID.
- Tiempo de activación.
- Temperatura inicial de colocación.
- Parámetros térmicos.
- Parámetros de hidratación.
- Estado activo/inactivo.

Preparar una API clara, por ejemplo:

active_mask(t)
activate_pour(id, time, initial_temperature)
pour_age(t, id)

Los nombres definitivos pueden variar si existen alternativas más coherentes.

Requisitos:

- Antes de su activación, una vertida no participa en la capacidad térmica ni en los intercambios conductivos.
- Cuando se activa, sus celdas reciben la temperatura inicial especificada.
- Su edad térmica o edad desde vertido comienza en cero.
- Los eventos se procesan en orden cronológico.
- Un mismo evento no debe aplicarse dos veces.
- Cambios de activación deben modificar las superficies expuestas.
- El paso temporal debe alcanzar con precisión los instantes de activación, sin saltarlos.

Probar eventos en t=0 y en tiempos posteriores.

Definir qué sucede si dos vertidas se activan simultáneamente.

No asumir automáticamente un calendario constructivo real.

Utilizar un cronograma ficticio explícitamente etiquetado como demostración.

# 12. DISEÑO DEL MODELO DE HIDRATACIÓN

Implementar el diseño matemático y una interfaz testeable de generación térmica por hidratación.

Definir una función:

q_dot_h(t, T, material, estado)

con resultado en W/m³.

Seleccionar y justificar un modelo preliminar razonable.

Puede ser, por ejemplo:

A. Curva prescrita de calor adiabático o temperatura adiabática, o

B. Modelo cinético de grado de hidratación.

Se debe separar:

- Calor total potencial.
- Tasa de liberación de calor.
- Grado de hidratación.
- Edad desde vertido.
- Dependencia térmica, si se modela.

Si se utiliza grado de hidratación ξ:

0 ≤ ξ ≤ 1.

q_dot_h = H_vol × dξ/dt.

H_vol debe tener unidades J/m³.

dξ/dt tiene unidades 1/s.

Por tanto q_dot_h tiene unidades W/m³.

Si se parte de una curva adiabática T_ad(t), explicar la relación ideal:

q_dot_h = rho*cp*dT_ad/dt.

Esta relación supone ausencia de pérdidas, capacidad térmica apropiada y consistencia en la definición de tiempo/edad.

Distinguir calor de hidratación de una fuente uniforme arbitraria usada como benchmark.

No inventar parámetros calibrados para el hormigón real de Freirina.

# 13. DEPENDENCIA DE TEMPERATURA

Si el modelo preliminar considera dependencia térmica, formularla claramente.

Puede utilizar una función cinética basada en Arrhenius o madurez equivalente, con parámetros configurables y unidades verificables.

Distinguir:

- Temperatura Celsius usada en las simulaciones.
- Temperatura Kelvin para expresiones termodinámicas.
- Edad real.
- Edad equivalente de hidratación.

Evitar exponentes físicamente inconsistentes y errores Celsius/Kelvin.

Preparar al menos pruebas de:

- Fuente positiva cuando corresponda.
- Fuente nula una vez agotado el calor disponible.
- Conservación de calor total potencial.
- Reinicio de edad al activar una nueva vertida.
- Respuesta al cambio de temperatura si la dependencia está habilitada.

Si no existen datos suficientes para calibrar, declarar la dependencia térmica como conceptual o preliminar.

# 14. ACOPLAMIENTO CON EL SOLVER E06

El objetivo es conectar el BIM con la grilla térmica.

Preparar una estructura compatible con el solver cartesiano existente.

Reutilizar donde sea correcto:

- Convenciones de centros de celda.
- Capacidad térmica volumétrica.
- Conductancias.
- Fuentes volumétricas.
- Condiciones de borde.

Realizar una demostración mínima que confirme que:

- La grilla se genera desde el IFC.
- Las celdas conservan vertida_id.
- Se pueden identificar máscaras activas.
- Las interfaces y fronteras se clasifican correctamente.
- La fuente de hidratación tiene dimensiones correctas.

Para E07 es suficiente que el modelo de hidratación y la activación temporal estén formulados e implementados como estructura de prueba.

No presentar una simulación térmica final de fundación si el acoplamiento transiente completo todavía no existe.

No forzar el solver de caja completa a representar celdas vacías como hormigón con parámetros ficticios.

Si se requiere un solver de dominio enmascarado, identificar claramente si está implementado o si permanece como siguiente paso.

# 15. PRUEBAS AUTOMATIZADAS

Crear tests nuevos para:

1. Lectura de cinco IfcFooting.
2. GUID y VertidaID.
3. Unidades IFC.
4. Centros interiores y exteriores.
5. Volumen total.
6. Volumen individual.
7. Cambio de volumen con resolución.
8. Robustez geométrica.
9. Detección de caras exteriores.
10. Detección de interfaces internas.
11. Interfaces activas.
12. Activación temporal.
13. Temperatura inicial al activar.
14. Edad desde vertido.
15. Fuente de hidratación y unidades.
16. Curva adiabática.
17. Dependencia térmica, si se implementa.
18. Conservación del calor potencial.
19. Compatibilidad con el solver existente.
20. Regresión de todos los tests E01–E06.

No crear tests triviales exclusivamente para aumentar el número.

Utilizar casos sintéticos simples con solución conocida para aislar la corrección del voxelizador.

Para la fundación real, comparar volumen con referencia IFC independiente.

No utilizar el mismo algoritmo como única fuente de verdad de su propia prueba.

# 16. DEMOSTRACIONES

Crear:

examples/run_e07.py

Debe permitir:

- Inspeccionar el IFC.
- Voxelizar.
- Elegir tamaño de celda.
- Mostrar volumen y error.
- Mostrar vertida_id.
- Identificar caras exteriores.
- Identificar interfaces.
- Ejecutar activación temporal de ejemplo.
- Mostrar el modelo de hidratación preliminar.
- Guardar resultados reproducibles.

Preparar comandos sencillos en PowerShell.

El programa debe rechazar entradas inválidas y documentar claramente sus límites.

No utilizar rutas absolutas obligatorias.

# 17. FIGURAS

Generar figuras claras a partir de datos reales:

1. Fundación voxelizada, diferenciando vertidas.
2. Error de volumen frente a resolución.
3. Interfaces y superficies exteriores.
4. Cronograma ilustrativo de activación.
5. Curva preliminar de hidratación o fuente térmica.

Usar Matplotlib u otras bibliotecas ya disponibles cuando sea razonable.

Evitar figuras decorativas que no representen resultados reales.

Si una figura utiliza parámetros hipotéticos, indicarlo en su título o pie.

No presentar visualizaciones reconstruidas desde el IFC como capturas de Bonsai.

# 18. DOCUMENTACIÓN E07

Crear:

docs/E07_FORMULACION.md
docs/E07_DEMO.md
docs/E07_AUDITORIA.md
docs/E07_ESTADO.md

Documentar:

- Lectura IFC.
- Regla punto-en-sólido.
- Convención de índices.
- Definición de vértices y centros.
- Elección de grilla.
- Error staircase.
- Volumen.
- Interfaces.
- Superficies exteriores.
- Activación temporal.
- Inicialización de temperatura.
- Edad de vertida.
- Hidratación y unidades.
- Dependencia de temperatura.
- Estado exacto de integración con el solver.
- Limitaciones y próximos pasos.

Actualizar README con los comandos de E07.

Mantener documentación anterior disponible.

# 19. PREPARACIÓN ORAL

Preparar respuestas simples, precisas y vinculadas al código real para las nueve preguntas oficiales.

Para cada pregunta entregar:

- Respuesta breve de 20 a 40 segundos.
- Explicación física.
- Archivo y función que permiten demostrarla.
- Comando reproducible.
- Qué resultado debería observarse.
- Qué limitación reconocer.

No afirmar que existe una simulación final de hidratación si solamente está diseñado el modelo.

Preparar una secuencia breve de demostración en vivo, tolerante a cambios de parámetros del profesor.

# 20. AUDITORÍA FINAL

Repetir:

- Tests heredados.
- Tests nuevos.
- Verificación IFC.
- Voxelización en distintas resoluciones.
- Estimación volumétrica.
- Clasificación de superficies.
- Identificación de interfaces.
- Activaciones temporales.
- Hidratación.
- Generación de figuras.
- Reproducción desde copia independiente.
- Integridad de entregas anteriores.

Registrar número exacto de pruebas aprobadas y fallidas.

No ocultar fallos ni asumir que un gráfico equivale a una verificación.

Registrar limitaciones y problemas reales.

# 21. MATRIZ DE CUMPLIMIENTO

Crear una tabla:

| Requisito | Implementación | Test | Evidencia | Estado |

Incluir los seis entregables previos obligatorios y las nueve preguntas orales.

Estados:

CUMPLE Y VERIFICADO.
CUMPLE CON OBSERVACIONES.
NO VERIFICADO.
NO CUMPLE.

No declarar completa una capacidad únicamente porque exista su diseño en documentación.

# 22. INFORME FINAL

Al terminar, informar:

1. Ruta P2_E07.
2. Archivos nuevos.
3. Archivos heredados modificados.
4. Tests ejecutados y resultados.
5. Vóxeles generados.
6. Resoluciones verificadas.
7. Volumen voxelizado y error.
8. Volumen por vertida.
9. Superficies exteriores.
10. Interfaces.
11. Activación temporal.
12. Hidratación.
13. Figuras.
14. Comandos de demostración.
15. Estado de integración BIM–solver.
16. Limitaciones.
17. Pendientes.
18. Confirmación de que E01–E06 siguen intactas.

No crear commits ni publicar contenido.

# CRITERIO FINAL DE ACEPTACIÓN

E07 está técnicamente lista para la revisión oral únicamente si:

- Se lee la geometría real del IFC.
- Se genera una grilla voxelizada 3D.
- Cada celda ocupada tiene vertida_id.
- Se estima el volumen.
- Se cuantifica el error geométrico.
- Se identifican superficies exteriores.
- Se distinguen interfaces entre vertidas.
- Existe estructura temporal de activación.
- Se define cómo inicializar una nueva vertida.
- El diseño de hidratación tiene unidades correctas.
- Las funciones nuevas tienen pruebas.
- Los tests anteriores siguen pasando.
- La demostración puede ejecutarse en vivo.
- El estado real de integración con el solver se informa sin exageraciones.
- La carpeta es autónoma.

El commit formal sigue siendo un requisito independiente cuando el curso lo exija, y debe resolverse con autorización antes de presentar un estado de repositorio publicado.

Comienza inspeccionando E06, planificando la integración y desarrollando incrementalmente E07.