# Estado E02

**Software implementado y verificado. Round-trip humano y defensa oral PENDIENTES.**

No se declara la entrega completamente lista: la edición desde Bonsai es un
requisito obligatorio. Blender de nube es 4.3.2; no se encontró el módulo Bonsai
en su Python. No se abrió ni se editó el IFC desde Bonsai en esta sesión.

| Requisito | Estado | Evidencia |
|---|---|---|
| IFC con cinco objetos y lector Python | CUMPLE Y VERIFICADO | Verificación IFC integral |
| Comparador por GUID, atributos y psets | CUMPLE Y VERIFICADO | Tests E02 y comparación de fixtures |
| Edición y guardado real en Bonsai | IMPLEMENTADO, PENDIENTE DE DEMO REAL | Guía E02_DEMO; no hay IFC humano nuevo |
| Solver parametrizable, nx/dt/t_end | CUMPLE Y VERIFICADO | CLI y simulaciones.json |
| Comparación dx/dt y rechazo inestable | CUMPLE Y VERIFICADO | Simulaciones, tests, inestable.txt |
| Pruebas heredadas y nuevas | CUMPLE Y VERIFICADO | 67 antes; 80 después, ninguna omitida |
| Funcionamiento independiente | CUMPLE Y VERIFICADO | Entorno nuevo fuera del checkout; 80 tests y comandos funcionales |
| Conservación de E01 | CUMPLE Y VERIFICADO | 106 archivos originales sin cambios; IFC idéntico |
| Documentación y guía de defensa | CUMPLE Y VERIFICADO | README y E02_DEMO |
| Defensa oral individual | NO VERIFICADO | Debe realizarla cada integrante |
| Integración IFC al solver, hidratación, 2D/3D | NO APLICA | Fuera del alcance E02 |

Pendiente humano: seguir E02_DEMO, guardar el nuevo IFC, ejecutar comparación,
conservar capturas reales, verificar el modelo editado y actualizar este estado.
Posteriormente publicar la rama autorizada y entregar el SHA real en Canvas.
No se han publicado cambios remotos ni se ha fusionado con main.
