# E14 — Identificación de la entrega

Repositorio: [amvaras/Proyecto-2-MCOC](https://github.com/amvaras/Proyecto-2-MCOC).

Rama: `codex/e14`. Etiqueta: [entrega-e14](https://github.com/amvaras/Proyecto-2-MCOC/tree/entrega-e14/P2_E14).

El commit evaluado es el SHA completo al que apunta `entrega-e14`. Para obtenerlo desde una copia Git actualizada:

```powershell
git rev-parse entrega-e14
```

Canvas solicita el enlace del repositorio y ese SHA. No declarar el SHA de E13 ni inventar un ID de job remoto.

## Alcance comprobado

- Monte Carlo: ocho planes, 10000 realizaciones por plan y comparación con enumeración exacta de 24 escenarios por plan.
- Batería integrada: 447 pruebas aprobadas durante la auditoría; controles posteriores dirigidos y evidencia JUnit incluidos.
- Demostración local: N=1000, semilla 20261121, 24 simulaciones nuevas con dos procesos; métricas, balances y hashes de campos idénticos a las referencias.
- Nueva semilla, reutilización de inputs, reanudación, agregación separada, Pf(N) e intervalos comprobados.
- Slurm: scripts y emulación local comprobados. **Acceso a cluster no confirmado; ejecución remota sin acreditar.** Esta limitación permanece explícita frente al enunciado.

[Guía de uso local](E14_DEMO_LOCAL.md), [auditoría](E14_AUDITORIA_20261118.md) y [evidencia de la demostración](../results/verification/demo_local_e14.json).

La identificación del README y el generador del inventario recibieron cambios administrativos para publicar. La migración del índice sellado está declarada en `results/verification/publicacion_final_e14.json`: no cambia código físico, inputs, temperaturas, probabilidades ni figuras. Los resultados siguen indicando que no se encontró un plan térmicamente factible bajo el modelo y los pesos declarados.
