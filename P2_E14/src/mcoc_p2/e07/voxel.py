"""Grilla SI XYZ, etiquetas por centro y regla determinista de interfaz."""
from dataclasses import dataclass
import math
import numpy as np
from ..thermal_nd import CartesianGrid


@dataclass(frozen=True)
class VoxelGrid:
    origin:tuple
    spacing:tuple
    shape:tuple

    def __post_init__(self):
        if len(self.origin)!=3 or len(self.spacing)!=3 or len(self.shape)!=3:raise ValueError('Grilla requiere tres ejes')
        if not np.isfinite(self.origin).all() or not np.isfinite(self.spacing).all() or min(self.spacing)<=0:raise ValueError('Origen finito y pasos positivos SI')
        if any(isinstance(n,(bool,np.bool_)) or not isinstance(n,(int,np.integer)) or n<1 for n in self.shape):raise ValueError('Shape entero positivo')
        if math.prod(self.shape)>2_000_000:raise ValueError('Grilla supera presupuesto de 2000000 celdas')

    @property
    def coordinates(self):return tuple(o+(np.arange(n)+.5)*d for o,n,d in zip(self.origin,self.shape,self.spacing))
    @property
    def cell_volume(self):return math.prod(self.spacing)
    @property
    def upper(self):return tuple(o+n*d for o,n,d in zip(self.origin,self.shape,self.spacing))
    @property
    def points(self):return np.stack(np.meshgrid(*self.coordinates,indexing='ij'),axis=-1).reshape(-1,3)
    def box_grid(self):return CartesianGrid(tuple(n*d for n,d in zip(self.shape,self.spacing)),self.shape)


@dataclass
class Voxelization:
    grid:VoxelGrid
    vertida_id:np.ndarray
    guid_by_id:dict
    reference_volumes:dict
    boundary_ties:int=0

    def __post_init__(self):
        if self.vertida_id.shape!=self.grid.shape or not np.issubdtype(self.vertida_id.dtype,np.integer) or np.any(self.vertida_id<0):raise ValueError('Etiquetas enteras no negativas con forma de grilla')
        if set(map(int,np.unique(self.vertida_id)))-{0}-set(self.guid_by_id):raise ValueError('VertidaID desconocido')
        if set(self.guid_by_id)!=set(self.reference_volumes) or len(set(self.guid_by_id.values()))!=len(self.guid_by_id):raise ValueError('Correspondencia GUID/ID no única')
        if any(not math.isfinite(v) or v<=0 for v in self.reference_volumes.values()):raise ValueError('Volúmenes de referencia positivos')

    @property
    def occupation_mask(self):return self.vertida_id>0

    def report(self):
        rows=[]
        for identifier,guid in sorted(self.guid_by_id.items()):
            count=int(np.count_nonzero(self.vertida_id==identifier));v=count*self.grid.cell_volume;ref=self.reference_volumes[identifier]
            rows.append(dict(vertida_id=identifier,guid=guid,cells=count,volume_voxel_m3=v,
                             volume_reference_m3=ref,absolute_error_m3=abs(v-ref),signed_error_m3=v-ref,relative_error=abs(v-ref)/ref))
        total=sum(r['volume_voxel_m3'] for r in rows);ref=sum(self.reference_volumes.values())
        return dict(origin_m=self.grid.origin,spacing_m=self.grid.spacing,shape=self.grid.shape,
                    upper_m=self.grid.upper,axes='XYZ; array[i,j,k]; C-order',cell_volume_m3=self.grid.cell_volume,
                    grid_cells=math.prod(self.grid.shape),occupied_cells=int(self.occupation_mask.sum()),
                    volume_voxel_m3=total,volume_reference_mesh_m3=ref,absolute_error_m3=abs(total-ref),
                    relative_error=abs(total-ref)/ref,signed_error_m3=total-ref,
                    sum_absolute_pour_errors_m3=sum(r['absolute_error_m3'] for r in rows),
                    max_pour_relative_error=max((r['relative_error'] for r in rows),default=0.),
                    boundary_ties=self.boundary_ties,by_pour=rows)


def voxelize(solids,spacing=.3,*,margin=0.):
    if not solids:raise ValueError('No hay sólidos')
    if len({s.pour_id for s in solids})!=len(solids) or any(s.pour_id<=0 or s.pour_id>65535 for s in solids):raise ValueError('VertidaID no único o fuera de uint16')
    ds=np.broadcast_to(np.asarray(spacing,dtype=float),(3,)).copy()
    if not np.isfinite(ds).all() or np.any(ds<=0) or not math.isfinite(margin) or margin<0:raise ValueError('Resolución positiva y margen no negativo')
    low=np.min([s.mesh.low for s in solids],axis=0)-margin;high=np.max([s.mesh.high for s in solids],axis=0)+margin
    shape=tuple(int(n) for n in np.ceil((high-low)/ds))
    grid=VoxelGrid(tuple(low),tuple(ds),shape);points=grid.points
    ids=np.zeros(len(points),dtype=np.uint16);state=np.full(len(points),-1,dtype=np.int8);ties=0
    for solid in sorted(solids,key=lambda s:s.pour_id):
        candidate=np.flatnonzero(np.all((points>=solid.mesh.low-solid.mesh.tolerance)&(points<=solid.mesh.high+solid.mesh.tolerance),axis=1))
        current=solid.mesh.classify(points[candidate]);inside=current>=0
        ix=candidate[inside];kind=current[inside]
        overlap=(ids[ix]>0)&(state[ix]==1)&(kind==1)
        if np.any(overlap):raise ValueError('Solapamiento interior entre vertidas en centros')
        ties+=int(np.count_nonzero((ids[ix]>0)&(state[ix]==0)&(kind==0)))
        replace=(ids[ix]==0)|((state[ix]==0)&(kind==1))
        ids[ix[replace]]=solid.pour_id;state[ix[replace]]=kind[replace]
    ids=ids.reshape(shape)
    if any(not np.any(ids==s.pour_id) for s in solids):raise ValueError('Una vertida sin centros: reducir resolución, especialmente dz')
    return Voxelization(grid,ids,{s.pour_id:s.guid for s in solids},{s.pour_id:s.mesh.volume for s in solids},ties)
