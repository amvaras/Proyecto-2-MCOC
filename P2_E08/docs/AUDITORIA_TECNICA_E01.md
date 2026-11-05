# Auditoría técnica integral E01 — Grupo 2

Fecha: **20 de octubre de 2026**. Alcance: archivos reales, formulación, código,
pruebas, entorno, benchmark, modelo IFC/Bonsai y documentación técnica.

## Veredicto técnico general

**COMPLETO.** Los cinco requisitos técnicos obligatorios de E01 están
implementados y verificados después de las correcciones. No queda un defecto
bloqueante ni un requisito técnico obligatorio pendiente.

La revisión partió de las guías G00/G01/G02/G05 del ZIP del curso, la guía
geométrica docente y el enunciado E01 proporcionado. Se inspeccionó el código
y se volvieron a ejecutar los cálculos; no se tomó el informe anterior como
prueba suficiente. El caso G2 conserva Freirina/costa de Huasco, Sarco, Atacama,
latitud **-28.856102**, longitud **-71.421831**.

## Matriz de cumplimiento

| Requisito técnico | Evidencia | Resultado | Estado | Defecto/pendiente | Acción correctiva |
|---|---|---|---|---|---|
| README mínimo y comandos | README.md, ejecución desde raíz | Instalación, tests, ejemplo y scripts documentados y ejecutados | CUMPLE Y VERIFICADO | Texto previo de Bonsai desactualizado | Se corrigió su estado y se enlazaron las capturas |
| Entorno reproducible | pyproject.toml, requirements-lock.txt, environment_rebuild.json | Python 3.12.10, 24 versiones idénticas, entorno limpio, pip check sin conflictos | CUMPLE Y VERIFICADO | Faltaba una rueda en la caché local de la auditoría | Se completó el suministro local y se reinstaló sin cambiar versiones |
| Imports, estructura e independencia | src/, tests/, instalación editable y suite nueva | Solver importa NumPy y biblioteca estándar; no requiere Blender | CUMPLE Y VERIFICADO | Ninguno | No requirió cambios |
| Primeros tests automatizados | pytest.txt y pytest.xml | 67 aprobadas, 0 fallidas, 0 errores, 0 omitidas | CUMPLE Y VERIFICADO | Casos límite no cubiertos antes | 13 pruebas adicionales |
| Formulación y solver 1D | diffusion_1d.py y FORMULACION_1D.md | Balance por celda, FTCS/Euler, medias celdas, fuente SI | CUMPLE Y VERIFICADO | Energía fallaba para dx entero | Anchos flotantes y prueba de regresión |
| Validación de entradas | Validadores y pruebas negativas | Finitud, positividad física, formas y tipos de borde controlados | CUMPLE Y VERIFICADO | Se descartaba parte imaginaria de un vector complejo | Rechazo explícito antes de convertir a float |
| Inicial y Dirichlet/Neumann/Robin | API y tests físicos/analíticos | Signos salientes consistentes, aislación, calentamiento y enfriamiento verificados | CUMPLE Y VERIFICADO | Ninguno en las ecuaciones inspeccionadas | Se amplió cobertura de calentamiento Robin |
| Estabilidad explícita | stable_timestep y tests | Fo≤0,5 y Fo(1+h dx/k)≤0,5 en extremos Robin | CUMPLE Y VERIFICADO | Ninguno | Se mantuvo cota suficiente y alcance documentado |
| Conservación y fuentes | Tests de energía y fuente | Intercambios internos opuestos; balance exterior por paso | CUMPLE Y VERIFICADO | Ninguno | Se conservó el esquema funcional |
| Solución exacta y benchmark | diffusion_1d.json/npz/png y accuracy.json | 24 h, 1280 pasos, Fo=0,4, error 0,000645135652 °C | CUMPLE Y VERIFICADO | Ninguno | Se recalculó error y analítica desde los datos guardados |
| Convergencia espacial/temporal | Tests y check_diffusion_accuracy.py | Segundo orden espacial; primer orden temporal aislado | CUMPLE Y VERIFICADO | Antes solo había refinamiento conjunto dt~dx² | Se agregaron estudios separados |
| Primer modelo IFC/Bonsai | foundation.ifc, validador y ocho capturas | IFC4 legible y abierto en Bonsai, cinco IfcFooting | CUMPLE Y VERIFICADO | La documentación no incorporaba la revisión humana nueva | Se inspeccionaron y registraron las ocho capturas |
| Identidad, jerarquía y propiedades | check_ifc.py y pruebas negativas | GUID únicos, cadena espacial, material, pset y cotas coherentes | CUMPLE Y VERIFICADO | No se contrastaban todas las cotas declaradas ni cadena completa | Validador ampliado |
| Geometría, unidades y solapamientos | ifc_check.json | Metros; 18×18×4,30 m global; mallas cerradas, volúmenes y diez parejas sin solapamiento | CUMPLE Y VERIFICADO | Comprobaciones anteriores menos explícitas | Se añadieron anillos, orientación, conectividad y controles entre pares |
| Evidencia y documentación técnica | E01_ESTADO, E01_EVIDENCIAS, IFC_BONSAI y registros | Coherentes con la ejecución y observaciones actuales | CUMPLE Y VERIFICADO | Estados obsoletos y sobrescritura de registros | Actualización técnica, archivo previo e historial automático |
| Criterios reales de 14 días, Tmax≤70 °C y ΔTmax≤20 °C | Contexto documentado | No se presentan como calculados por el benchmark | NO APLICA A E01 | Ninguno para E01 | Reservados a etapas posteriores |
| Clima, hidratación avanzada, voxelización y solver final | Alcance del proyecto | No se implementaron como parte de esta auditoría | NO APLICA A E01 | Ninguno para E01 | Sin ampliación de alcance |

## Resultados reales de las pruebas

- Inicio: **54 aprobadas en 6,12 s**, 0 fallidas y 0 omitidas.
- Tras corregir y ampliar cobertura: **67 aprobadas en 11,99 s**.
- Verificación integral en el entorno reconstruido: **67 aprobadas en 12,33 s**,
  0 fallidas, 0 errores y 0 omitidas; 12,323 s en el XML de pytest.
- Los siete procesos del verificador integral terminaron con código 0:
  comprobación de dependencias, suite, benchmark, estudio de precisión,
  verificador IFC, generación de vista previa y contraste de evidencia Bonsai.

Los tests cubren resultados físicos y numéricos: conservación adiabática de
perfil no uniforme, estado uniforme, fuente uniforme y espacial, extremos
prescritos, signo del flujo en ambas caras, Robin frío/caliente, condición de
estabilidad, soluciones exactas y validación de entradas. Las tres pruebas IFC
nuevas rechazan modificaciones deliberadamente incoherentes de propiedades o
jerarquía en copias temporales; no cambian el modelo entregado.

## Estado del solver y benchmark

Se revisó la actualización real. Cada intercambio interno k(T_j-T_i)/dx se
suma a una celda y se resta a su vecina. La capacidad por área es rho cp dx
en interiores y rho cp dx/2 en extremos; la fuente aporta q_dot*w. Neumann y
Robin se restan como potencia saliente, con la misma convención en ambas caras.
Se usa el estado viejo completo para calcular flujos antes de actualizar.
Dirichlet se impone inicialmente y después de cada paso.

La cota de monotonía incluye simultáneamente conducción y convección. No se
extiende a fuentes dependientes de T, materiales heterogéneos o fronteras
con dinámica propia. No se encontró un defecto en las ecuaciones soportadas.

El benchmark reprodujo exactamente los parámetros reportados: 86400 s,
dt=67,5 s, 1280 pasos, Fo=0,4 y error máximo 0,0006451356521708362 °C.
La solución exacta sinusoidal satisface las condiciones iniciales y Dirichlet;
el chequeo independiente desde NPZ coincidió con JSON. La figura nueva fue
inspeccionada y representa esos perfiles e historia térmica.

Refinamiento espacial con dt=1 s: errores 0,00683600 → 0,00170988 →
0,000424847 °C al reducir dx a la mitad (cocientes ≈4). Refinamiento temporal
sobre malla fija, usando como referencia el modo semidiscreto exacto: errores
0,0167731 → 0,00836970 → 0,00418066 → 0,00208928 °C (cocientes ≈2).
Así se comprueban por separado los órdenes esperados, sin confundirlos con
el refinamiento conjunto de la batería inicial.

## Estado BIM/IFC y revisión Bonsai

Modelo IFC4 existente, jerarquía correcta, unidades en metros, origen local,
cinco IfcFooting con nombres y propiedades individuales. Esquema/EXPRESS:
**cero incidencias**. Se verificaron los intervalos de vertida 0–0,55;
0,55–1,10; 1,10–2,20; 2,20–3,30; 3,30–4,30 m y el cilindro de diámetro 7 m.
El modelo conserva sus dimensiones y no necesitó modificación.

Volúmenes analíticos: 147,625714; 147,625714; 214,224351; 88,924748 y
38,484510 m³. Los cuatro volúmenes octagonales coinciden con su triangulación
a redondeo; el cilindro teselado difiere aproximadamente 0,019 %, dentro de la
tolerancia geométrica declarada. Las diez parejas no tienen intersección de
interiores: sus intervalos Z están separados o solo comparten una cara.

Las ocho capturas existen en **Evidencias/bonsai/** y fueron inspeccionadas.
Se ven Blender **5.1.2**, Bonsai **v0.9.0-post1**, IFC4, las cinco entidades,
selección individual, UANDES_HormigonMasivo y los ID/cotas correspondientes.
Las vistas son 3D, superior y posterior ortográfica. Los GUID se ven truncados;
sus prefijos coinciden y los valores completos se verificaron automáticamente.

Se distingue la evidencia humana aportada de la validación desde Python.
El auditor no afirma haber operado otra sesión de Blender. Las capturas y
la validación conjunta cubren la revisión del primer modelo para E01.

## Defectos y correcciones

| Hallazgo | Impacto técnico original | Corrección | Estado final |
|---|---|---|---|
| dx entero en energía | Entradas SI válidas causaban UFuncTypeError al formar medias celdas | dtype=float en _widths y regresión con dx=1 | Corregido y verificado |
| Campos complejos | Conversión silenciosa perdía información imaginaria | Validación antes de convertir initial, q_dot y temperatura energética | Corregido y verificado |
| Falta de prueba temporal aislada | No permitía atribuir orden temporal por separado | Solución semidiscreta exacta sobre malla fija; estudio espacial separado | Corregido y verificado |
| Control IFC incompleto | Cotas declaradas o jerarquía incorrectas podían pasar el verificador anterior | Contraste de pset/geometría, cadena espacial y pruebas negativas | Corregido y verificado |
| Documentación de Bonsai obsoleta | Presentaba una revisión realizada como pendiente | Inspección de ocho imágenes y actualización con procedencia explícita | Corregido y verificado |
| Registros de ejecución reemplazables | Repetir una corrida podía perder resultados anteriores | Archivo previo, salida configurable e historial automático | Corregido; copia previa existente y resultados nuevos separados |

No se cambió la arquitectura ni se sustituyó el esquema térmico funcional por
preferencias de estilo. Las correcciones se limitaron al alcance técnico E01.

## Reproducibilidad, limitaciones y cierre

El entorno se reconstruyó vacío en Python 3.12.10 / Windows AMD64. Se instalaron
las 24 versiones fijadas y el paquete editable; pip check, tests y todos los
scripts corrieron correctamente allí. Se usaron ruedas locales y se documentó
cómo se suplió la que faltaba; no se afirma una descarga remota nueva. Logs y
proveniencia: `docs/evidencias/auditoria/environment_rebuild.json` y archivos de
instalación en la misma carpeta.

Límites explícitos: grilla uniforme 1D, material constante, fronteras constantes
y fuente prescrita independiente de temperatura/tiempo. El benchmark no es
validación experimental del hormigón ni predicción térmica de la fundación.
La integración geométrica, las propiedades de material calibradas y los análisis
finales pertenecen a etapas posteriores. No se exige otro sistema operativo
para la reproducibilidad ya comprobada en el entorno documentado.

Se conservaron registros anteriores; las evidencias actuales incluyen versiones,
salidas de procesos, JUnit, datos NPZ/JSON y figuras. No se observa un requisito
técnico obligatorio sin verificar.

**¿Está completo el trabajo técnico exigido para E01? Sí. No quedan requisitos
técnicos obligatorios pendientes.**
