"""Demo parametrizable del mismo benchmark físico E01; sin conexión IFC."""
import argparse
import json
from pathlib import Path
import numpy as np
from mcoc_p2 import Material, Dirichlet, solve, stable_timestep


def run_case(nx=81, dt=67.5, t_end=86400.):
    material = Material(2., 2400., 900.)
    if nx < 3:
        raise ValueError('nx debe ser >= 3')
    dx = 1. / (nx-1)
    x = np.linspace(0., 1., nx)
    result = solve(material=material, length=1., nx=nx, dt=dt, t_end=t_end,
                   initial=20+10*np.sin(np.pi*x), left=Dirichlet(20),
                   right=Dirichlet(20), save_every=max(1, int(t_end/dt)//20) if dt > 0 else 1)
    exact = 20+10*np.sin(np.pi*x)*np.exp(-material.alpha*np.pi**2*t_end)
    # Referencia semidiscreta: separa error temporal de error espacial.
    rate_h = 4*material.alpha/dx**2*np.sin(np.pi/(2*(nx-1)))**2
    semidiscrete = 20+10*np.sin(np.pi*x)*np.exp(-rate_h*t_end)
    report = dict(nx=nx, dx_m=dx, requested_dt_s=dt, effective_dt_s=result.dt,
                  stable_dt_s=stable_timestep(material, dx, Dirichlet(20), Dirichlet(20)),
                  fourier=result.fourier, steps=result.steps, t_end_s=float(result.times[-1]),
                  initial_max_C=float(result.temperature[0].max()),
                  final_min_C=float(result.temperature[-1].min()),
                  final_max_C=float(result.temperature[-1].max()),
                  final_center_C=float(result.temperature[-1, nx//2]),
                  error_exact_C=float(np.max(np.abs(result.temperature[-1]-exact))),
                  error_temporal_semidiscrete_C=float(np.max(np.abs(result.temperature[-1]-semidiscrete))))
    return report, result, exact


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--nx', type=int, default=81)
    p.add_argument('--dt', type=float, default=67.5)
    p.add_argument('--t-end', type=float, default=86400.)
    p.add_argument('--output', type=Path, default=Path('results/e02/demo'))
    a = p.parse_args()
    try:
        report, result, exact = run_case(a.nx, a.dt, a.t_end)
    except (ValueError, FloatingPointError, OverflowError) as exc:
        p.exit(2, f'ERROR: {exc}\n')
    a.output.mkdir(parents=True, exist_ok=True)
    (a.output/'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    np.savez_compressed(a.output/'solution.npz', x=result.x, times=result.times,
                        temperature=result.temperature, exact_final=exact)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
