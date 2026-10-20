"""Difusión 1D: balance nodal conservativo y Euler explícito, todo en SI.

Nodos x_i=i*dx incluidos los extremos. Volúmenes por área: dx interiores,
dx/2 extremos. Flujo Neumann positivo SALIENTE en ambas caras.
Fuente y fronteras constantes en el tiempo, material homogéneo constante.
Ver docs/FORMULACION_1D.md para derivación y restricciones.
"""

from dataclasses import dataclass
import math

import numpy as np
from numpy.typing import ArrayLike, NDArray


def _finite(name: str, value: float, *, positive: bool = False) -> None:
    if not math.isfinite(value) or (positive and value <= 0):
        raise ValueError(f"{name} debe ser finito" + (" y positivo" if positive else ""))


@dataclass(frozen=True)
class Material:
    """k [W/(m K)], rho [kg/m³], cp [J/(kg K)]; alpha se deriva en m²/s."""

    k: float
    rho: float
    cp: float

    def __post_init__(self) -> None:
        for name in ("k", "rho", "cp"):
            _finite(name, getattr(self, name), positive=True)
        _finite("rho*cp", self.rho * self.cp, positive=True)
        _finite("alpha", self.alpha, positive=True)

    @property
    def alpha(self) -> float:
        return self.k / (self.rho * self.cp)


@dataclass(frozen=True)
class Dirichlet:
    """Temperatura superficial prescrita [°C], también impuesta en t=0."""

    temperature: float

    def __post_init__(self) -> None:
        _finite("temperature", self.temperature)


@dataclass(frozen=True)
class Neumann:
    """Flujo SALIENTE [W/m²]. Cero: adiabático; negativo: aporte de calor."""

    outward_flux: float = 0.0

    def __post_init__(self) -> None:
        _finite("outward_flux", self.outward_flux)


@dataclass(frozen=True)
class Robin:
    """q_out=h*(T_surface-ambient); h [W/(m² K)] >=0, ambient [°C]."""

    h: float
    ambient: float

    def __post_init__(self) -> None:
        _finite("h", self.h)
        _finite("ambient", self.ambient)
        if self.h < 0:
            raise ValueError("h debe ser no negativo")


Boundary = Dirichlet | Neumann | Robin


def stable_timestep(material: Material, dx: float, left: Boundary,
                    right: Boundary) -> float:
    """Cota suficiente de monotonía: Fo<=1/2 y Fo*(1+h*dx/k)<=1/2.

    La segunda restricción se aplica en cada extremo Robin. No cubre fuentes
    dependientes de T, propiedades heterogéneas ni fronteras dinámicas.
    """
    _finite("dx", dx, positive=True)
    limit = dx**2 / (2 * material.alpha)
    for boundary in (left, right):
        if not isinstance(boundary, (Dirichlet, Neumann, Robin)):
            raise TypeError("Frontera debe ser Dirichlet, Neumann o Robin")
        if isinstance(boundary, Robin):
            limit = min(limit, dx**2 / (
                2 * material.alpha * (1 + boundary.h * dx / material.k)))
    _finite("dt estable", limit, positive=True)
    return limit


def _field(value: ArrayLike, nx: int, name: str) -> NDArray[np.float64]:
    array = np.asarray(value, dtype=float)
    if array.ndim == 0:
        array = np.full(nx, float(array))
    if array.shape != (nx,) or not np.all(np.isfinite(array)):
        raise ValueError(f"{name}: se espera escalar o vector finito de largo nx={nx}")
    return array.copy()


def _widths(nx: int, dx: float) -> NDArray[np.float64]:
    widths = np.full(nx, dx)
    widths[[0, -1]] *= 0.5
    return widths


@dataclass(frozen=True)
class Solution:
    """Temperaturas [°C] de forma (instantes guardados, nx); tiempos en s."""

    x: NDArray[np.float64]
    times: NDArray[np.float64]
    temperature: NDArray[np.float64]
    dt: float
    fourier: float
    steps: int


def solve(*, material: Material, length: float, nx: int, dt: float,
          t_end: float, initial: ArrayLike, left: Boundary = Neumann(),
          right: Boundary = Neumann(), q_dot: ArrayLike = 0.0,
          save_every: int = 1) -> Solution:
    """Integra rho*cp*dT/dt=k*d²T/dx²+q_dot; q_dot en W/m³.

    initial y q_dot: escalar o vector nx, independientes del tiempo.
    Rechaza dt solicitado fuera de la cota; luego reduce dt uniformemente
    para llegar exactamente a t_end. Guarda siempre t=0 y el estado final.
    Dirichlet prevalece sobre initial en los extremos correspondientes.
    """
    _finite("length", length, positive=True)
    _finite("dt", dt, positive=True)
    _finite("t_end", t_end)
    if t_end < 0:
        raise ValueError("t_end debe ser no negativo")
    for name, value, minimum in (("nx", nx, 3), ("save_every", save_every, 1)):
        if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < minimum:
            raise ValueError(f"{name} debe ser entero >= {minimum}")
    dx = length / (nx - 1)
    limit = stable_timestep(material, dx, left, right)
    if dt > limit * (1 + 1e-12):
        raise ValueError(f"dt={dt:g} s supera cota explícita {limit:g} s (incluye Robin)")
    temperature = _field(initial, nx, "initial")
    source = _field(q_dot, nx, "q_dot")
    boundaries = ((0, left), (-1, right))
    for index, boundary in boundaries:
        if isinstance(boundary, Dirichlet):
            temperature[index] = boundary.temperature

    steps = math.ceil(t_end / dt)
    actual_dt = t_end / steps if steps else 0.0
    widths = _widths(nx, dx)
    capacity = material.rho * material.cp * widths  # J/(m² K)
    snapshots = [temperature.copy()]
    times = [0.0]
    for step in range(1, steps + 1):
        # Cada intercambio se suma a un volumen y se resta al vecino.
        exchange = material.k / dx * np.diff(temperature)  # W/m² hacia izquierda
        power = source * widths
        power[:-1] += exchange
        power[1:] -= exchange
        for index, boundary in boundaries:
            if isinstance(boundary, Neumann):
                power[index] -= boundary.outward_flux
            elif isinstance(boundary, Robin):
                power[index] -= boundary.h * (temperature[index] - boundary.ambient)
        temperature = temperature + actual_dt * power / capacity
        for index, boundary in boundaries:
            if isinstance(boundary, Dirichlet):
                temperature[index] = boundary.temperature
        if not np.all(np.isfinite(temperature)):
            raise FloatingPointError("Temperatura no finita; revisar escala de entradas")
        if step % save_every == 0 or step == steps:
            snapshots.append(temperature.copy())
            times.append(t_end if step == steps else step * actual_dt)
    return Solution(np.linspace(0, length, nx), np.array(times),
                    np.array(snapshots), actual_dt,
                    material.alpha * actual_dt / dx**2, steps)


def energy_per_area(temperature: ArrayLike, material: Material, dx: float,
                    reference: float = 0.0) -> NDArray[np.float64]:
    """E/A=rho*cp*sum((T-Tref)*width) [J/m²], medias celdas en extremos.

    Se comparan diferencias de energía sensible respecto de Tref [°C].
    El último eje es espacial; admite un perfil o una historia de perfiles.
    """
    _finite("dx", dx, positive=True)
    _finite("reference", reference)
    values = np.asarray(temperature, dtype=float)
    if values.ndim < 1 or values.shape[-1] < 3 or not np.all(np.isfinite(values)):
        raise ValueError("temperature debe tener al menos 3 nodos finitos")
    return material.rho * material.cp * np.sum(
        (values - reference) * _widths(values.shape[-1], dx), axis=-1)
