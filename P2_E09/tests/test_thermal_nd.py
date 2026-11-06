"""Verificación física independiente: analíticas, energía, fronteras y contacto."""
import numpy as np
import pytest
from numpy.testing import assert_allclose

from mcoc_p2 import (Material, Dirichlet, Neumann, Robin, CartesianGrid,
                     CartesianSystem, CellMaterial, solve_nd)

M = Material(2., 2400., 900.)


def box(dim, n=8, boundaries=None, material=M):
    return CartesianSystem(CartesianGrid((1.,) * dim, (n,) * dim), material, boundaries)


@pytest.mark.parametrize("dim", [2, 3])
def test_uniform_adiabatic_and_linear_source(dim):
    s = box(dim)
    for q in (0., 1500.):
        r = solve_nd(system=s, initial=20., dt=.7*s.stable_dt, t_end=12345., q_dot=q)
        exact = 20 + r.times * q / (2400*900)
        assert_allclose(r.temperature, np.broadcast_to(exact.reshape((-1,) + (1,)*dim),
                                                      r.temperature.shape), atol=2e-13)


@pytest.mark.parametrize("dim", [2, 3])
def test_heterogeneous_adiabatic_conserves_energy(dim):
    rng = np.random.default_rng(42)
    shape = (5,)*dim
    s = CartesianSystem(CartesianGrid((1.,)*dim, shape),
                        CellMaterial(rng.uniform(.5, 4., shape),
                                     rng.uniform(1800, 2500, shape),
                                     rng.uniform(700, 1100, shape)))
    r = solve_nd(system=s, initial=rng.uniform(10, 60, shape), dt=.8*s.stable_dt,
                 t_end=20000.)
    energy = np.array([s.energy(t) for t in r.temperature])
    assert_allclose(energy, energy[0], rtol=3e-15)


@pytest.mark.parametrize("face", ["x-", "x+", "y-", "y+", "z-", "z+"])
@pytest.mark.parametrize("flux", [-100., 100.])
def test_flux_sign_and_area_on_every_face(face, flux):
    # Caja de lados distintos: área de cada cara importa.
    grid = CartesianGrid((1., 2., 3.), (4, 5, 6))
    s = CartesianSystem(grid, M, {face: Neumann(flux)})
    r = solve_nd(system=s, initial=20., dt=.8*s.stable_dt, t_end=5000.)
    axis = "xyz".index(face[0])
    area = np.prod(grid.lengths) / grid.lengths[axis]
    assert_allclose(s.energy(r.temperature[-1], 20), -flux*area*5000,
                    rtol=1e-12, atol=1e-6)


@pytest.mark.parametrize("dim", [2, 3])
def test_mixed_boundaries_source_and_corners_balance(dim):
    boundaries = {"x-": Dirichlet(50), "x+": Robin(12, 5), "y-": Neumann(-20)}
    if dim == 3:
        boundaries.update({"z-": Robin(20, 10), "z+": Dirichlet(30)})
    s = box(dim, n=5, boundaries=boundaries)
    q = np.arange(5**dim).reshape(s.grid.shape)*3.
    r = solve_nd(system=s, initial=20, q_dot=q, dt=.7*s.stable_dt, t_end=10000.)
    for old, new in zip(r.temperature[:-1], r.temperature[1:]):
        outward = sum(np.sum(v) for v in s.boundary_heat_rates(old).values())
        expected = r.dt * (np.sum(q)*s.grid.cell_volume - outward)
        assert_allclose(s.energy(new)-s.energy(old), expected, rtol=2e-12, atol=1e-7)


@pytest.mark.parametrize("dim", [2, 3])
def test_robin_uses_surface_temperature_and_half_cell_resistance(dim):
    s = box(dim, boundaries={"x-": Robin(12, 20)})
    ts = s.face_temperature(50., "x-")
    q = s.boundary_heat_rates(50.)["x-"] / (s.grid.cell_volume/s.grid.spacing[0])
    assert_allclose(q, 12*(ts-20), rtol=2e-15)
    assert np.all((ts > 20) & (ts < 50))
    # h->infinito: misma resistencia de media celda que Dirichlet.
    a = box(dim, boundaries={"x-": Robin(1e15, 20)})
    b = box(dim, boundaries={"x-": Dirichlet(20)})
    assert_allclose(a.power(50), b.power(50), rtol=1e-12)


@pytest.mark.parametrize("ambient,initial", [(20., 50.), (50., 20.)])
def test_robin_cooling_heating_and_maximum_principle(ambient, initial):
    s = box(3, n=5, boundaries={"x-": Robin(20, ambient), "z+": Robin(50, ambient)})
    r = solve_nd(system=s, initial=initial, dt=s.stable_dt, t_end=50000.)
    assert r.temperature.min() >= min(ambient, initial)-1e-12
    assert r.temperature.max() <= max(ambient, initial)+1e-12
    assert (s.energy(r.temperature[-1])-s.energy(r.temperature[0]))*(ambient-initial) > 0


@pytest.mark.parametrize("dim", [2, 3])
def test_two_materials_exact_series_resistance_steady_state(dim):
    grid = CartesianGrid((1.,)*dim, (10,)+(4,)*(dim-1))
    x = grid.coordinates[0].reshape((-1,)+(1,)*(dim-1))
    k = np.where(x < .5, 1., 4.)
    s = CartesianSystem(grid, CellMaterial(k, 2400., 900.),
                        {"x-": Dirichlet(60), "x+": Dirichlet(20)})
    flux = (60-20)/(.5/1+.5/4)
    exact = np.broadcast_to(60-flux*np.where(x < .5, x, .5+(x-.5)/4), grid.shape)
    assert_allclose(s.power(exact), 0., atol=5e-12)
    assert_allclose(np.sum(s.boundary_heat_rates(exact)["x+"]), flux, rtol=1e-14)
    r = solve_nd(system=s, initial=exact, dt=.8*s.stable_dt, t_end=10000.)
    assert_allclose(r.temperature[-1], exact, rtol=0, atol=3e-13)


@pytest.mark.parametrize("dim", [2, 3])
def test_linear_neumann_robin_profile_and_dirichlet_faces(dim):
    s = box(dim, boundaries={"x-": Neumann(-20), "x+": Robin(5, 10)})
    x = s.grid.coordinates[0].reshape((-1,)+(1,)*(dim-1))
    exact = np.broadcast_to(14+10*(1-x), s.grid.shape)
    assert_allclose(s.power(exact), 0., atol=2e-12)
    assert_allclose(s.face_temperature(exact, "x+"), 14., atol=1e-14)
    d = box(dim, boundaries={"x-": Dirichlet(60)})
    assert_allclose(d.face_temperature(20., "x-"), 60., atol=1e-14)


@pytest.mark.parametrize("dim", [2, 3])
def test_sine_spatial_convergence_fixed_dt(dim):
    errors = []
    for n in (6, 12, 24):
        s = box(dim, n=n, boundaries={a+b: Dirichlet(20) for a in "xyz"[:dim] for b in "-+"})
        coordinates = np.meshgrid(*s.grid.coordinates, indexing="ij")
        mode = np.prod([np.sin(np.pi*x) for x in coordinates], axis=0)
        r = solve_nd(system=s, initial=20+10*mode, dt=5., t_end=10000., save_every=100000)
        exact = 20+10*mode*np.exp(-M.alpha*dim*np.pi**2*10000)
        errors.append(np.max(abs(r.temperature[-1]-exact)))
    ratios = np.array(errors[:-1])/errors[1:]
    assert np.all((ratios > 3.7) & (ratios < 4.5)), (errors, ratios)


@pytest.mark.parametrize("dim", [2, 3])
def test_temporal_convergence_against_semidiscrete_mode(dim):
    n = 6
    s = box(dim, n=n, boundaries={a+b: Dirichlet(20) for a in "xyz"[:dim] for b in "-+"})
    mode = np.prod([np.sin(np.pi*x) for x in np.meshgrid(*s.grid.coordinates, indexing="ij")], axis=0)
    rate = 4*M.alpha*n*n*dim*np.sin(np.pi/(2*n))**2
    end = 50000.
    exact = 20+10*mode*np.exp(-rate*end)
    errors = []
    for dt in (500., 250., 125.):
        r = solve_nd(system=s, initial=20+10*mode, dt=dt, t_end=end, save_every=100000)
        errors.append(np.max(abs(r.temperature[-1]-exact)))
    assert np.all((np.array(errors[:-1])/errors[1:] > 1.98)
                  & (np.array(errors[:-1])/errors[1:] < 2.05))


@pytest.mark.parametrize("dim", [2, 3])
def test_neumann_cosine_exact_mode(dim):
    n = 12
    s = box(dim, n=n)
    x = s.grid.coordinates[0].reshape((-1,)+(1,)*(dim-1))
    mode = np.broadcast_to(np.cos(np.pi*x), s.grid.shape)
    r = solve_nd(system=s, initial=20+10*mode, dt=50., t_end=10000., save_every=100000)
    exact = 20+10*mode*np.exp(-M.alpha*np.pi**2*10000)
    assert np.max(abs(r.temperature[-1]-exact)) < .006


def test_anisotropic_stability_limit_and_rejection():
    grid = CartesianGrid((1., 2., 3.), (8, 6, 4))
    s = CartesianSystem(grid, M)
    expected = .5 / (M.alpha*sum(1/d**2 for d in grid.spacing))
    assert_allclose(s.stable_dt, expected, rtol=1e-14)
    with pytest.raises(ValueError, match="cota"):
        solve_nd(system=s, initial=20, dt=1.01*s.stable_dt, t_end=1.)
    # Cara Dirichlet está a dx/2: cambia la cota en celdas de borde.
    d = CartesianSystem(grid, M, {"x-": Dirichlet(20)})
    assert d.stable_dt < s.stable_dt


def test_initial_centers_final_time_no_mutation_and_zero_h():
    s = box(2, boundaries={"x-": Dirichlet(50)})
    initial = np.full(s.grid.shape, 20.)
    r = solve_nd(system=s, initial=initial, dt=100., t_end=251., save_every=2)
    assert r.steps == 3 and r.times[-1] == 251. and len(r.times) == 3
    assert_allclose(initial, 20., rtol=0, atol=0)
    assert_allclose(r.temperature[0], 20., rtol=0, atol=0)
    z = solve_nd(system=s, initial=20., dt=100., t_end=0.)
    assert z.steps == z.dt == 0 and z.temperature.shape == (1, 8, 8)
    a, b = box(2), box(2, boundaries={"x-": Robin(0, 99)})
    assert_allclose(a.power(np.arange(64).reshape((8, 8))),
                    b.power(np.arange(64).reshape((8, 8))), rtol=0, atol=0)


@pytest.mark.parametrize("lengths,shape", [((1,), (1,)), ((0,1), (2,2)),
    ((1,1), (True,2)), ((1,), (2,2)), ((1,1,1,1), (2,2,2,2)), ((np.inf,), (2,))])
def test_grid_rejects_invalid_inputs(lengths, shape):
    with pytest.raises(ValueError):
        CartesianGrid(lengths, shape)


@pytest.mark.parametrize("field,value", [("k", 0), ("rho", -1), ("cp", np.inf),
                                         ("k", [1,2,3]), ("cp", 2+3j)])
def test_material_fields_rejected(field, value):
    props = dict(k=2., rho=2400., cp=900.)
    props[field] = value
    with pytest.raises(ValueError):
        box(2, material=CellMaterial(**props))


@pytest.mark.parametrize("kwargs", [{"dt": 0}, {"dt": np.nan}, {"t_end": -1},
    {"initial": np.nan}, {"initial": np.ones((3,3))}, {"q_dot": 1+2j},
    {"save_every": True}, {"save_every": 0}])
def test_solver_rejects_invalid_inputs(kwargs):
    args = dict(system=box(2), initial=20, dt=50, t_end=100)
    args.update(kwargs)
    with pytest.raises(ValueError):
        solve_nd(**args)


def test_unknown_faces_and_boundary_types():
    with pytest.raises(ValueError, match="Caras"):
        box(2, boundaries={"z-": Neumann()})
    with pytest.raises(TypeError, match="frontera"):
        box(2, boundaries={"x+": "adiabatico"})


@pytest.mark.parametrize("dim", [2, 3])
def test_robin_eigenmode_spatial_refinement(dim):
    mu = np.pi/4
    errors = []
    for n in (8,16):
        s = box(dim, n=n, boundaries={"x+": Robin(M.k*mu*np.tan(mu),20.)})
        x = s.grid.coordinates[0].reshape((-1,)+(1,)*(dim-1))
        mode = np.broadcast_to(np.cos(mu*x), s.grid.shape)
        # Se permite difundir la perturbación de borde antes de medir el orden.
        r = solve_nd(system=s, initial=20+10*mode, dt=5., t_end=50000., save_every=100000)
        exact = 20+10*mode*np.exp(-M.alpha*mu**2*50000)
        errors.append(np.max(abs(r.temperature[-1]-exact)))
    assert 3.5 < errors[0]/errors[1] < 4.5, errors


def test_demo_cli_accepts_3d_and_rejects_instability(tmp_path):
    from pathlib import Path
    import subprocess
    import sys
    import json
    root = Path(__file__).resolve().parents[1]
    command = [sys.executable, "-X", "utf8", str(root/"examples/run_e04.py"),
               "--dim", "3", "--case", "source", "--n", "4", "--t-end", "100",
               "--output", str(tmp_path/"demo")]
    good = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    assert good.returncode == 0, good.stderr
    report = json.loads((tmp_path/"demo/summary.json").read_text(encoding="utf-8"))
    assert report["error_Linf_C"] < 1e-12
    assert (tmp_path/"demo/temperature.png").is_file()
    bad = subprocess.run(command+["--dt", "1e20"], capture_output=True, text=True, encoding="utf-8")
    assert bad.returncode == 2 and "cota" in bad.stderr
