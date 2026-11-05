# E08 — Formulación y verificación

> Consultar la [constancia de publicación E08](PUBLICACION_E08.md).
> Los estados pendientes de los registros originales son históricos.

## Resultado

**Pipeline técnico completo para el laboratorio E08.** La copia autónoma P2_E08
incluye IFC, extracción SI, grilla etiquetada, integrador térmico por etapas,
hidratación funcional, visualización 3D interactiva y edición de inputs.

La suite aprobó **327 pruebas**, sin fallos, errores u omisiones: 307 heredadas
y 20 nuevas E08. Aprobaron también 60 variantes térmicas, dos simulaciones
completas y sus siete controles. El paquete 0.8.0 se instaló en un entorno
nuevo, sin red, desde las ruedas incluidas. No se añadieron dependencias.

## Balance y discretización

Para cada celda activa:

```text
C_i = rho_i * cp_i * V
C_i * dT_i/dt = sum_j G_ij*(T_j-T_i) + q_h*V - sum_f q_out*A
G_ij = A / (dx/(2*k_i) + dx/(2*k_j))
dt <= safety * min_i(C_i / sum(G_i)), con 0 < safety <= 1
```

Las fronteras externas incluyen las conductancias de Dirichlet/Robin en la cota.
Neumann positivo extrae calor. Una cara ante una vertida futura es externa;
al activarse ambas celdas pasa a ser conductiva y deja de recibir Robin interno.
El contacto es perfecto. El conjunto de eventos y tiempos de guardado subdivide
el cálculo: no se salta una colocación y se alcanza exactamente el tiempo final.

La fuente media de un paso se calcula por curva, no por muestreo puntual:

```text
q_h_media = H_vol * (grado(edad_final)-grado(edad_inicial)) / dt  [W/m³]
E_final-E_inicial = Q_h - Q_out + sum_eventos(C_nueva*(T_col-T_ref))
```

T_ref=0 °C por defecto. El estado inicial ya contiene las colocaciones en t=0;
el término de entrada acumulado cuenta solo las colocaciones posteriores.
Las temperaturas anteriores se conservan y solo se inicializan las celdas nuevas.

## Matriz de verificación E08

| Prueba | Referencia / resultado |
|---|---|
| Hidratación por etapas, tres Δt máximos | Dos piezas aisladas; curvas adiabáticas independientes y activación a 37,5 s. Misma energía liberada con pasos 3/47/1000 s. |
| Difusión con incorporación de material | Dos celdas; modo discreto exacto de Euler tras activar la segunda. Temperatura antigua conservada y masa entrante contabilizada. |
| Robin transiente | Voxel único; solución exponencial de su balance discreto; refinamiento temporal confirma primer orden. |
| Estabilidad al cambiar la máscara | Conductividad distinta en la nueva vertida; cota actualizada y pasos dentro de safety. |
| Eventos simultáneos / duración cero | Inicialización consistente, sin aplicar eventos dos veces. |
| Inputs inválidos | Rechazo de pasos no positivos, NaN, presupuesto espacial/historial excesivo y resoluciones repetidas. |
| IFC real y cambios separados | Cambiar solo colocación eleva temperaturas; cambiar solo calendario modifica el campo final. Se conservan inputs y se protege el destino. |
| Aplicación web | Ejecuta el CLI Python, sirve temperaturas reales y conserva escenarios/IFC tras reiniciar. |
| Navegador | Cambio de malla, horarios y colocación; ejecución; slider; reproducción; ocultar/mostrar; cambio de color; escala coherente. |

La referencia nominal de 72 h usa cinco activaciones a 0/6/12/18/24 h,
colocaciones 18/19/20/21/22 °C y 73 fotogramas. Máxima registrada:
**51,64791988 °C**. Volumen: **633,18165625 m³**; error **0,5803408%** frente
a malla IFC. El caso con malla gruesa, intervalo 3 h y colocación +5 °C
registra **56,40883374 °C**. Son parámetros ilustrativos.

Balance nominal: Q_h=41,030171325 GJ, pérdidas netas=9,361585021 GJ,
entrada posterior a t=0=21,059531213 GJ. Residuo global **1,1444e-5 J** frente
a tolerancia previa **0,67785458 J**. La tolerancia escala con las energías,
no con el error observado. El reporte conserva pasos reales, cotas, residuos
por paso y balance acumulado.

## Rúbrica y límites

| Criterio | Estado |
|---|---|
| IFC→grid, 0,9 pt | IFC real y extracción/voxelización existentes conectados con un transiente ejecutado. |
| Geometría/volumen, 0,6 pt | Tres resoluciones, error total/por pieza y cambio interactivo de malla. No se inventa orden ni monotonía. |
| Activación/hidratación, 0,8 pt | Calendario de inputs, al menos dos tiempos distintos, fuente por edad y energía entrante. |
| Demo/explicación, 0,7 pt | Interfaz y guía listas; el desempeño individual debe demostrarlo el grupo. |

Se conservan ocupación por centros y área staircase, incluyendo su sesgo de
orientación. Material constante en tiempo; generación prescrita; bordes constantes
por orientación. El caso nominal utiliza Robin uniforme, también en la base:
es una hipótesis docente, no un modelo calibrado de suelo ni clima real.
No se evalúan aquí criterios finales de seguridad térmica de la obra.

La visibilidad nunca modifica la máscara física: el visor dibuja superficies
por vertida y filtra su presentación. Al ocultar una pieza se revela su vecina;
la solución y sus energías quedan intactas.

La instalación editable inicialmente tropezó con el nombre de la carpeta
temporal protegida del entorno. Se repitió con la autorización solicitada
en la carpeta temporal normal de Windows y aprobó, sin usar internet.
El servidor también se inició fuera del entorno protegido para permitir la
conexión del navegador local. Ambos casos fueron problemas del entorno de
ejecución, no fallos ocultados del solver.

Los antecedentes E01–E07 incluidos describen sus etapas originales. Los módulos
Python heredados permanecen iguales a la base E07 copiada. La evidencia de E08
y su registro de interfaz identifican las comprobaciones actuales. No se hizo
commit ni push; falta declarar el SHA que incluya esta entrega al publicarla.
