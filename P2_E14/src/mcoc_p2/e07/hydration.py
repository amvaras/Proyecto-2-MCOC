"""Curva adiabática prescrita: parámetros ilustrativos, sin calibración Freirina."""
from dataclasses import dataclass
import math
import numpy as np


@dataclass(frozen=True)
class AdiabaticCurve:
    H_vol_J_m3:float=64_800_000.
    duration_s:float=172800.

    def __post_init__(self):
        if not math.isfinite(self.H_vol_J_m3) or self.H_vol_J_m3<0 or not math.isfinite(self.duration_s) or self.duration_s<=0:raise ValueError('H_vol>=0 J/m³ y duración>0 s finitos')

    def degree(self,age_s):
        age=np.asarray(age_s,dtype=float)
        if not np.isfinite(age).all():raise ValueError('Edad finita')
        u=np.clip(age/self.duration_s,0,1)
        return .5*(1-np.cos(np.pi*u))

    def source(self,age_s):
        age=np.asarray(age_s,dtype=float)
        if not np.isfinite(age).all():raise ValueError('Edad finita')
        u=age/self.duration_s
        return np.where((u>0)&(u<1),self.H_vol_J_m3*np.pi/(2*self.duration_s)*np.sin(np.pi*np.clip(u,0,1)),0.)

    def released(self,age0_s,age1_s):
        if np.any(np.asarray(age1_s)<np.asarray(age0_s)):raise ValueError('Edades deben aumentar')
        return self.H_vol_J_m3*(self.degree(age1_s)-self.degree(age0_s))

    def adiabatic_temperature(self,age_s,material,initial_C=20.):
        if not math.isfinite(initial_C) or initial_C<=-273.15:raise ValueError('Temperatura física en °C')
        return initial_C+self.H_vol_J_m3*self.degree(age_s)/(material.rho*material.cp)


@dataclass(frozen=True)
class HydrationContext:
    curve:AdiabaticCurve
    activation_s:float

    def __post_init__(self):
        if not math.isfinite(self.activation_s) or self.activation_s<0:raise ValueError('Activación finita no negativa')


def q_dot_h(t,T,material,estado):
    """W/m³. Modelo prescrito por edad real; T no acelera la cinética.

    No usa Arrhenius ni edad equivalente. Se valida T en Celsius; no hay
    expresiones termodinámicas que requieran convertir a Kelvin en este modelo.
    """
    if not math.isfinite(t) or t<0:raise ValueError('Tiempo no negativo finito')
    temperatures=np.asarray(T,dtype=float)
    if not np.isfinite(temperatures).all() or np.any(temperatures<=-273.15):raise ValueError('Temperatura física °C')
    if material.rho<=0 or material.cp<=0:raise ValueError('Capacidad material positiva')
    return np.full_like(temperatures,estado.curve.source(t-estado.activation_s),dtype=float)
