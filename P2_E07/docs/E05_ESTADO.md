# E05 — Estado técnico final

Preparación: **28 de octubre de 2026, America/Santiago**.
Actividad: jueves **29 de octubre de 2026, 10:30–12:30**, 3 puntos.

**E05 técnicamente COMPLETA.** Los casos obligatorios están implementados y
comprobados, el núcleo y los tests heredados permanecen intactos y la carpeta
funciona desde otra ubicación con su propio entorno y dependencias locales.

## Resultados efectivamente ejecutados

| Comprobación | Resultado | Evidencia |
|---|---|---|
| Suite heredada antes de ampliar | 137 aprobadas, sin fallos, 20,66 s | evidencias/e05_instalacion/pytest_base.txt |
| Primera suite nueva | 59 aprobadas y 1 fallo temporal, preservado | evidencias/e05_primeros_tests/pytest.xml |
| Suite final completa | **198 aprobadas, 0 fallidas, 0 errores, 0 omitidas; 26,02 s** | evidencias/e05/verificacion_03/pytest.txt y pytest.xml |
| Pruebas nuevas E05 | 61, incluidas en las 198 | tests/test_e05_verification.py |
| Casos CLI | Diez casos y variantes ejecutados con PASS | evidencias/e05/verificacion_03/battery/ y variantes |
| Barrido configurable | 60 combinaciones aprobadas | parameter_sweep.json en la misma verificación |
| Rechazos deliberados | dt excesivo: 2; unidades incompatibles: 2; precisión insuficiente: 1 con FAIL | logs de controles esperados |
| Independencia externa | **198 aprobadas, 0 fallos/omisiones; 25,41 s**, diez casos y otras 60 combinaciones | evidencias/e05_independencia_02/independence.json |
| Modelo IFC | IFC4, cinco IfcFooting, 0 incidencias de esquema | ifc_check.json |
| Dependencias | pip check sin conflictos; instalación desde 24 ruedas incluidas | vendor/wheels y logs de instalación |
| Base Python preservada | 20 archivos heredados comparados, ninguno cambiado | verification.json |
| Entregas anteriores | P2_E01/P2_E02/P2_E04 conservan sus 7579/7660/7722 archivos y fechas | evidencias/e05/proteccion_entregas.json |

Los siete casos mínimos están cubiertos: seno 1D/2D/3D, conservación,
fuente uniforme, Neumann y Robin. Se añadieron estudios separados de orden y
un caso de estabilidad. La CLI admite selección individual/categoría/total,
JSON editable y cambios de parámetros sin editar el solver.

## Métricas de la batería de laboratorio

Con material k=2 W/(m K), rho=2400 kg/m³, cp=900 J/(kg K), 12 celdas por eje,
longitudes 1 m, tiempo 10000 s e inicial sinusoidal de amplitud 10 °C:

| Caso | Error L∞ [°C] | Error L2 RMS [°C] | Criterio L∞ |
|---|---:|---:|---:|
| Exacto 1D | 0,000670749101 | 0,000478383878 | ≤0,03 °C |
| Exacto 2D | 0,001213820492 | 0,000617429445 | ≤0,03 °C |
| Exacto 3D | 0,002314445944 | 0,000839646245 | ≤0,03 °C |

Los pasos efectivos y Fourier están registrados por caso: no se presupone
un mismo dt para distintas dimensiones. Dirichlet está en caras y las
referencias se evalúan en centros de celda. El solver nodal antiguo se
conserva y sus pruebas siguen aprobando.

- Conservación heterogénea 3D: residuo máximo 4,4793e-10 J frente a
  tolerancia 3,0850e-4 J; la temperatura no permanece uniforme ni fija.
- Fuente uniforme de 1000 W/m³ durante 10000 s, caja de 1 m³:
  aumento exacto **4,62962963 °C**, energía generada **10000000 J**,
  error máximo térmico 2,4869e-14 °C.
- Neumann z− de −100 W/m²: aporte esperado **1000000 J**;
  error energético final aproximadamente −3,03e-9 J.
- Robin h=12, inicial 50 °C y aire 20 °C en todas las caras:
  cambio energético −13455099,4154 J, residuo máximo por balance 5,59e-9 J.
  Se comprobaron también calentamiento, h=0 y variación de h.

En los estudios configurables no cúbicos de 1D/2D/3D, órdenes espaciales
entre 1,880 y 1,995 y temporales entre 1,00015 y 1,00055. La batería nominal
2D dio órdenes espaciales 1,9225/2,0014 y temporales 1,0040/1,0020.
Son verificaciones numéricas, sin calibración del caso real.

## Correcciones efectuadas y pendientes

Se corrigió la elección automática temporal para que existan pasos efectivos
distintos al cambiar alpha/L² o duración. Se hizo que n/shape controlen las
mallas de refinamiento y se rechazó una malla fina excesiva antes de reservar
sus arrays. Se preservaron las corridas anteriores, incluida la fallida.
No fue necesario cambiar diffusion_1d.py ni thermal_nd.py.

**Pendientes técnicos obligatorios: ninguno identificado.** El material para
la demostración y preguntas está en E05_DEMO.md; esta verificación de software
no atribuye desempeño individual ni una actividad presencial ya realizada.

## Límites

Cajas cartesianas, propiedades constantes en tiempo, condiciones por cara
constantes, generación prescrita y contacto perfecto. Las referencias exactas
requieren homogeneidad; la heterogeneidad se usa en conservación. No hay
voxelización, clima, hidratación avanzada, activación ni análisis real de
14 días/70 °C/20 °C. Esas limitaciones no son requisitos pendientes de E05.
Las ruedas incluidas y la instalación se comprobaron en Windows x64/Python 3.12.
