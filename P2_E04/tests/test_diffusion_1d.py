"""Balances exactos: tolerancias de redondeo; PDE: error y refinamiento."""

import numpy as np
import pytest
from numpy.testing import assert_allclose

from mcoc_p2 import (
    Dirichlet, Material, Neumann, Robin, energy_per_area, solve, stable_timestep,
)

CONCRETE = Material(k=2.0, rho=2400.0, cp=900.0)


def run(**changes):
    parameters = dict(material=CONCRETE, length=1., nx=21, dt=300.,
                      t_end=3600., initial=20.)
    parameters.update(changes)
    return solve(**parameters)


def test_uniform_adiabatic_remains_constant():
    assert_allclose(run().temperature, 20., rtol=0, atol=1e-13)


def test_dirichlet_overrides_initial_and_stays_fixed():
    result = run(left=Dirichlet(10.), right=Dirichlet(30.))
    assert_allclose(result.temperature[:, 0], 10., rtol=0, atol=0)
    assert_allclose(result.temperature[:, -1], 30., rtol=0, atol=0)
    assert result.temperature.min() >= 10.
    assert result.temperature.max() <= 30.


def test_nonuniform_adiabatic_conserves_weighted_energy():
    initial = np.random.default_rng(42).uniform(10, 70, 21)
    result = run(initial=initial, t_end=36000.)
    energy = energy_per_area(result.temperature, CONCRETE, .05)
    # Error relativo cercano al redondeo incluso tras 120 pasos.
    assert_allclose(energy, energy[0], rtol=3e-14, atol=1e-7)
    assert np.ptp(result.temperature[-1]) < np.ptp(initial)


def test_uniform_source_adiabatic_matches_exact_rise():
    result = run(q_dot=1200., t_end=3700.)
    expected = 20. + result.times * 1200. / (2400 * 900)
    assert_allclose(result.temperature, np.broadcast_to(expected[:, None],
                    result.temperature.shape), rtol=0, atol=2e-13)


def test_spatial_source_energy_integral():
    source = np.linspace(0, 2000, 21)
    result = run(q_dot=source)
    energy = energy_per_area(result.temperature, CONCRETE, .05, reference=20.)
    assert_allclose(energy, 1000 * result.times, rtol=2e-13, atol=1e-7)


@pytest.mark.parametrize("side", ["left", "right"])
@pytest.mark.parametrize("flux", [-100., 100.])
def test_neumann_sign_and_energy_on_either_face(side, flux):
    result = run(**{side: Neumann(flux)})
    energy = energy_per_area(result.temperature, CONCRETE, .05, reference=20.)
    assert_allclose(energy, -flux * result.times, rtol=2e-13, atol=1e-7)


def test_neumann_steady_linear_profile():
    # T=20+10*x -> q_out,left=+k*10 y q_out,right=-k*10.
    initial = np.linspace(20, 30, 21)
    result = run(initial=initial, left=Neumann(20), right=Neumann(-20))
    assert_allclose(result.temperature, np.broadcast_to(initial,
                    result.temperature.shape), rtol=0, atol=1e-13)


def test_robin_energy_balance_each_step_and_cooling():
    result = run(initial=50., left=Robin(12., 20.), right=Robin(6., 10.))
    energy = energy_per_area(result.temperature, CONCRETE, .05)
    outward = (12 * (result.temperature[:-1, 0] - 20)
               + 6 * (result.temperature[:-1, -1] - 10))
    assert_allclose(np.diff(energy), -result.dt * outward, rtol=2e-12, atol=1e-7)
    assert result.temperature.min() >= 10.
    assert result.temperature.max() <= 50.
    assert result.temperature[-1, 0] < result.temperature[-1, 10]


def test_robin_zero_h_is_adiabatic():
    initial = np.linspace(10, 50, 21)
    a = run(initial=initial)
    b = run(initial=initial, left=Robin(0., -50.), right=Robin(0., 100.))
    assert_allclose(a.temperature, b.temperature, rtol=0, atol=0)


def test_robin_steady_linear_profile():
    # Flujo saliente izquierdo +20, derecho -20 W/m².
    initial = np.linspace(20, 30, 21)
    result = run(initial=initial, left=Robin(2., 10.), right=Robin(2., 40.))
    assert_allclose(result.temperature, np.broadcast_to(initial,
                    result.temperature.shape), rtol=0, atol=1e-13)


def test_reject_diffusion_instability_and_accept_limit():
    limit = stable_timestep(CONCRETE, .05, Neumann(), Neumann())
    with pytest.raises(ValueError, match="cota"):
        run(dt=limit * 1.001)
    result = run(dt=limit, t_end=limit)
    assert_allclose(result.fourier, .5)


@pytest.mark.parametrize("side", ["left", "right"])
def test_robin_can_be_unstable_even_if_fourier_less_than_half(side):
    boundary = Robin(100., 20.)
    pure_limit = .05**2 / (2 * CONCRETE.alpha)
    convection_limit = pure_limit / (1 + 100 * .05 / 2)
    assert stable_timestep(CONCRETE, .05, boundary, Neumann()) == convection_limit
    with pytest.raises(ValueError, match="Robin"):
        run(dt=.9 * pure_limit, **{side: boundary})
    run(dt=convection_limit, **{side: boundary})


def test_material_units_and_derived_diffusivity():
    assert_allclose(CONCRETE.alpha, 9.259259259259259e-7, rtol=1e-15)
    # Mismo alpha y distinta capacidad: misma difusión pero mitad del alza por fuente.
    a = run(q_dot=1000.)
    b = run(material=Material(4., 4800., 900.), q_dot=1000.)
    assert_allclose(b.temperature - 20, (a.temperature - 20) / 2, atol=2e-13)


@pytest.mark.parametrize("name", ["k", "rho", "cp"])
@pytest.mark.parametrize("value", [0., -1., np.nan, np.inf])
def test_invalid_material(name, value):
    parameters = dict(k=2., rho=2400., cp=900.)
    parameters[name] = value
    with pytest.raises(ValueError):
        Material(**parameters)


@pytest.mark.parametrize("changes", [
    {"length": 0}, {"length": np.inf}, {"nx": 2}, {"nx": 20.5}, {"nx": True},
    {"dt": 0}, {"dt": np.nan}, {"t_end": -1}, {"t_end": np.inf},
    {"initial": [20, 30]}, {"initial": np.nan}, {"q_dot": np.inf},
    {"q_dot": np.ones((21, 1))}, {"save_every": 0}, {"save_every": 1.5},
])
def test_invalid_solver_inputs(changes):
    with pytest.raises(ValueError):
        run(**changes)


@pytest.mark.parametrize("factory", [lambda: Robin(-1, 20), lambda: Robin(1, np.nan),
                                    lambda: Dirichlet(np.inf), lambda: Neumann(np.nan)])
def test_invalid_boundaries(factory):
    with pytest.raises(ValueError):
        factory()


def test_unknown_boundary_rejected():
    with pytest.raises(TypeError):
        run(left="adiabatic")


def test_energy_accepts_integer_dx_and_counts_half_cells():
    # Dos metros de dominio; un Kelvin uniforme: E/A=rho*cp*2 m.
    result = energy_per_area([21, 21, 21], CONCRETE, dx=1, reference=20)
    assert_allclose(result, 2400 * 900 * 2, rtol=0, atol=0)


@pytest.mark.parametrize("field", ["initial", "q_dot"])
def test_complex_fields_rejected_without_losing_imaginary_part(field):
    with pytest.raises(ValueError, match="reales"):
        run(**{field: np.full(21, 20 + 2j)})


def test_complex_energy_profile_rejected():
    with pytest.raises(ValueError, match="reales"):
        energy_per_area(np.array([20+1j]*3), CONCRETE, dx=1)


@pytest.mark.parametrize("temperature", [20., [20, 20], [20, np.nan, 20]])
def test_energy_rejects_invalid_profiles(temperature):
    with pytest.raises(ValueError):
        energy_per_area(temperature, CONCRETE, dx=1)


def test_robin_heating_sign_and_maximum_principle():
    result = run(initial=10., left=Robin(12., 30.), right=Robin(6., 40.))
    energy = energy_per_area(result.temperature, CONCRETE, .05)
    assert np.all(np.diff(energy) > 0)
    assert result.temperature.min() >= 10.
    assert result.temperature.max() <= 40.
    assert result.temperature[-1, 0] > result.temperature[-1, 10]


def test_temporal_first_order_on_fixed_mesh_against_semidiscrete_exact_solution():
    # La solución del sistema espacial discretizado elimina el error espacial.
    nx = 21
    x = np.linspace(0, 1, nx)
    dx = x[1]
    rate = 4 * CONCRETE.alpha / dx**2 * np.sin(np.pi/(2*(nx-1)))**2
    end = 100000.
    exact = 20 + 10 * np.sin(np.pi*x) * np.exp(-rate*end)
    errors = []
    for steps in (100, 200, 400, 800):
        result = run(nx=nx, dt=end/steps, t_end=end, initial=20+10*np.sin(np.pi*x),
                     left=Dirichlet(20), right=Dirichlet(20), save_every=10000)
        errors.append(np.max(np.abs(result.temperature[-1]-exact)))
    ratios = np.array(errors[:-1]) / errors[1:]
    assert np.all((ratios > 1.98) & (ratios < 2.03))


def test_spatial_second_order_with_fixed_small_temporal_error():
    # dt fijo pequeño: el error espacial domina en las tres mallas.
    errors = []
    for nx in (11, 21, 41):
        x = np.linspace(0, 1, nx)
        result = run(nx=nx, dt=1., t_end=10000., initial=20+10*np.sin(np.pi*x),
                     left=Dirichlet(20), right=Dirichlet(20), save_every=10000)
        exact = 20+10*np.sin(np.pi*x)*np.exp(-CONCRETE.alpha*np.pi**2*10000)
        errors.append(np.max(np.abs(result.temperature[-1]-exact)))
    ratios = np.array(errors[:-1])/errors[1:]
    assert np.all((ratios > 3.9) & (ratios < 4.2))


def test_exact_final_time_snapshots_and_no_input_mutation():
    initial = np.linspace(10, 30, 21)
    original = initial.copy()
    result = run(initial=initial, t_end=1001., save_every=3)
    assert result.times[-1] == 1001.
    assert result.dt <= 300.
    assert result.steps == 4
    assert len(result.times) == 3  # inicio, paso 3 y final
    assert_allclose(initial, original, atol=0, rtol=0)
    zero = run(t_end=0.)
    assert zero.temperature.shape == (1, 21)
    assert zero.dt == zero.fourier == zero.steps == 0


def test_sine_exact_solution_and_second_order_refinement():
    errors = []
    for nx in (21, 41, 81):
        x = np.linspace(0, 1, nx)
        dx = x[1]
        result = run(nx=nx, dt=.3 * dx**2 / CONCRETE.alpha,
                     t_end=100000., initial=20 + 10 * np.sin(np.pi * x),
                     left=Dirichlet(20), right=Dirichlet(20), save_every=100000)
        exact = 20 + 10 * np.sin(np.pi * x) * np.exp(-CONCRETE.alpha * np.pi**2 * 100000)
        errors.append(np.max(np.abs(result.temperature[-1] - exact)))
    # dt ~ dx²: error global O(dt + dx²); cada refinamiento reduce ~4 veces.
    assert errors[-1] < .001
    assert np.all(np.array(errors[:-1]) / errors[1:] > 3.8)


def test_robin_exact_eigenmode_and_refinement():
    # theta=cos(mu*x)*exp(-alpha*mu²*t), izquierda aislada.
    # -k*theta_x(1)=h*theta(1) si h=k*mu*tan(mu).
    mu = np.pi / 4
    errors = []
    for nx in (21, 41, 81):
        x = np.linspace(0, 1, nx)
        right = Robin(CONCRETE.k * mu * np.tan(mu), 20.)
        dt = .6 * stable_timestep(CONCRETE, x[1], Neumann(), right)
        result = run(nx=nx, dt=dt, t_end=100000., initial=20 + 10 * np.cos(mu * x),
                     right=right, save_every=100000)
        exact = 20 + 10 * np.cos(mu * x) * np.exp(-CONCRETE.alpha * mu**2 * 100000)
        errors.append(np.max(np.abs(result.temperature[-1] - exact)))
    assert errors[-1] < .001
    assert np.all(np.array(errors[:-1]) / errors[1:] > 3.7)
