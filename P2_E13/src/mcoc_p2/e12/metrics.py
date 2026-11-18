"""Métricas globales en todos los pasos y reconstrucción declarada de S25."""
import numpy as np
from ..e11.pipeline import Recorder
from ..e07.coupling import MaskedAssembly

def surface_values(assembly,T,depth_m=.025):
    faces=assembly.faces
    half=np.array(assembly.voxels.grid.spacing)[faces.axis]/2
    if np.any(depth_m>half):raise ValueError('La reconstrucción requiere profundidad <= media celda')
    cell=T[assembly.face_indices];k=assembly.k[assembly.face_indices]
    q=(assembly.face_g*(cell-assembly.reservoir)+assembly.prescribed)/faces.areas
    face=cell-q*half/k
    near=cell-q*(half-depth_m)/k
    centers=np.array(assembly.voxels.grid.origin)+(faces.indices+.5)*np.array(assembly.voxels.grid.spacing)
    face_xyz=centers.copy();face_xyz[np.arange(len(half)),faces.axis]+=faces.sign*half
    near_xyz=face_xyz.copy();near_xyz[np.arange(len(half)),faces.axis]-=faces.sign*depth_m
    return face,near,cell,near_xyz,face_xyz,q

def point(voxels,index):
    index=np.asarray(index)
    return dict(index=index.astype(int).tolist(),coordinate_m=(np.array(voxels.grid.origin)+(index+.5)*np.array(voxels.grid.spacing)).tolist(),vertida_id=int(voxels.vertida_id[tuple(index)]),active=True)

class GlobalRecorder(Recorder):
    def __init__(self,voxels,events,environment,target,*,capture_all=False,capture_times=(),depth_m=.025):
        super().__init__(voxels,events,environment,target)
        self.events=events;self.capture_all=capture_all;self.capture_times=set(capture_times);self.depth_m=depth_m
        self.left_times={e.activation_s for e in events if e.activation_s>0}|{environment.formwork.remove_at_s}
        self.fields=[];self.captured={};self.extra=[];self.delta_peak=None;self.peak_field=None;self.delta_field=None
    def __call__(self,t,T,active):
        # El integrador entrega T justo después de activar, sin alterar T de
        # las celdas anteriores. Reconstruir también el límite izquierdo de
        # sus caras y del desmolde: S25 puede cambiar instantáneamente.
        if t>0 and t in self.left_times:
            before=np.isin(self.voxels.vertida_id,[e.pour_id for e in self.events if e.activation_s<t])
            self.__call__(float(np.nextafter(t,-np.inf)),T,before)
        super().__call__(t,T,active);a=self.assembly
        face,near,cell,near_xyz,face_xyz,q=surface_values(a,T,self.depth_m)
        vals=T[active];maximum=float(vals.max());j=int(np.argmin(near));delta=maximum-float(near[j])
        ground=(a.faces.axis==2)&(a.faces.sign==-1)&(a.faces.indices[:,2]==self.environment.base_index)
        self.extra.append([float(near.min()),float(face.min()),float(cell.min()),delta,
                           float(np.sum(q[~ground]*a.faces.areas[~ground])),float(np.sum(q[ground]*a.faces.areas[ground])),
                           sum(float(e.hydration.source(t-e.activation_s))*np.count_nonzero(self.voxels.vertida_id==e.pour_id)*self.voxels.grid.cell_volume for e in self.events if t>=e.activation_s)])
        occupied=np.where(active[self.voxels.occupation_mask],T[self.voxels.occupation_mask],0.)
        if self.capture_all:self.fields.append(np.nan_to_num(occupied,nan=0.).copy())
        if t in self.capture_times:self.captured[t]=np.nan_to_num(occupied,nan=0.).copy()
        if self.peak['time_h']==t/3600:
            self.peak_time_s=t;self.peak_field=np.nan_to_num(occupied,nan=0.).copy()
        if self.delta_peak is None or delta>self.delta_peak['value_C']:
            self.delta_time_s=t
            hot=np.unravel_index(np.argmax(np.where(active,T,-np.inf)),T.shape)
            self.delta_peak=dict(value_C=delta,time_h=t/3600,hot=point(self.voxels,hot),
                                 cold=dict(index=a.faces.indices[j].astype(int).tolist(),coordinate_m=near_xyz[j].tolist(),
                                           face_coordinate_m=face_xyz[j].tolist(),vertida_id=int(a.faces.pour_id[j]),
                                           face='xyz'[a.faces.axis[j]]+('+' if a.faces.sign[j]>0 else '-'),
                                           classification=str(a.faces.classification[j]),temperature_C=float(near[j]),kind='reconstrucción lineal a 25 mm'),
                                 hot_temperature_C=maximum,depth_m=self.depth_m,
                                 definition='max Ω activo menos min S25 en el mismo instante; todas las caras expuestas, incluida base y frente a vertida futura')
            self.delta_field=np.nan_to_num(occupied,nan=0.).copy()
    def arrays(self):
        result=super().arrays();x=np.asarray(self.extra)
        for j,key in enumerate(('S25min_C','face_min_C','boundary_cell_min_C','delta25_C','air_power_out_W','soil_power_out_W','hydration_power_W')):result[key]=x[:,j]
        return result

