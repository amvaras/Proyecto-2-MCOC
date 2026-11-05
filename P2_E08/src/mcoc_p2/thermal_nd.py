"""Balances por caras en cajas cartesianas 1D/2D/3D, centros de celda, SI.

No hay voxelización IFC ni activación. Fuente y bordes constantes en tiempo.
El núcleo depende solo de NumPy y de las clases físicas heredadas de E01.
"""
from dataclasses import dataclass
from collections.abc import Mapping
import math

import numpy as np

from .diffusion_1d import Material, Dirichlet, Neumann, Robin


def _field(value, shape, name, *, positive=False):
    if np.iscomplexobj(value):
        raise ValueError(f"{name}: se requieren valores reales")
    try:
        data = np.broadcast_to(np.asarray(value, dtype=float), shape).copy()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name}: forma incompatible con {shape}") from exc
    if not np.all(np.isfinite(data)) or (positive and np.any(data <= 0)):
        raise ValueError(f"{name}: valores finitos" + (" y positivos" if positive else ""))
    return data


@dataclass(frozen=True)
class CartesianGrid:
    """shape = número de celdas; lengths [m]; ejes ordenados x, y, z."""

    lengths: tuple
    shape: tuple

    def __post_init__(self):
        lengths, shape = tuple(self.lengths), tuple(self.shape)
        if not 1 <= len(shape) <= 3 or len(lengths) != len(shape):
            raise ValueError("Se requieren 1, 2 o 3 ejes con igual número de longitudes")
        if any(isinstance(n, (bool, np.bool_)) or not isinstance(n, (int, np.integer))
               or n < 2 for n in shape):
            raise ValueError("shape: cada eje requiere un entero >= 2 celdas")
        if any(not math.isfinite(v) or v <= 0 for v in lengths):
            raise ValueError("lengths: longitudes finitas y positivas en metros")
        object.__setattr__(self, "lengths", lengths)
        object.__setattr__(self, "shape", shape)

    @property
    def spacing(self):
        return tuple(length / n for length, n in zip(self.lengths, self.shape))

    @property
    def cell_volume(self):
        # En 1D/2D se adopta sección/espesor unitario en las direcciones omitidas.
        return math.prod(self.spacing)

    @property
    def coordinates(self):
        return tuple((np.arange(n) + .5) * d for n, d in zip(self.shape, self.spacing))


@dataclass(frozen=True)
class CellMaterial:
    """Propiedades constantes en tiempo, escalares o arrays compatibles con shape.

    k [W/(m K)], rho [kg/m³], cp [J/(kg K)]. Contacto térmico perfecto.
    """

    k: object
    rho: object
    cp: object


@dataclass(frozen=True)
class NDSolution:
    times: np.ndarray
    temperature: np.ndarray
    dt: float
    steps: int
    stable_dt: float


class CartesianSystem:
    """C_i dT_i/dt = sum G_ij(T_j-T_i) + q_dot V - sum q_out A.

    Cada cara externa recibe una condición independiente. Nombres: x-/x+,
    y-/y+, z-/z+. Las caras omitidas son adiabáticas. No hay celdas inactivas.
    """

    def __init__(self, grid: CartesianGrid, material: Material | CellMaterial,
                 boundaries: Mapping | None = None):
        if not isinstance(material, (Material, CellMaterial)):
            raise TypeError("material debe ser Material o CellMaterial")
        self.grid = grid
        self.k = _field(material.k, grid.shape, "k", positive=True)
        self.rho_cp = (_field(material.rho, grid.shape, "rho", positive=True)
                       * _field(material.cp, grid.shape, "cp", positive=True))
        self.capacity = self.rho_cp * grid.cell_volume
        if not np.all(np.isfinite(self.capacity)) or np.any(self.capacity <= 0):
            raise ValueError("Capacidad térmica fuera de rango")
        allowed = {f"{axis}{side}" for axis in "xyz"[:len(grid.shape)] for side in "-+"}
        supplied = dict(boundaries or {})
        if supplied.keys() - allowed:
            raise ValueError(f"Caras desconocidas: {sorted(supplied.keys() - allowed)}")
        self.boundaries = {name: supplied.get(name, Neumann()) for name in sorted(allowed)}
        self._interfaces = []
        self._faces = {}
        diagonal = np.zeros(grid.shape)
        for axis, dx in enumerate(grid.spacing):
            area = grid.cell_volume / dx
            lo, hi = [slice(None)] * len(grid.shape), [slice(None)] * len(grid.shape)
            lo[axis], hi[axis] = slice(None, -1), slice(1, None)
            lo, hi = tuple(lo), tuple(hi)
            # Dos resistencias de media celda en serie: media armónica de k.
            conductance = area / (dx / (2 * self.k[lo]) + dx / (2 * self.k[hi]))
            self._interfaces.append((lo, hi, conductance))
            diagonal[lo] += conductance
            diagonal[hi] += conductance
            for side, index in (("-", 0), ("+", -1)):
                name = "xyz"[axis] + side
                key = [slice(None)] * len(grid.shape)
                key[axis] = index
                key = tuple(key)
                boundary = self.boundaries[name]
                resistance = dx / (2 * self.k[key])  # m² K/W, centro a cara
                if isinstance(boundary, Dirichlet):
                    g = area / resistance
                elif isinstance(boundary, Robin):
                    g = area * boundary.h / (1 + boundary.h * resistance)
                elif isinstance(boundary, Neumann):
                    g = np.zeros_like(resistance)
                else:
                    raise TypeError(f"{name}: frontera debe ser Dirichlet, Neumann o Robin")
                self._faces[name] = (key, area, resistance, g)
                diagonal[key] += g
        if not np.all(np.isfinite(diagonal)) or np.any(diagonal <= 0):
            raise ValueError("Conductancias fuera de rango")
        self.stable_dt = float(np.min(self.capacity / diagonal))
        if not math.isfinite(self.stable_dt) or self.stable_dt <= 0:
            raise ValueError("Paso estable fuera de rango")

    def boundary_heat_rates(self, temperature):
        """Potencia por cara/celda de borde [W], positiva SALIENTE en toda cara."""
        t = _field(temperature, self.grid.shape, "temperature")
        rates = {}
        for name, (key, area, _, g) in self._faces.items():
            boundary = self.boundaries[name]
            if isinstance(boundary, Neumann):
                rates[name] = np.full_like(t[key], boundary.outward_flux * area)
            else:
                reservoir = (boundary.temperature if isinstance(boundary, Dirichlet)
                             else boundary.ambient)
                rates[name] = g * (t[key] - reservoir)
        return rates

    def face_temperature(self, temperature, face):
        """Temperatura física de cara [°C]; distinta del centro y del ambiente."""
        t = _field(temperature, self.grid.shape, "temperature")
        key, area, resistance, _ = self._faces[face]
        return t[key] - self.boundary_heat_rates(t)[face] / area * resistance

    def power(self, temperature, q_dot=0.):
        """Potencia neta por celda [W]; fuente volumétrica q_dot [W/m³]."""
        t = _field(temperature, self.grid.shape, "temperature")
        power = _field(q_dot, self.grid.shape, "q_dot") * self.grid.cell_volume
        for lo, hi, g in self._interfaces:
            exchange = g * (t[hi] - t[lo])
            power[lo] += exchange
            power[hi] -= exchange
        for name, rate in self.boundary_heat_rates(t).items():
            power[self._faces[name][0]] -= rate
        return power

    def energy(self, temperature, reference=0.):
        """Energía sensible [J]; para historia usar un llamado por instante."""
        if not math.isfinite(reference):
            raise ValueError("reference debe ser finito")
        t = _field(temperature, self.grid.shape, "temperature")
        return float(np.sum(self.capacity * (t - reference)))


def solve_nd(*, system: CartesianSystem, initial, dt: float, t_end: float,
             q_dot=0., save_every: int = 1):
    """Euler explícito; dt solicitado debe cumplir monotonía local C/sum(G).

    Fuente prescrita constante en tiempo, escalar o campo. initial representa
    centros: Dirichlet fija la CARA, sin sobrescribir centros iniciales.
    """
    if not math.isfinite(dt) or dt <= 0:
        raise ValueError("dt debe ser finito y positivo")
    if not math.isfinite(t_end) or t_end < 0:
        raise ValueError("t_end debe ser finito y no negativo")
    if isinstance(save_every, (bool, np.bool_)) or not isinstance(save_every, (int, np.integer)) or save_every < 1:
        raise ValueError("save_every debe ser un entero positivo")
    if dt > system.stable_dt * (1 + 1e-12):
        raise ValueError(f"dt={dt:g} supera cota explícita local {system.stable_dt:g} s")
    t = _field(initial, system.grid.shape, "initial")
    source = _field(q_dot, system.grid.shape, "q_dot")
    steps = math.ceil(t_end / dt)
    actual_dt = t_end / steps if steps else 0.
    history, times = [t.copy()], [0.]
    for step in range(1, steps + 1):
        t += actual_dt * system.power(t, source) / system.capacity
        if not np.all(np.isfinite(t)):
            raise FloatingPointError("Temperatura no finita")
        if step % save_every == 0 or step == steps:
            history.append(t.copy())
            times.append(t_end if step == steps else step * actual_dt)
    return NDSolution(np.array(times), np.array(history), actual_dt, steps, system.stable_dt)
