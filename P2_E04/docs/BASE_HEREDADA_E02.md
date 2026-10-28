# Procedencia de la base E04

Base Git: E02, commit bd332545bc3ecaa29327de7a154dbcf59b43a98b.
Preparación: 27 de octubre de 2026, America/Santiago.
Se copió físicamente P2_E02 a P2_E04, sin imports ni rutas hacia otra entrega.
La raíz E01 y P2_E02 se conservan. Se excluyen entornos y cachés.

El usuario confirmó el 27 de octubre que el equipo realizó la demostración y
defensa E02. Los estados pendientes heredados describen su preparación anterior;
se conservan como historial. No se atribuyen nuevas capturas ni IFC a esta sesión.

E04 agrega thermal_nd.py, tests, demos y verificación; amplía exports y versión
del paquete. El README E02 se preserva en README_HEREDADO_E02.md.
El solver 1D heredado no se modificó. Inventarios y documentos de congelación
anteriores describen sus versiones históricas y no validan esta entrega ampliada.

Adaptación de portabilidad: test_e02.py fija UTF-8 tanto en el subproceso CLI
como en su decodificación. Evita desacuerdo cp1252/UTF-8 en Windows cuando el
proceso principal usa modo UTF-8; no altera las comprobaciones ni el comparador.
