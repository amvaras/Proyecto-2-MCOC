# Fuentes consultadas y precedencia

Revisión: 20 de octubre de 2026. Los originales se conservaron sin cambios en
la carpeta superior al clon. No se agregan al repositorio los ZIP ni la PPTX.
El código funciona sin esos archivos.

1. Enunciado E01 y requisitos del usuario: texto adjunto a esta conversación.
   Fuente principal para alcance, rúbrica, horario y límites del trabajo.
2. `guias.zip`: se leyeron G00, G01, G02, G03, G05 y G08; además la formulación
   y ejemplos 1D de `DIFUSION_DE_CALOR_1D_2D_3D.md`.
3. `GUIA_BONSAI_FUNDACION.md`: dimensiones, orientación octagonal, transición,
   clasificación preliminar y flujo IFC. Se conservaron cinco volúmenes.
4. `Presentacion_inicial_P2_Hormigon_Masivo_2026.pptx`: texto extraído de las
   diapositivas para revisar objetivos y separación entre BIM, solver,
   incertidumbre y decisión. No se declara revisión de cada imagen o video.
5. `codigo_difusion.zip`: se inspeccionaron sus cuatro ejemplos Python. Son
   material de apoyo; no son evidencia de ejecución del solver desarrollado.
   Algunos rótulos/comentarios del ejemplo Dirichlet ya no corresponden a sus
   condiciones modificadas. La fuente de calor del ejemplo de calor interno
   está dentro del paréntesis multiplicado por Fo; no se adopta como una fuente
   física en W/m³. Aquí se usa dt*q_dot/(rho*cp) con unidades explícitas.

No se encontraron `00_PROYECTO_GENERAL.md`, un enunciado E01 separado ni el
`course_geometry.json` mencionado por la guía. No se inventó su contenido.
Las coordenadas G2 y criterios globales se tomaron del enunciado proporcionado:
latitud -28.856102, longitud -71.421831, 14 días, 70 °C y 20 °C.
Las demás guías de etapas posteriores fueron inventariadas, sin implementar
esas etapas. Cada integrante aún debe leer personalmente G00/G01/G02/G05.

Referencias técnicas oficiales consultadas como apoyo a la implementación:

- [IfcOpenShell: creación de geometría](https://docs.ifcopenshell.org/ifcopenshell-python/geometry_creation.html).
- [IfcOpenShell: procesamiento geométrico](https://docs.ifcopenshell.org/ifcopenshell-python/geometry_processing.html).
- [Bonsai: exploración de modelos](https://docs.bonsaibim.org/quickstart/explore_model.html).

Las firmas y el comportamiento utilizados se comprobaron también con la
biblioteca IfcOpenShell instalada, no solo con la documentación web.
