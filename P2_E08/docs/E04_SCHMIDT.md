# Lectura exigida: ICH, Anexo 4, método de Schmidt

ICH, *Especificación para Hormigón Masivo Estructural*, julio de 2019,
Anexo 4, sección 4, página impresa **25** (página **21 del PDF**).
[Página oficial ICH](https://ich.cl/documentos-ich/especificacion-para-hormigon-masivo-estructural/).
[Ejemplar de la biblioteca CChC](https://catalogo.extension.cchc.cl/documentos/documentos/43106-2.pdf).
Consulta: 27 de octubre de 2026. Se leyó el texto y se inspeccionaron visualmente
las ecuaciones de esa página. El PDF completo queda fuera del repositorio.
Cada integrante debe realizar personalmente la lectura.

La sección describe diferencias finitas con nodos y pasos discretos. Presenta
dt=dx²/(2 alpha) y un promedio de dos vecinos para el caso 1D correspondiente.
Incorpora el incremento de temperatura adiabática y señala extensiones a varias
dimensiones y efectos constructivos. Es contexto para el enfoque del curso;
nuestro programa todavía no implementa todas esas extensiones.

Conexión derivada con nuestro balance: en el stencil homogéneo 1D, al elegir
r=alpha*dt/dx²=1/2, el coeficiente propio 1-2r se anula y quedan los vecinos
con peso 1/2. En 2D/3D hay que sumar contribuciones de todos los ejes y revisar
los bordes. E04 permite pasos menores y calcula conductancias locales.

Las viñetas situadas antes del título “4. Método de Schmidt” continúan las
limitaciones del método gráfico anterior. No atribuir a Schmidt la exclusión
del intercambio con el entorno indicada en ese bloque.
