"""Ensamblaje enmascarado de capacidad y potencia; NO integrador transiente final."""
import math
import numpy as np
from ..diffusion_1d import Material,Dirichlet,Neumann,Robin
from .faces import contacts,exposed_faces


class MaskedAssembly:
    def __init__(self,voxels,active,materials,boundaries=None):
        self.voxels=voxels;self.active=np.asarray(active,dtype=bool).copy()
        if self.active.shape!=voxels.grid.shape or np.any(self.active&~voxels.occupation_mask):raise ValueError('Máscara activa incompatible')
        if set(materials)!=set(voxels.guid_by_id) or any(not isinstance(m,Material) for m in materials.values()):raise ValueError('Un material por vertida')
        self.capacity=np.zeros(voxels.grid.shape);self.k=np.zeros(voxels.grid.shape)
        for pid,material in materials.items():
            cells=self.active&(voxels.vertida_id==pid)
            self.k[cells]=material.k;self.capacity[cells]=material.rho*material.cp*voxels.grid.cell_volume
        self.edges=contacts(voxels,self.active,different_only=False);self.faces=exposed_faces(voxels,self.active)
        first,second=self.edges['first'],self.edges['second'];self.i=tuple(first.T);self.j=tuple(second.T)
        d=np.array(voxels.grid.spacing)[self.edges['axis']]
        self.g=self.edges['area_m2']/(d/(2*self.k[self.i])+d/(2*self.k[self.j]))
        allowed={a+s for a in 'xyz' for s in '-+'};supplied=dict(boundaries or {})
        if supplied.keys()-allowed:raise ValueError('Cara desconocida')
        if any(not isinstance(b,(Dirichlet,Neumann,Robin)) for b in supplied.values()):raise ValueError('Frontera desconocida')
        self.boundaries={name:supplied.get(name,Neumann()) for name in allowed}
        self.face_g=np.zeros(len(self.faces.areas));self.reservoir=np.zeros(len(self.faces.areas));self.prescribed=np.zeros(len(self.faces.areas))
        self.face_indices=tuple(self.faces.indices.T)
        for a in range(3):
            for sign in (-1,1):
                select=(self.faces.axis==a)&(self.faces.sign==sign);b=self.boundaries['xyz'[a]+('+' if sign==1 else '-')]
                key=tuple(self.faces.indices[select].T);r=voxels.grid.spacing[a]/(2*self.k[key]);area=self.faces.areas[select]
                if isinstance(b,Neumann):self.prescribed[select]=b.outward_flux*area
                elif isinstance(b,Dirichlet):self.face_g[select]=area/r;self.reservoir[select]=b.temperature
                else:self.face_g[select]=area*b.h/(1+b.h*r);self.reservoir[select]=b.ambient
        diagonal=np.zeros(voxels.grid.shape)
        np.add.at(diagonal,self.i,self.g);np.add.at(diagonal,self.j,self.g);np.add.at(diagonal,self.face_indices,self.face_g)
        candidates=self.active&(diagonal>0)
        self.stable_dt=float(np.min(self.capacity[candidates]/diagonal[candidates])) if candidates.any() else math.inf

    def power(self,temperature_C,q_dot=0.):
        t=np.asarray(temperature_C,dtype=float);q=np.broadcast_to(np.asarray(q_dot,dtype=float),self.voxels.grid.shape)
        if t.shape!=self.voxels.grid.shape or not np.isfinite(t[self.active]).all() or not np.isfinite(q[self.active]).all():raise ValueError('Campos activos finitos')
        power=np.zeros(self.voxels.grid.shape);power[self.active]=q[self.active]*self.voxels.grid.cell_volume
        exchange=self.g*(t[self.j]-t[self.i]);np.add.at(power,self.i,exchange);np.add.at(power,self.j,-exchange)
        outward=self.face_g*(t[self.face_indices]-self.reservoir)+self.prescribed
        np.add.at(power,self.face_indices,-outward)
        return power,float(outward.sum())

    def energy(self,temperature_C,reference=0.):
        t=np.asarray(temperature_C,dtype=float)
        if t.shape!=self.active.shape or not np.isfinite(t[self.active]).all() or not math.isfinite(reference):raise ValueError('Temperaturas activas y referencia finitas')
        return float(np.sum(self.capacity[self.active]*(t[self.active]-reference)))
