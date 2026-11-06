"""Demo E04 de caja ideal: no predice la temperatura real de la fundación."""
import argparse
import json
from pathlib import Path
import platform

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from mcoc_p2 import (Material, CellMaterial, CartesianGrid, CartesianSystem,
                     Dirichlet, Neumann, Robin, solve_nd)


def case_system(dim, n, case, h=12., q_dot=1000.):
    grid = CartesianGrid((1.,)*dim, (n,)*dim)
    material = Material(2., 2400., 900.)
    boundaries, initial, source = {}, 20., 0.
    if case == "sine":
        boundaries = {axis+side: Dirichlet(20) for axis in "xyz"[:dim] for side in "-+"}
        mode = np.prod([np.sin(np.pi*x) for x in np.meshgrid(*grid.coordinates, indexing="ij")], axis=0)
        initial = 20+10*mode
    elif case == "source":
        source = q_dot
    elif case == "robin":
        boundaries = {axis+side: Robin(h, 20.) for axis in "xyz"[:dim] for side in "-+"}
        initial = 50.
    elif case == "flux":
        boundaries = {"x+": Neumann(100.)}
    elif case == "two-materials":
        x = grid.coordinates[0].reshape((-1,)+(1,)*(dim-1))
        if n % 2:
            raise ValueError("two-materials requiere n par: interfaz x=0,5 m en una cara")
        material = CellMaterial(np.where(x < .5, 1., 4.), 2400., 900.)
        boundaries = {"x-": Dirichlet(60.), "x+": Dirichlet(20.)}
        initial = np.broadcast_to(60-64*np.where(x < .5, x, .5+(x-.5)/4), grid.shape).copy()
    else:
        raise ValueError(f"Caso desconocido: {case}")
    return CartesianSystem(grid, material, boundaries), initial, source


def run_case(dim=3, n=16, case="sine", dt=None, t_end=21600., h=12., q_dot=1000.):
    s, initial, source = case_system(dim, n, case, h, q_dot)
    requested_dt = .8*s.stable_dt if dt is None else dt
    save_every = max(1, int(t_end/requested_dt)//40) if requested_dt > 0 else 1
    r = solve_nd(system=s, initial=initial, q_dot=source, dt=requested_dt,
                 t_end=t_end, save_every=save_every)
    exact = None
    if case == "sine":
        exact = 20+(initial-20)*np.exp(-2/(2400*900)*dim*np.pi**2*t_end)
    elif case == "source":
        exact = np.full(s.grid.shape, 20+source*t_end/(2400*900))
    elif case == "two-materials":
        exact = initial.copy()
    energies = np.array([s.energy(t, reference=20.) for t in r.temperature])
    report = {
        "scope": "Caja ideal E04, independiente del IFC; sin hidratacion ni clima real",
        "case": case, "dimensions": dim, "shape": s.grid.shape,
        "lengths_m": s.grid.lengths, "spacing_m": s.grid.spacing,
        "temperature_location": "cell_centers", "requested_dt_s": requested_dt,
        "effective_dt_s": r.dt, "stable_dt_s": s.stable_dt, "steps": r.steps,
        "t_end_s": t_end, "q_dot_W_m3": float(source),
        "boundaries": {name: {"type": type(b).__name__, **vars(b)} for name,b in s.boundaries.items()},
        "material": {"k_min_W_mK": float(s.k.min()), "k_max_W_mK": float(s.k.max()),
                     "rho_kg_m3": 2400., "cp_J_kgK": 900.},
        "initial_min_C": float(r.temperature[0].min()),
        "initial_max_C": float(r.temperature[0].max()),
        "final_min_C": float(r.temperature[-1].min()),
        "final_max_C": float(r.temperature[-1].max()),
        "energy_change_J": float(energies[-1]-energies[0]),
        "error_Linf_C": None if exact is None else float(np.max(abs(r.temperature[-1]-exact))),
        "python": platform.python_version(), "numpy": np.__version__,
    }
    if case in ("source", "flux"):
        expected = (source*np.prod(s.grid.lengths) if case == "source" else -100.)*t_end
        report["expected_energy_change_J"] = float(expected)
        report["energy_error_J"] = float(energies[-1]-energies[0]-expected)
    return report, s, r, exact, energies


def plot_case(report, s, r, output):
    dim = report["dimensions"]
    final = r.temperature[-1]
    fig, axes = plt.subplots(2, 2, figsize=(10, 8), layout="constrained")
    low, high = float(final.min()), float(final.max())
    if high-low < 1e-8:
        low, high = low-.5, high+.5
    if dim == 2:
        slices = [(r.temperature[0], (0,1), "Inicial"), (final, (0,1), "Final")]
        axes[1,0].plot(s.grid.coordinates[0], final[:, s.grid.shape[1]//2], label="numérica")
        axes[1,0].set(xlabel="x [m]", ylabel="T [°C]", title="Perfil por fila central")
        axes[1,0].grid(alpha=.25)
    else:
        mid = [n//2 for n in s.grid.shape]
        slices = [(final[:,:,mid[2]], (0,1), f"z={s.grid.coordinates[2][mid[2]]:.3f} m"),
                  (final[:,mid[1],:], (0,2), f"y={s.grid.coordinates[1][mid[1]]:.3f} m"),
                  (final[mid[0],:,:], (1,2), f"x={s.grid.coordinates[0][mid[0]]:.3f} m")]
    for ax, (field, (i,j), title) in zip(axes.flat, slices):
        # La fila/columna identifica centros, el extent muestra las caras del dominio.
        image = ax.imshow(field.T, origin="lower", extent=(0,1,0,1),
                          cmap="inferno", vmin=low if dim == 3 else None,
                          vmax=high if dim == 3 else None, aspect="equal")
        ax.set(xlabel="xyz"[i]+" [m]", ylabel="xyz"[j]+" [m]", title=title)
        fig.colorbar(image, ax=ax, label="T [°C]", shrink=.8)
    flat = r.temperature.reshape((len(r.times), -1))
    ax = axes[1,1]
    ax.plot(r.times/3600, flat.max(axis=1), label="máximo de centros")
    ax.plot(r.times/3600, flat.min(axis=1), label="mínimo de centros")
    center = (slice(None),) + tuple(n//2 for n in s.grid.shape)
    ax.plot(r.times/3600, r.temperature[center], "--", label="celda central")
    ax.set(xlabel="tiempo [h]", ylabel="T [°C]", title="Historia térmica")
    ax.legend(fontsize=8)
    ax.grid(alpha=.25)
    fig.suptitle(f"E04 · {dim}D · {report['case']} · caja ideal de 1 m\n"
                 f"dt={r.dt:.2f} s · {r.steps} pasos · sin conexión IFC")
    fig.savefig(output, dpi=150)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dim", type=int, choices=(2,3), default=3)
    p.add_argument("--n", type=int, default=16, help="celdas por eje; dx=1/n m")
    p.add_argument("--case", choices=("sine","source","robin","flux","two-materials"), default="sine")
    p.add_argument("--dt", type=float, default=None, help="segundos; por defecto 0,8*cota local")
    p.add_argument("--t-end", type=float, default=21600.)
    p.add_argument("--h", type=float, default=12., help="W/(m² K), caso robin")
    p.add_argument("--q-dot", type=float, default=1000., help="W/m³, caso source")
    p.add_argument("--output", type=Path)
    a = p.parse_args()
    try:
        report, s, r, exact, energy = run_case(a.dim, a.n, a.case, a.dt, a.t_end, a.h, a.q_dot)
    except (ValueError, TypeError, FloatingPointError, OverflowError) as exc:
        p.exit(2, f"ERROR: {exc}\n")
    output = a.output or Path(f"results/e04/{a.case}_{a.dim}d")
    output.mkdir(parents=True, exist_ok=True)
    (output/"summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    fields = dict(times_s=r.times, temperature_C=r.temperature, energy_J=energy)
    fields.update({axis+"_m": values for axis,values in zip("xyz", s.grid.coordinates)})
    if exact is not None:
        fields["exact_final_C"] = exact
    np.savez_compressed(output/"solution.npz", **fields)
    plot_case(report, s, r, output/"temperature.png")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
