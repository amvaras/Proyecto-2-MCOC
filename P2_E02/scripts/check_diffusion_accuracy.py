"""Audita error espacial, temporal y datos del benchmark mediante modos exactos."""

import argparse
import json
from pathlib import Path

import numpy as np

from mcoc_p2 import Dirichlet, Material, solve


def check_accuracy(benchmark_directory: Path) -> dict:
    material = Material(2., 2400., 900.)
    spatial = []
    for nx in (11, 21, 41):
        x = np.linspace(0, 1, nx)
        result = solve(material=material, length=1., nx=nx, dt=1., t_end=10000.,
                       initial=20+10*np.sin(np.pi*x), left=Dirichlet(20),
                       right=Dirichlet(20), save_every=10000)
        exact = 20+10*np.sin(np.pi*x)*np.exp(-material.alpha*np.pi**2*10000.)
        spatial.append(dict(nx=nx, dx_m=float(x[1]), dt_s=result.dt,
                            error_Linf_C=float(np.max(np.abs(result.temperature[-1]-exact)))))
    temporal = []
    nx, end = 21, 100000.
    x = np.linspace(0, 1, nx)
    rate = 4 * material.alpha / x[1]**2 * np.sin(np.pi/(2*(nx-1)))**2
    semidiscrete = 20+10*np.sin(np.pi*x)*np.exp(-rate*end)
    for steps in (100, 200, 400, 800):
        result = solve(material=material, length=1., nx=nx, dt=end/steps, t_end=end,
                       initial=20+10*np.sin(np.pi*x), left=Dirichlet(20),
                       right=Dirichlet(20), save_every=10000)
        temporal.append(dict(nx=nx, dt_s=result.dt, steps=result.steps,
                             error_Linf_C=float(np.max(np.abs(result.temperature[-1]-semidiscrete)))))
    spatial_ratios = [a["error_Linf_C"]/b["error_Linf_C"] for a, b in zip(spatial, spatial[1:])]
    temporal_ratios = [a["error_Linf_C"]/b["error_Linf_C"] for a, b in zip(temporal, temporal[1:])]
    if not all(3.9 < ratio < 4.2 for ratio in spatial_ratios):
        raise ValueError("No se verifica segundo orden espacial")
    if not all(1.98 < ratio < 2.03 for ratio in temporal_ratios):
        raise ValueError("No se verifica primer orden temporal")
    # Recalcula analitica y error desde NPZ, independientemente de los metadatos.
    metadata = json.loads((benchmark_directory / "diffusion_1d.json").read_text(encoding="utf-8"))
    with np.load(benchmark_directory / "diffusion_1d.npz") as data:
        x, times, temperature = data["x"], data["times"], data["temperature"]
        exact = 20+10*np.sin(np.pi*x)*np.exp(-material.alpha*np.pi**2*times[-1])
        error = float(np.max(np.abs(temperature[-1]-exact)))
        if not (np.allclose(data["exact_final"], exact, rtol=0, atol=1e-13)
                and np.allclose(temperature[0], 20+10*np.sin(np.pi*x), rtol=0, atol=1e-13)
                and np.all(temperature[:, [0, -1]] == 20.)
                and np.all(np.diff(times) > 0)
                and times[-1] == metadata["time_s"] == 86400.
                and metadata["steps"] == 1280
                and np.isclose(material.alpha*metadata["dt_s"]/(x[1]-x[0])**2,
                               metadata["fourier"], rtol=1e-14)
                and np.isclose(error, metadata["error_Linf_C"], rtol=1e-12, atol=1e-14)):
            raise ValueError("Datos, analitica y parametros del benchmark no coinciden")
    return dict(spatial=spatial, spatial_error_ratios=spatial_ratios,
                temporal=temporal, temporal_error_ratios=temporal_ratios,
                temporal_reference="Solucion exacta del sistema espacial semidiscreto, malla fija",
                benchmark_data_consistent=True, benchmark_error_Linf_C=error)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path, default=Path("results"))
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    report = check_accuracy(args.benchmark)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
