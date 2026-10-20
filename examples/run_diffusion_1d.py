"""Benchmark seno 1D con solución exacta; no predice la fundación de Freirina."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from mcoc_p2 import Dirichlet, Material, solve


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    material = Material(k=2., rho=2400., cp=900.)  # Valores ilustrativos, no calibrados.
    length, nx, end = 1., 81, 86400.
    x = np.linspace(0., length, nx)
    dx = x[1] - x[0]
    result = solve(material=material, length=length, nx=nx,
                   dt=.4 * dx**2 / material.alpha, t_end=end,
                   initial=20 + 10 * np.sin(np.pi * x / length),
                   left=Dirichlet(20), right=Dirichlet(20), save_every=200)
    exact = 20 + 10 * np.sin(np.pi * x / length) * np.exp(
        -material.alpha * (np.pi / length)**2 * end)
    error = float(np.max(np.abs(result.temperature[-1] - exact)))
    metadata = dict(case="Benchmark seno, no predicción de Freirina", k_W_mK=material.k,
                    rho_kg_m3=material.rho, cp_J_kgK=material.cp, alpha_m2_s=material.alpha,
                    length_m=length, nx=nx, dx_m=dx, dt_s=result.dt,
                    steps=result.steps, fourier=result.fourier, time_s=end,
                    left="Dirichlet 20 °C", right="Dirichlet 20 °C", q_dot_W_m3=0,
                    initial="20 + 10*sin(pi*x/L) °C", error_Linf_C=error)
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    (args.output / "diffusion_1d.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    np.savez_compressed(args.output / "diffusion_1d.npz", x=result.x,
                        times=result.times, temperature=result.temperature, exact_final=exact)
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for index in np.unique(np.linspace(0, len(result.times)-1, 5, dtype=int)):
        axes[0].plot(x, result.temperature[index], label=f"{result.times[index]/3600:.1f} h")
    axes[0].plot(x[::4], exact[::4], "k.", label="exacta final")
    axes[0].set(xlabel="x [m]", ylabel="T [°C]", title="Perfiles inicial, intermedios y final")
    axes[1].plot(result.times/3600, result.temperature[:, nx//2], label="centro")
    axes[1].plot(result.times/3600, result.temperature[:, 0], label="extremos")
    axes[1].set(xlabel="tiempo [h]", ylabel="T [°C]", title=f"Fo={result.fourier:.4f}; error final={error:.2e} °C")
    for ax in axes:
        ax.legend()
        ax.grid(alpha=.3)
    figure.suptitle("Verificación numérica 1D · L=1 m · Dirichlet 20 °C · sin fuente")
    figure.tight_layout()
    figure.savefig(args.output / "diffusion_1d.png", dpi=160)
    plt.close(figure)


if __name__ == "__main__":
    main()
