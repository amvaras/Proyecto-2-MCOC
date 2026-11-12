"""Ley de borde por cara expuesta. El signo positivo sale del hormigón."""

from dataclasses import dataclass

import numpy as np

from .weather import finite_number


@dataclass(frozen=True)
class Air:
    h_still_W_m2K: float
    h_wind_per_m_s: float
    solar_absorptivity: float

    def __post_init__(self):
        finite_number(self.h_still_W_m2K, "h sin viento", 0)
        if self.h_still_W_m2K == 0:
            raise ValueError("h sin viento debe ser positivo")
        finite_number(self.h_wind_per_m_s, "Coeficiente de viento", 0)
        if finite_number(self.solar_absorptivity, "Absortividad solar", 0) > 1:
            raise ValueError("La absortividad solar no puede superar 1")

    def h(self, wind_m_s):
        return self.h_still_W_m2K + self.h_wind_per_m_s * wind_m_s


@dataclass(frozen=True)
class Soil:
    temperature_C: float
    depth_m: float
    conductivity_W_mK: float
    contact_m2K_W: float = 0.0
    adiabatic: bool = False

    def __post_init__(self):
        finite_number(self.temperature_C, "Temperatura de suelo", -273.15)
        finite_number(self.depth_m, "Profundidad de suelo", 0)
        if finite_number(self.conductivity_W_mK, "Conductividad de suelo", 0) == 0:
            raise ValueError("La conductividad de suelo debe ser positiva")
        finite_number(self.contact_m2K_W, "Resistencia de contacto", 0)
        if type(self.adiabatic) is not bool:
            raise ValueError("adiabatic debe ser booleano")

    @property
    def resistance(self):
        return self.depth_m / self.conductivity_W_mK + self.contact_m2K_W


@dataclass(frozen=True)
class Layer:
    name: str
    thickness_m: float
    conductivity_W_mK: float

    def __post_init__(self):
        finite_number(self.thickness_m, "Espesor", 0)
        if finite_number(self.conductivity_W_mK, "Conductividad de capa", 0) == 0:
            raise ValueError("La conductividad de capa debe ser positiva")


@dataclass(frozen=True)
class Formwork:
    orientations: tuple
    remove_at_s: float
    layers: tuple

    def __post_init__(self):
        allowed = {"x-", "x+", "y-", "y+", "z+"}
        if not set(self.orientations) <= allowed:
            raise ValueError("Orientación de moldaje desconocida")
        finite_number(self.remove_at_s, "Hora de desmolde", 0)

    @property
    def resistance(self):
        return sum(layer.thickness_m / layer.conductivity_W_mK for layer in self.layers)


class Environment:
    def __init__(self, voxels, weather, air, soil, formwork):
        self.weather = weather
        self.air = air
        self.soil = soil
        self.formwork = formwork
        self.base_index = np.flatnonzero(voxels.occupation_mask.any(axis=(0, 1)))[0]
        self.change_times_s = tuple(sorted({*weather.change_times_s, formwork.remove_at_s}))

    def __call__(self, assembly, time_s):
        sample = self.weather.at(time_s)
        faces = assembly.faces
        up = (faces.axis == 2) & (faces.sign == 1)
        ground = (faces.axis == 2) & (faces.sign == -1) & (faces.indices[:, 2] == self.base_index)
        half_cell = np.asarray(assembly.voxels.grid.spacing)[faces.axis] / (2 * assembly.k[assembly.face_indices])
        resistance = half_cell.copy()
        if time_s < self.formwork.remove_at_s:
            covered = np.zeros(len(faces.axis), dtype=bool)
            for orientation in self.formwork.orientations:
                axis = "xyz".index(orientation[0])
                sign = -1 if orientation[1] == "-" else 1
                covered |= (faces.axis == axis) & (faces.sign == sign)
            covered &= (faces.classification != "future_pour") & ~ground
            resistance[covered] += self.formwork.resistance

        h = self.air.h(sample.wind_m_s)
        denominator = 1 + h * resistance
        conductance = faces.areas * h / denominator
        reservoir = np.full(len(faces.axis), sample.air_C)
        # Sol absorbido en la cara exterior. El nodo de superficie reparte
        # esta potencia entre el aire y el hormigón en el mismo balance.
        solar = faces.areas * up * self.air.solar_absorptivity * sample.ghi_W_m2 / denominator
        reservoir[ground] = self.soil.temperature_C
        if self.soil.adiabatic:
            conductance[ground] = 0
        else:
            conductance[ground] = faces.areas[ground] / (half_cell[ground] + self.soil.resistance)
        assembly.set_face_conditions(conductance, reservoir, -solar)
