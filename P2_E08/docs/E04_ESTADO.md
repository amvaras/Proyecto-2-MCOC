# Estado técnico E04

Preparación: 27 de octubre de 2026, America/Santiago.
**Software y material de preparación listos para la revisión oral.**
La lectura y comprensión de cada integrante y la defensa E04 deben realizarse
personalmente. La implementación no acredita por sí sola esos actos.

## Matriz de requisitos

| Requisito recibido | Implementación/evidencia actual |
|---|---|
| Avance 2D y 3D | thermal_nd.py, demos seno, cortes y soluciones exactas |
| Dirichlet | cara a temperatura prescrita, conducción desde centro a dx/2 |
| Neumann | flujo saliente en cada cara; cero adiabático; pruebas de seis caras |
| Robin | resistencia de media celda más película, casos frío/caliente y modo exacto |
| Fuente volumétrica | escalar o campo W/m³; crecimiento uniforme exacto y balance |
| Dos materiales | k armónica por interfaz y capacidades locales; flujo de capas exacto |
| Balance/estabilidad | formulación, cota local con caras/esquinas y rechazo de dt |
| Avance BIM | IFC4 conservado, cinco vertidas, validación nueva y vista desde Python |
| Lectura Schmidt | fuente original leída, ecuaciones inspeccionadas y nota de estudio |
| Preparación oral | E04_ORAL.md, recorrido y preguntas de la rúbrica |
| Canvas sin informe | repositorio más SHA del commit final publicado |

## Verificación ejecutada

Comando desde P2_E04, con el entorno aislado de la preparación:

```powershell
..\.venv-e04\Scripts\python.exe -X utf8 -B scripts/verify_e04.py --output evidencias/e04
```

El verificador usa el ejecutable del entorno actual. Para repetir después de
instalar esta carpeta de forma autónoma, usar `.\.venv\Scripts\python.exe`
y una salida nueva en results, como indica el README.

Entorno: Python **3.12.14**, Windows x64; NumPy **2.5.4**, pytest **9.1.1**,
Matplotlib **3.11.2**, IfcOpenShell **0.9.0.post1**. Paquete E04 **0.4.0**.
El import se comprobó dentro de P2_E04/src, sin usar el paquete de otra entrega.
`pip check`: sin conflictos.

Suite completa: **137 aprobadas, 0 fallidas, 0 errores, 0 omitidas**, 30,52 s
en la salida de pytest. Incluye las 80 heredadas y 57 nuevas de E04.
Resultados reales: `../evidencias/e04/pytest.txt`, `pytest.xml`,
`verification.json`, `convergence.json`, logs y campos de las demos.
El JSON registra comandos, versiones, códigos de salida y hashes de inputs.
Las horas de las corridas se registran en UTC; la fecha de esta preparación
se expresa en America/Santiago.

## Convergencia separada

Seno exacto sobre cajas 2D/3D. Espacio: n=6/12/24 por eje, dt=5 s fijo,
final=10000 s. Tiempo: n=6 fijo, dt=500/250/125 s, final=50000 s, referencia
semidiscreta para eliminar el error espacial.

| Estudio | Errores [°C] al refinar | Cocientes |
|---|---|---|
| Espacio 2D | 0,03216064 → 0,00846445 → 0,00209449 | 3,7995; 4,0413 |
| Espacio 3D | 0,04253039 → 0,01144570 → 0,00281419 | 3,7158; 4,0671 |
| Tiempo 2D | 0,01529496 → 0,00763229 → 0,00381236 | 2,0040; 2,0020 |
| Tiempo 3D | 0,02127835 → 0,01061545 → 0,00530182 | 2,0045; 2,0022 |

Resultados coherentes con segundo orden espacial y primero temporal; las
mallas gruesas todavía presentan efectos previos al régimen asintótico.
Robin también se contrasta con modo coseno analítico y refinamiento.

## Demos generadas

Todas con n=12 y final=21600 s. Las fuentes y propiedades son ilustrativas.

- Fuente uniforme adiabática 3D de 1000 W/m³: incremento exacto 10 °C,
  error máximo 2,84e-14 °C; error energético absoluto 5,96e-8 J.
- Neumann saliente 100 W/m² en x+ de caja 2D con espesor unitario:
  cambio energético −2160000 J, error reportado 0 J.
- Dos materiales 3D: perfil exacto de capas estacionario, flujo 64 W/m²,
  error final de temperatura reportado 0 °C.
- Robin 3D, h=12 W/(m² K), aire 20 °C e inicial 50 °C:
  centros finales entre 26,0043 y 49,2031 °C. Es una demo de enfriamiento,
  sin atribuirle cumplimiento de los criterios de la fundación.
- Seno 2D y 3D: JSON/NPZ y figuras con evolución/cortes. La demo 3D tiene
  error final 0,01045614 °C con su dt automático; el estudio de convergencia
  controla por separado el efecto de espacio y tiempo.

Se inspeccionaron visualmente las figuras seno 2D/3D y Robin 3D. Las demás
figuras y campos se producen con el mismo programa a partir de sus inputs.

## BIM y conservación

Nueva ejecución del verificador: IFC4 en metros, cinco IfcFooting y **0
incidencias de esquema**, geometrías/propiedades y volúmenes verificados.
La geometría se conserva sin modificaciones respecto de E02. Se generó
`../evidencias/e04/foundation_preview.png` con IfcOpenShell y Matplotlib.
Las ocho capturas Bonsai heredadas se conservan con su procedencia histórica.
No se afirma una nueva operación de interfaz Bonsai en esta sesión.

E01 y P2_E02 no se modificaron. El usuario confirmó que E02 ya se defendió.
P2_E04 incluye una copia física de su base, con README anterior preservado.
Se adaptó la prueba CLI heredada para fijar UTF-8 en ambos extremos del
subproceso. Una corrida inicial detectó ese problema y se preservó localmente
en results/e04/primer_intento; la evidencia vigente es la corrida aprobada.

## Alcance para esta entrega

Cajas cartesianas, propiedades por celda constantes en tiempo, fronteras
constantes por cara, fuente prescrita y contacto perfecto. El solver nodal
1D heredado sigue intacto. No se implementaron hidratación, clima real,
voxelización IFC ni activación. Tampoco se calculó el diferencial real a
25 mm de superficie ni se validó material frente a mediciones.

Antes de Canvas: publicar el commit preparado y usar su SHA real. No se
declara publicada una rama hasta completar y comprobar el push.
