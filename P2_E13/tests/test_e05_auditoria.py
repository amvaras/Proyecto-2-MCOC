"""Auditoría E05: referencias continuas independientes para perfiles de borde.

Complementa la batería original sin modificar su solver ni sus tolerancias.
Las referencias se calculan desde la PDE, no desde power/boundary_heat_rates.
"""
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
from numpy.testing import assert_allclose

from mcoc_p2 import CartesianGrid, CartesianSystem, Material, Neumann, Robin, solve_nd

pytestmark = pytest.mark.e05
ROOT = Path(__file__).resolve().parents[1]
AXES = [(dim, axis) for dim in (1, 2, 3) for axis in range(dim)]
MATERIAL = Material(2.7, 2310., 870.)


def axis_box(dim, axis, n=24):
    lengths = tuple(.8 + .35*i for i in range(dim))
    shape = tuple(n if i == axis else 3+i for i in range(dim))
    grid = CartesianGrid(lengths, shape)
    reshape = [1]*dim
    reshape[axis] = n
    return grid, grid.coordinates[axis].reshape(reshape), lengths[axis]


@pytest.mark.parametrize("dim,axis", AXES)
@pytest.mark.parametrize("flux", [-73., 119.])
def test_neumann_nonzero_transient_profile_matches_continuous_solution(dim, axis, flux, record_property):
    """Flujo neto cero: un balance global NO basta para aprobar este perfil."""
    grid, x, length = axis_box(dim, axis)
    name = "xyz"[axis]
    system = CartesianSystem(grid, MATERIAL, {name+"-": Neumann(-flux), name+"+": Neumann(flux)})
    steady = 30. + flux/MATERIAL.k*(length/2-x)
    mode = np.cos(np.pi*x/length)
    initial = np.broadcast_to(steady + 6.*mode, grid.shape)
    end = .04*length**2/MATERIAL.alpha
    result = solve_nd(system=system, initial=initial, dt=.05*system.stable_dt,
                      t_end=end, save_every=1000000)
    exact = np.broadcast_to(steady + 6.*mode*np.exp(-MATERIAL.alpha*(np.pi/length)**2*end), grid.shape)
    error = float(np.max(np.abs(result.temperature[-1]-exact)))
    # Umbral previo: 0,05 % de la amplitud, sin escalarlo con el error observado.
    assert error < .003
    assert_allclose(system.energy(result.temperature[-1]), system.energy(initial), rtol=2e-14)
    assert np.max(np.abs(result.temperature[-1]-initial)) > 1.
    record_property("e05_audit_reference", json.dumps(dict(
        case="neumann_transient", dimension=dim, axis=name, flux_out_plus_W_m2=flux,
        shape=grid.shape, lengths_m=grid.lengths, t_end_s=end, dt_s=result.dt,
        error_Linf_C=error, tolerance_C=.003,
        reference="T0+q/k*(L/2-x)+A*cos(pi*x/L)*exp(-alpha*(pi/L)^2*t)")))


def robin_root(biot):
    """Primera raíz de mu*tan(mu)=Bi en (0, pi/2), por bisección escalar."""
    low, high = 0., math.pi/2
    for _ in range(80):
        middle = (low+high)/2
        if middle*math.tan(middle) < biot:
            low = middle
        else:
            high = middle
    return (low+high)/2


@pytest.mark.parametrize("dim,axis", AXES)
@pytest.mark.parametrize("side,biot,amplitude", [("+", .25, 8.), ("-", 3., -8.)])
def test_robin_eigenmode_for_changed_geometry_material_face_and_biot(dim, axis, side, biot, amplitude, record_property):
    """Comprueba el campo transiente, para enfriamiento y calentamiento."""
    grid, coordinate, length = axis_box(dim, axis)
    x = coordinate if side == "+" else length-coordinate
    mu = robin_root(biot)
    assert abs(mu*math.tan(mu)-biot) < 1e-13
    h = biot*MATERIAL.k/length
    system = CartesianSystem(grid, MATERIAL, {"xyz"[axis]+side: Robin(h, 19.)})
    mode = np.cos(mu*x/length)
    initial = np.broadcast_to(19. + amplitude*mode, grid.shape)
    end = .12*length**2/MATERIAL.alpha
    result = solve_nd(system=system, initial=initial, dt=.05*system.stable_dt,
                      t_end=end, save_every=1000000)
    exact = np.broadcast_to(19. + amplitude*mode*np.exp(-MATERIAL.alpha*(mu/length)**2*end), grid.shape)
    error = float(np.max(np.abs(result.temperature[-1]-exact)))
    # 0,125 % de la amplitud. La referencia depende de h y de la cara real.
    assert error < .01
    record_property("e05_audit_reference", json.dumps(dict(
        case="robin_transient", dimension=dim, face="xyz"[axis]+side, biot=biot,
        h_W_m2K=h, mu=mu, amplitude_C=amplitude, shape=grid.shape,
        lengths_m=grid.lengths, t_end_s=end, dt_s=result.dt,
        error_Linf_C=error, tolerance_C=.01,
        reference="Tamb+A*cos(mu*x/L)*exp(-alpha*(mu/L)^2*t); mu*tan(mu)=h*L/k")))


@pytest.mark.parametrize("dim", [1, 2, 3])
def test_robin_independent_reference_has_second_order_spatial_convergence(dim, record_property):
    errors = []
    # Paso pequeño y común: evita atribuir el error temporal a la malla.
    for n in (10, 20, 40):
        grid, x, length = axis_box(dim, dim-1, n)
        biot, amplitude = 1.3, 8.
        mu = robin_root(biot)
        system = CartesianSystem(grid, MATERIAL, {"xyz"[dim-1]+"+": Robin(biot*MATERIAL.k/length, 19.)})
        initial = np.broadcast_to(19. + amplitude*np.cos(mu*x/length), grid.shape)
        end = .12*length**2/MATERIAL.alpha
        # <= 0,04 de la cota interior de la malla fina, independiente de n.
        dt = .02*(length/40)**2/MATERIAL.alpha
        result = solve_nd(system=system, initial=initial, dt=dt, t_end=end, save_every=100000000)
        exact = 19. + amplitude*np.cos(mu*x/length)*np.exp(-MATERIAL.alpha*(mu/length)**2*end)
        errors.append(float(np.max(np.abs(result.temperature[-1]-exact))))
    orders = [math.log(a/b, 2) for a, b in zip(errors, errors[1:])]
    assert all(1.7 < order < 2.3 for order in orders), (errors, orders)
    record_property("e05_audit_reference", json.dumps(dict(
        case="robin_spatial", dimension=dim, n=[10,20,40], errors_Linf_C=errors,
        observed_orders=orders, expected_order=2., tolerance_order=.3)))


@pytest.mark.parametrize("dim", [1, 2, 3])
def test_live_exact_cli_uses_changed_parameters_and_saves_real_fields(dim, tmp_path):
    shape = [8+2*i for i in range(dim)]
    lengths = [1.1+.3*i for i in range(dim)]
    output = tmp_path/"exacta"
    args = [sys.executable, "-X", "utf8", "-B", str(ROOT/"examples/run_e05.py"),
            "--case", f"exact_{dim}d", "--shape", *map(str, shape),
            "--lengths", *map(str, lengths), "--k", "3.2", "--rho", "2250",
            "--cp", "950", "--initial", "17", "--amplitude", "7",
            "--dt", "20", "--t-end", "1600", "--output", str(output)]
    completed = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    assert completed.returncode == 0, completed.stdout+completed.stderr
    folder = output/f"exact_{dim}d"
    report = json.loads((folder/"summary.json").read_text(encoding="utf-8"))
    assert report["shape"] == shape and report["lengths_m"] == lengths
    assert report["config"]["k"] == 3.2 and report["effective_dt_s"] == 20.
    with np.load(folder/"solution.npz") as data:
        mode = np.ones(shape)
        for axis in range(dim):
            view = [1]*dim
            view[axis] = shape[axis]
            x = (np.arange(shape[axis])+.5)*lengths[axis]/shape[axis]
            assert_allclose(data["xyz"[axis]+"_m"], x)
            mode *= np.sin(np.pi*x/lengths[axis]).reshape(view)
        exact = 17. + 7.*mode*np.exp(-3.2/(2250*950)*sum((np.pi/L)**2 for L in lengths)*1600)
        assert_allclose(data["exact_final_C"], exact, rtol=0, atol=2e-14)
        assert np.max(np.abs(data["temperature_C"][-1]-exact)) < .03
        assert data["times_s"][-1] == 1600.
    assert (folder/"result.png").stat().st_size > 1000
