# E05 — Enunciado usado en la auditoría

Transcripción de las instrucciones y de la imagen proporcionadas por el usuario
el 4 de noviembre de 2026. Actividad: jueves 29 de octubre, 10:30–12:30.
Puntaje: 3 puntos. Objetivo: ejecutar en vivo una batería de tests 1D/2D/3D
y condiciones de borde; el ayudante puede seleccionar casos y cambiar parámetros.

## Casos solicitados

- Solución 1D exacta.
- Solución 2D sinusoidal.
- Solución 3D sinusoidal.
- Conservación de energía adiabática.
- Fuente uniforme.
- Neumann.
- Robin.

La imagen especifica:

```text
2D:
T(x,y,t) = T0 + A sin(pi*x/Lx) sin(pi*y/Ly) exp(-alpha*lambda*t)
lambda = (pi/Lx)^2 + (pi/Ly)^2

3D:
T(x,y,z,t) = T0 + A sin(pi*x/Lx) sin(pi*y/Ly) sin(pi*z/Lz) exp(-alpha*lambda*t)
lambda = (pi/Lx)^2 + (pi/Ly)^2 + (pi/Lz)^2

Fuente uniforme adiabática:
dT/dt = q0/(rho*cp)
```

La escritura de T(x,y,z,t) en 3D explicita la dependencia espacial en z que
aparece en el producto de senos de la imagen. Se usa alpha=k/(rho*cp).

## Rúbrica y entrega

| Criterio | Puntos |
|---|---:|
| Batería de tests funcionando | 1,2 |
| Conservación/fuente volumétrica | 0,6 |
| Condiciones de borde | 0,6 |
| Respuesta oral y capacidad de modificar casos | 0,6 |

Canvas solicita repositorio y SHA del commit evaluado. No requiere texto ni
informe. La evaluación de código se realiza sobre el SHA declarado.

Esta transcripción fija el alcance de la revisión; la auditoría técnica y sus
evidencias son documentación interna del proyecto.
