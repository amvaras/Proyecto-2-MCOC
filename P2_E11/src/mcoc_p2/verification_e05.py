"""Casos científicos configurables E05, sin sustituir el solver conservativo E04."""
from dataclasses import asdict, dataclass, fields
import json
import math
from numbers import Real
from pathlib import Path

import numpy as np

from .diffusion_1d import Material, Dirichlet, Neumann, Robin
from .thermal_nd import CartesianGrid, CartesianSystem, CellMaterial, solve_nd

CASES = {
    "exact_1d": "exact", "exact_2d": "exact", "exact_3d": "exact",
    "energy": "conservation", "source": "source", "neumann": "boundary",
    "robin": "boundary", "spatial": "convergence", "temporal": "convergence",
    "stability": "stability",
}
SI_UNITS = {"length": "m", "time": "s", "temperature": "degC", "k": "W/(m K)",
            "rho": "kg/m^3", "cp": "J/(kg K)", "q_dot": "W/m^3",
            "flux": "W/m^2", "h": "W/(m^2 K)"}


@dataclass(frozen=True)
class CaseConfig:
    dimension: int = 2
    n: int = 12
    shape: tuple | None = None
    lengths_m: object = 1.
    k: float = 2.
    rho: float = 2400.
    cp: float = 900.
    initial_C: float = 20.
    amplitude_C: float = 10.
    ambient_C: float = 10.
    h: float = 12.
    q_dot: float = 1000.
    flux: float = 100.
    face: str | None = None
    dt_s: float | None = None
    t_end_s: float = 10000.
    heterogeneous: bool = False
    atol_C: float = .03
    energy_rtol: float = 5e-12
    energy_atol_J: float = 1e-7

    def __post_init__(self):
        for name in ("dimension", "n"):
            value = getattr(self, name)
            minimum = 1 if name == "dimension" else 2
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < minimum:
                raise ValueError(f"{name} debe ser entero >= {minimum}")
        if self.dimension > 3:
            raise ValueError("dimension debe ser 1, 2 o 3")
        for name in ("k", "rho", "cp", "initial_C", "amplitude_C", "ambient_C", "h",
                     "q_dot", "flux", "t_end_s", "atol_C", "energy_rtol", "energy_atol_J"):
            value = getattr(self, name)
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real) or not math.isfinite(value):
                raise ValueError(f"{name} debe ser real finito")
        Material(self.k, self.rho, self.cp)
        if self.h < 0 or self.t_end_s <= 0 or min(self.atol_C, self.energy_rtol, self.energy_atol_J) < 0:
            raise ValueError("h y tolerancias no negativos; t_end_s estrictamente positivo")
        if self.dt_s is not None and (isinstance(self.dt_s, bool) or not isinstance(self.dt_s, Real)
                                      or not math.isfinite(self.dt_s) or self.dt_s <= 0):
            raise ValueError("dt_s debe ser real finito y positivo")
        if not isinstance(self.heterogeneous, bool):
            raise ValueError("heterogeneous debe ser booleano")
        shape = (self.n,)*self.dimension if self.shape is None else tuple(self.shape)
        lengths = self.lengths_m
        if isinstance(lengths, Real) and not isinstance(lengths, bool):
            lengths = (float(lengths),)*self.dimension
        else:
            lengths = tuple(lengths)
            if len(lengths) == 1:
                lengths = lengths*self.dimension
        if any(isinstance(v, bool) for v in lengths):
            raise ValueError("Longitudes no pueden ser booleanas")
        grid = CartesianGrid(lengths, shape)
        if math.prod(shape) > 262144:
            raise ValueError("Caso de laboratorio limitado a 262144 celdas")
        allowed = {a+b for a in "xyz"[:self.dimension] for b in "-+"}
        if self.face is not None and self.face not in allowed:
            raise ValueError(f"Cara {self.face!r} incompatible con dimension {self.dimension}")
        object.__setattr__(self, "shape", grid.shape)
        object.__setattr__(self, "lengths_m", grid.lengths)


def make_config(case, overrides=None):
    if case not in CASES:
        raise ValueError(f"Caso desconocido: {case}")
    values = dict(overrides or {})
    known = {field.name for field in fields(CaseConfig)}
    if values.keys()-known:
        raise ValueError(f"Parametros desconocidos: {sorted(values.keys()-known)}")
    if case.startswith("exact_"):
        dimension = int(case[-2])
        if "dimension" in values and values["dimension"] != dimension:
            raise ValueError("La dimension del caso exacto esta definida por su nombre")
        values["dimension"] = dimension
    if case in ("spatial", "temporal"):
        values.setdefault("n",6)
    config = CaseConfig(**values)
    if config.heterogeneous and case != "energy":
        raise ValueError("heterogeneous solo se admite en energy; las referencias exactas son homogeneas")
    if case in ("energy", "spatial", "temporal") or case.startswith("exact_"):
        if config.amplitude_C == 0:
            raise ValueError("Este caso requiere amplitud no nula para evitar verificacion vacua")
    return config


def load_configuration(path):
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"No se pudo leer configuracion JSON: {exc}") from exc
    if not isinstance(document, dict) or document.keys()-{"units", "defaults", "cases"}:
        raise ValueError("La configuracion admite units, defaults y cases")
    units = document.get("units", {})
    if not isinstance(units, dict) or any(SI_UNITS.get(k) != v for k, v in units.items()):
        raise ValueError(f"Unidades incompatibles; se requieren SI: {SI_UNITS}")
    defaults, cases = document.get("defaults", {}), document.get("cases", {})
    if not isinstance(defaults, dict) or not isinstance(cases, dict) or cases.keys()-CASES.keys():
        raise ValueError("defaults y cases deben ser objetos con casos conocidos")
    if any(not isinstance(v, dict) for v in cases.values()):
        raise ValueError("Cada caso debe contener un objeto de parametros")
    for case in CASES:
        make_config(case, {**defaults, **cases.get(case, {})})
    return document


def sine_mode(grid):
    mode = np.ones(grid.shape)
    for axis, (x, length) in enumerate(zip(grid.coordinates, grid.lengths)):
        shape = [1]*len(grid.shape)
        shape[axis] = len(x)
        mode *= np.sin(np.pi*x/length).reshape(shape)
    return mode


def eigenvalues(grid, material):
    continuous = material.alpha * sum((np.pi/length)**2 for length in grid.lengths)
    discrete = material.alpha * sum(4*np.sin(np.pi/(2*n))**2/dx**2
                                    for n, dx in zip(grid.shape, grid.spacing))
    return continuous, discrete


def _system(case, cfg, grid=None):
    grid = grid or CartesianGrid(cfg.lengths_m, cfg.shape)
    material = Material(cfg.k, cfg.rho, cfg.cp)
    boundaries = {}
    if case.startswith("exact_") or case in ("spatial", "temporal"):
        boundaries = {a+b: Dirichlet(cfg.initial_C) for a in "xyz"[:cfg.dimension] for b in "-+"}
    elif case == "neumann":
        boundaries[cfg.face or "x+"] = Neumann(cfg.flux)
    elif case == "robin":
        faces = [cfg.face] if cfg.face else [a+b for a in "xyz"[:cfg.dimension] for b in "-+"]
        boundaries = {face: Robin(cfg.h, cfg.ambient_C) for face in faces}
    if cfg.heterogeneous:
        x = grid.coordinates[0].reshape((-1,)+(1,)*(cfg.dimension-1))
        second = x >= grid.lengths[0]/2
        material = CellMaterial(np.where(second, 3*cfg.k, cfg.k),
                                np.where(second, 1.15*cfg.rho, cfg.rho),
                                np.where(second, .8*cfg.cp, cfg.cp))
    return CartesianSystem(grid, material, boundaries)


def _check(checks, name, measured, tolerance, *, expected=0., units=""):
    measured, tolerance, expected = float(measured), float(tolerance), float(expected)
    passed = math.isfinite(measured) and math.isfinite(tolerance) and abs(measured-expected) <= tolerance
    checks.append(dict(name=name,measured=measured,expected=expected,tolerance=tolerance,
                       units=units,passed=bool(passed)))


def _report(case, cfg, system, result, checks):
    alpha = cfg.k/(cfg.rho*cfg.cp)
    return dict(case=case, category=CASES[case], status="PASS" if all(c["passed"] for c in checks) else "FAIL",
                scope="Verificacion de caja ideal E05; no prediccion de fundacion ni conexion IFC",
                config=asdict(cfg), dimension=cfg.dimension,shape=system.grid.shape,
                cells=math.prod(system.grid.shape),lengths_m=system.grid.lengths,
                spacing_m=system.grid.spacing,temperature_location="cell_centers",
                alpha_m2_s=None if cfg.heterogeneous else alpha,
                requested_dt_s=cfg.dt_s if cfg.dt_s is not None else .6*system.stable_dt,
                effective_dt_s=result.dt, stable_dt_s=system.stable_dt,steps=result.steps,
                t_end_s=float(result.times[-1]),fourier_per_axis=None if cfg.heterogeneous else
                [alpha*result.dt/dx**2 for dx in system.grid.spacing],
                fourier_is_not_universal_limit=True, dt_over_local_limit=result.dt/system.stable_dt,
                boundaries={name:{"type":type(b).__name__,**vars(b)} for name,b in system.boundaries.items()},
                checks=checks)


def run_case(case, config=None):
    """Devuelve reporte, sistema, solución y referencia; PASS depende de checks reales."""
    cfg = config or make_config(case)
    if not isinstance(cfg, CaseConfig):
        raise TypeError("config debe ser CaseConfig")
    # Valida tambien configs construidas directamente, sin pasar por make_config.
    cfg = make_config(case, asdict(cfg))
    if case in ("spatial", "temporal"):
        return run_convergence(case, cfg), None, None, None
    if case == "stability":
        return run_stability(cfg), None, None, None
    system = _system(case, cfg)
    dt = cfg.dt_s if cfg.dt_s is not None else .6*system.stable_dt
    if dt > system.stable_dt*(1+1e-12):
        raise ValueError(f"dt solicitado {dt:g} s supera cota local {system.stable_dt:g} s")
    steps = math.ceil(cfg.t_end_s/dt)
    if steps > 20000 or (steps+1)*math.prod(cfg.shape) > 12000000:
        raise ValueError("Historial de laboratorio demasiado grande; reducir malla/tiempo o ajustar dt estable")
    initial = np.full(cfg.shape, cfg.initial_C)
    if case.startswith("exact_"):
        initial += cfg.amplitude_C*sine_mode(system.grid)
    elif case == "energy":
        mode = np.ones(cfg.shape)
        for axis, (x,length) in enumerate(zip(system.grid.coordinates,cfg.lengths_m)):
            shape = [1]*cfg.dimension
            shape[axis] = len(x)
            mode *= np.cos(np.pi*x/length).reshape(shape)
        initial += cfg.amplitude_C*mode
    source = cfg.q_dot if case == "source" else 0.
    result = solve_nd(system=system,initial=initial,dt=dt,t_end=cfg.t_end_s,q_dot=source)
    energies = np.array([system.energy(t,cfg.initial_C) for t in result.temperature])
    outward = np.array([sum(float(np.sum(v)) for v in system.boundary_heat_rates(t).values())
                         for t in result.temperature[:-1]])
    generated = source*math.prod(cfg.lengths_m)
    expected_energy = energies[0]+np.r_[0.,np.cumsum(result.dt*(generated-outward))]
    scale = float(np.sum(system.capacity))*max(1.,float(np.max(np.abs(result.temperature))))
    tolerance_J = cfg.energy_atol_J+cfg.energy_rtol*(scale+abs(generated)*cfg.t_end_s)
    checks=[]
    _check(checks,"balance_energia_todos_los_pasos",np.max(abs(energies-expected_energy)),tolerance_J,units="J")
    rates_initial = sum(float(np.sum(v)) for v in system.boundary_heat_rates(initial).values())
    internal_sum = float(np.sum(system.power(initial)))+rates_initial
    _check(checks,"cancelacion_intercambios_internos",internal_sum,
           1e-9+cfg.energy_rtol*float(np.sum(abs(system.power(initial)))),units="W")
    exact=None
    if case.startswith("exact_"):
        rate,_ = eigenvalues(system.grid,Material(cfg.k,cfg.rho,cfg.cp))
        exact = cfg.initial_C+cfg.amplitude_C*sine_mode(system.grid)*np.exp(-rate*cfg.t_end_s)
        error = result.temperature[-1]-exact
        _check(checks,"error_Linf",np.max(abs(error)),cfg.atol_C,units="degC")
        for face in system.boundaries:
            _check(checks,"Dirichlet_cara_"+face,
                   np.max(abs(system.face_temperature(result.temperature[-1],face)-cfg.initial_C)),
                   1e-11*max(1.,abs(cfg.initial_C),abs(cfg.amplitude_C)),units="degC")
    elif case == "energy":
        _check(checks,"energia_adiabatica_no_uniforme",np.max(abs(energies-energies[0])),tolerance_J,units="J")
    elif case == "source":
        expected = cfg.initial_C+result.times*cfg.q_dot/(cfg.rho*cfg.cp)
        exact = np.full(cfg.shape,expected[-1])
        reshape=(-1,)+(1,)*cfg.dimension
        _check(checks,"fuente_uniforme_todos_los_tiempos",
               np.max(abs(result.temperature-expected.reshape(reshape))),
               1e-11*max(1.,float(np.max(abs(expected)))),units="degC")
        _check(checks,"energia_generada",energies[-1]-energies[0]-generated*cfg.t_end_s,tolerance_J,units="J")
    elif case == "neumann":
        face = cfg.face or "x+"
        axis = "xyz".index(face[0])
        area = math.prod(length for i,length in enumerate(cfg.lengths_m) if i!=axis)
        prescribed = cfg.flux*area
        _check(checks,"potencia_flujo_por_area",rates_initial-prescribed,
               1e-11*max(1.,abs(prescribed)),units="W")
        _check(checks,"energia_flujo_prescrito",energies[-1]-energies[0]+prescribed*cfg.t_end_s,
               tolerance_J,units="J")
    elif case == "robin":
        for face,boundary in system.boundaries.items():
            if not isinstance(boundary,Robin):continue
            axis="xyz".index(face[0]); key=[slice(None)]*cfg.dimension; key[axis]=0 if face[1]=="-" else -1
            center=result.temperature[-1][tuple(key)]
            face_area=math.prod(d for i,d in enumerate(system.grid.spacing) if i!=axis)
            expected_q=cfg.h*(center-cfg.ambient_C)/(1+cfg.h*system.grid.spacing[axis]/(2*cfg.k))
            actual_q=system.boundary_heat_rates(result.temperature[-1])[face]/face_area
            surface=system.face_temperature(result.temperature[-1],face)
            qscale=max(1.,float(np.max(abs(expected_q))))
            _check(checks,"resistencias_en_serie_"+face,np.max(abs(actual_q-expected_q)),1e-11*qscale,units="W/m^2")
            # Al crecer h, restar temperaturas casi iguales condiciona esta comprobación.
            rounding=64*np.finfo(float).eps*cfg.h*max(1.,abs(cfg.initial_C),abs(cfg.ambient_C))
            _check(checks,"ley_superficial_"+face,np.max(abs(actual_q-cfg.h*(surface-cfg.ambient_C))),
                   1e-10*qscale+rounding,units="W/m^2")
        lower,upper=sorted((cfg.initial_C,cfg.ambient_C))
        overshoot=max(0.,lower-float(result.temperature.min()),float(result.temperature.max())-upper)
        _check(checks,"principio_maximo",overshoot,1e-10*max(1.,abs(lower),abs(upper)),units="degC")
        if cfg.h>0 and cfg.initial_C!=cfg.ambient_C:
            _check(checks,"sentido_intercambio",min(0.,(energies[-1]-energies[0])*(cfg.ambient_C-cfg.initial_C)),
                   tolerance_J*max(1.,abs(cfg.ambient_C-cfg.initial_C)),units="J K")
    report=_report(case,cfg,system,result,checks)
    report.update(energy_initial_J=float(energies[0]),energy_final_J=float(energies[-1]),
                  energy_balance_max_error_J=float(np.max(abs(energies-expected_energy))),
                  energy_tolerance_J=tolerance_J,initial_range_C=float(np.ptp(initial)),
                  final_range_C=float(np.ptp(result.temperature[-1])),
                  final_min_C=float(result.temperature[-1].min()),final_max_C=float(result.temperature[-1].max()))
    if exact is not None:
        error=result.temperature[-1]-exact
        report.update(error_Linf_C=float(np.max(abs(error))),error_L2_rms_C=float(np.sqrt(np.mean(error**2))),
                      error_L2_integral=float(np.sqrt(np.sum(error**2)*system.grid.cell_volume)))
    if case.startswith("exact_"):
        report["reference"]="Solucion sinusoidal de la PDE continua evaluada en centros; caras a initial_C"
        report["lambda_m_minus2"]=sum((np.pi/L)**2 for L in cfg.lengths_m)
    return report,system,result,exact


def run_convergence(case,cfg):
    if cfg.heterogeneous:raise ValueError("La referencia sinusoidal requiere homogeneidad")
    material=Material(cfg.k,cfg.rho,cfg.cp)
    rows=[]
    shapes=[tuple(n*2**i for n in cfg.shape) for i in range(3)] if case=="spatial" else [cfg.shape]*3
    # Rechazar antes de construir arrays: una malla base admisible puede
    # exceder el presupuesto de laboratorio tras multiplicar cada eje por 4.
    if any(math.prod(shape)>262144 for shape in shapes):
        raise ValueError("La malla fina supera el limite de 262144 celdas de laboratorio")
    fine=_system(case,cfg,CartesianGrid(cfg.lengths_m,shapes[-1]))
    # Al menos 20 pasos en el nivel temporal grueso: ceil(t/dt) no debe
    # colapsar varios niveles a un mismo paso efectivo cuando cambia alpha/L².
    fixed_dt=cfg.dt_s if cfg.dt_s is not None else (
        .01*fine.stable_dt if case=="spatial" else min(.6*fine.stable_dt,cfg.t_end_s/20))
    for index,shape in enumerate(shapes):
        system=_system(case,cfg,CartesianGrid(cfg.lengths_m,shape))
        dt=fixed_dt if case=="spatial" else fixed_dt/2**index
        if cfg.t_end_s/dt>200000 or math.ceil(cfg.t_end_s/dt)*math.prod(shape)>200000000:
            raise ValueError("Estudio demasiado costoso para laboratorio; ajustar tiempo/malla/dt")
        mode=sine_mode(system.grid)
        rate,discrete=eigenvalues(system.grid,material)
        initial=cfg.initial_C+cfg.amplitude_C*mode
        result=solve_nd(system=system,initial=initial,dt=dt,t_end=cfg.t_end_s,save_every=100000000)
        reference=cfg.initial_C+cfg.amplitude_C*mode*np.exp(-(rate if case=="spatial" else discrete)*cfg.t_end_s)
        error=result.temperature[-1]-reference
        semiexact=cfg.initial_C+cfg.amplitude_C*mode*np.exp(-discrete*cfg.t_end_s)
        rows.append(dict(shape=system.grid.shape,spacing_m=system.grid.spacing,requested_dt_s=dt,
                         effective_dt_s=result.dt,stable_dt_s=system.stable_dt,steps=result.steps,
                         cells=math.prod(system.grid.shape),t_end_s=cfg.t_end_s,
                         fourier_per_axis=[material.alpha*result.dt/d**2 for d in system.grid.spacing],
                         error_Linf_C=float(np.max(abs(error))),error_L2_rms_C=float(np.sqrt(np.mean(error**2))),
                         temporal_contamination_C=float(np.max(abs(result.temperature[-1]-semiexact)))))
    errors=[row["error_Linf_C"] for row in rows]
    if any(error<=1e-12*max(1.,abs(cfg.amplitude_C)) for error in errors):
        raise ValueError("Error cercano a redondeo: no permite medir orden de forma fiable")
    ratios=[a/b for a,b in zip(errors,errors[1:])]
    denominator=[2.,2.] if case=="spatial" else [a["effective_dt_s"]/b["effective_dt_s"] for a,b in zip(rows,rows[1:])]
    if any(value<=1 for value in denominator):raise ValueError("El refinamiento no reduce el paso efectivo")
    orders=[math.log(ratio)/math.log(refinement) for ratio,refinement in zip(ratios,denominator)]
    target=2. if case=="spatial" else 1.
    checks=[]
    for index,order in enumerate(orders):
        _check(checks,f"orden_observado_{index}",order,.3 if case=="spatial" else .15,expected=target)
    if case=="spatial":
        contamination=max(row["temporal_contamination_C"]/row["error_Linf_C"] for row in rows)
        _check(checks,"contaminacion_temporal_menor_10pct",max(0.,contamination-.1),0.)
    return dict(case=case,category="convergence",status="PASS" if all(c["passed"] for c in checks) else "FAIL",
                config=asdict(cfg),dimension=cfg.dimension,rows=rows,error_ratios=ratios,observed_orders=orders,
                reference="PDE continua" if case=="spatial" else "Modo exacto semidiscreto sobre malla fija",
                checks=checks)


def run_stability(cfg):
    system=_system("energy",cfg)
    x=system.grid.coordinates[0].reshape((-1,)+(1,)*(cfg.dimension-1))
    initial=np.broadcast_to(cfg.initial_C+cfg.amplitude_C*np.cos(np.pi*x/cfg.lengths_m[0]),cfg.shape)
    near=cfg.dt_s if cfg.dt_s is not None else .99*system.stable_dt
    duration=max(near,cfg.t_end_s)
    if duration/near>20000 or math.ceil(duration/near)*math.prod(cfg.shape)>200000000:
        raise ValueError("Estudio de estabilidad demasiado costoso para laboratorio")
    result=solve_nd(system=system,initial=initial,dt=near,t_end=duration,save_every=1000000)
    rejected=False
    try:solve_nd(system=system,initial=initial,dt=1.01*system.stable_dt,t_end=1.)
    except ValueError as exc:
        if "cota" not in str(exc):raise
        rejected=True
    checks=[]
    _check(checks,"paso_excesivo_rechazado",float(rejected),0.,expected=1.)
    excess=max(0.,float(result.temperature.max()-initial.max()),float(initial.min()-result.temperature.min()))
    _check(checks,"paso_cercano_al_limite_monotono",excess,1e-10,units="degC")
    report=_report("stability",cfg,system,result,checks)
    report.update(requested_dt_s=near,accepted_dt_s=near,rejected_dt_s=1.01*system.stable_dt)
    return report
