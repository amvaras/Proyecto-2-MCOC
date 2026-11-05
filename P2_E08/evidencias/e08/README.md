# E08 — Evidencia verificada

- `verification.json`: 327 tests sin fallos/errores/omisiones, 60 variaciones y dos transientes E08.
- `thermal_regression/`: suite y batería heredada, controles negativos, métricas y referencias.
- `nominal/`: referencia de 72 h, 73 fotogramas y cuatro figuras.
- `modified/`: malla gruesa, intervalo 3 h y colocaciones +5 °C.
- `ui/verificacion_ui.json`: comprobación de controles en navegador y hashes finales de la interfaz.
- `ui/escenario_modificado/`: caso ejecutado desde el formulario: Δ=(0,55;0,55;0,275) m, intervalo 3 h, vertida 2 a 27 °C, horizonte 36 h.
- `ui/interfaz_e08.jpg` y `interfaz_completa.jpg`: capturas reales de la interfaz conectada a Python.
- `cierre.json`: trazabilidad final, base preservada, fuentes y SHA256.

Las rutas absolutas en logs identifican la ejecución original. Los archivos
se conservan sin temporales pytest y con los datos necesarios para leer los
resultados. En E08, los enlaces de figuras del resumen son relativos al caso.

El código científico coincide con el ejecutado. La interfaz fue comprobada en navegador, incluidos escala térmica, etiqueta de
máxima registrada y ayuda de intervalo. El cierre posterior repitió la batería
completa y congeló las mismas fuentes finales con sus resultados.
La instalación se hizo en un entorno nuevo usando las dependencias incluidas,
sin acceder a internet. Los paquetes y el IFC están dentro de P2_E08.

Repetir desde P2_E08: `python scripts/verify_e08.py --output results/e08_nuevo`.
No hay commit ni push nuevos; la publicación y el SHA E08 siguen pendientes.

`historico_pre_cierre/` conserva los artefactos que cambiaron entre la primera
batería y el cierre, incluida la figura 3D anterior al ajuste de etiquetas.
