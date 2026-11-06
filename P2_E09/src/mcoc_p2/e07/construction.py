"""Calendario ilustrativo, estados y pasos que alcanzan cada evento exactamente."""
from dataclasses import dataclass
import math
import numpy as np
from ..diffusion_1d import Material
from .hydration import AdiabaticCurve,HydrationContext,q_dot_h


@dataclass(frozen=True)
class PourEvent:
    pour_id:int
    activation_s:float
    initial_C:float
    material:Material
    hydration:AdiabaticCurve

    def __post_init__(self):
        if isinstance(self.pour_id,bool) or not isinstance(self.pour_id,int) or self.pour_id<=0:raise ValueError('VertidaID entero positivo')
        if not math.isfinite(self.activation_s) or self.activation_s<0:raise ValueError('Activación no negativa finita')
        if not math.isfinite(self.initial_C) or self.initial_C<=-273.15:raise ValueError('Colocación física en °C')
        if not isinstance(self.material,Material) or not isinstance(self.hydration,AdiabaticCurve):raise ValueError('Material y curva requeridos')


class ConstructionState:
    def __init__(self,voxels,events):
        self.voxels=voxels;self.events=sorted(events,key=lambda e:(e.activation_s,e.pour_id))
        if len({e.pour_id for e in self.events})!=len(self.events):raise ValueError('Un evento por vertida; identificador duplicado')
        if {e.pour_id for e in self.events}!=set(voxels.guid_by_id):raise ValueError('Calendario debe cubrir exactamente las vertidas')
        self.time_s=0.;self.applied=set();self.temperature_C=np.full(voxels.grid.shape,np.nan)
        self.advance_to(0.)

    def active_mask(self,t=None):
        t=self.time_s if t is None else t
        if not math.isfinite(t) or t<0:raise ValueError('Tiempo no negativo')
        return np.isin(self.voxels.vertida_id,[e.pour_id for e in self.events if e.activation_s<=t])

    def pour_age(self,t,identifier):
        if not math.isfinite(t) or t<0:raise ValueError('Tiempo no negativo')
        event=next((e for e in self.events if e.pour_id==identifier),None)
        if event is None:raise ValueError('Vertida desconocida')
        return None if t<event.activation_s else t-event.activation_s

    def advance_to(self,t):
        if not math.isfinite(t) or t<self.time_s:raise ValueError('El tiempo debe avanzar')
        if any(self.time_s<e.activation_s<t for e in self.events if e.pour_id not in self.applied):raise ValueError('No saltar un evento: usar time_grid')
        added=[]
        for e in self.events:
            if e.activation_s<=t and e.pour_id not in self.applied:
                self.temperature_C[self.voxels.vertida_id==e.pour_id]=e.initial_C
                self.applied.add(e.pour_id);added.append(e.pour_id)
        self.time_s=t
        return added

    def time_grid(self,t_end,dt):
        if not math.isfinite(dt) or dt<=0 or not math.isfinite(t_end) or t_end<0:raise ValueError('dt>0 y tiempo final>=0')
        breaks=sorted({0.,float(t_end),*[e.activation_s for e in self.events if e.activation_s<=t_end]})
        result=[0.]
        for a,b in zip(breaks,breaks[1:]):
            n=math.ceil((b-a)/dt)
            if n>100000 or len(result)+n>100000:raise ValueError('Demasiados pasos de demostración')
            result.extend(np.linspace(a,b,n+1)[1:].tolist())
        return np.array(result)

    def hydration_source(self):
        field=np.zeros(self.voxels.grid.shape)
        for e in self.events:
            if e.pour_id in self.applied:
                cells=self.voxels.vertida_id==e.pour_id
                field[cells]=q_dot_h(self.time_s,self.temperature_C[cells],e.material,HydrationContext(e.hydration,e.activation_s))
        return field

    def hydration_report(self):
        """Parámetros efectivos, potencia y calor prescrito por vertida.

        released_energy_J integra la curva analítica desde la colocación;
        no es energía sensible obtenida de una integración térmica.
        """
        rows=[]
        for e in self.events:
            volume=float(np.count_nonzero(self.voxels.vertida_id==e.pour_id))*self.voxels.grid.cell_volume
            age=self.pour_age(self.time_s,e.pour_id)
            source=0. if age is None else float(e.hydration.source(age))
            released=0. if age is None else float(e.hydration.released(0.,age))
            rows.append(dict(vertida_id=e.pour_id,activation_s=e.activation_s,age_s=age,
                active=e.pour_id in self.applied,initial_C=e.initial_C,volume_m3=volume,
                material=dict(k=e.material.k,rho=e.material.rho,cp=e.material.cp),
                H_vol_J_m3=e.hydration.H_vol_J_m3,duration_s=e.hydration.duration_s,
                adiabatic_potential_rise_C=e.hydration.H_vol_J_m3/(e.material.rho*e.material.cp),
                source_W_m3=source,source_power_W=source*volume,
                released_J_m3=released,released_energy_J=released*volume))
        return rows
