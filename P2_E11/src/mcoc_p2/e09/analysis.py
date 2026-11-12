"""Sondas reproducibles y estadísticas sobre el campo activo, sin alterar física."""
import numpy as np
from .. import Robin,Dirichlet,Neumann
from ..e07.faces import exposed_faces


def select_probes(voxels,core_target=(0.,0.,1.65)):
    grid=voxels.grid
    indices=np.argwhere(voxels.occupation_mask)
    xyz=np.array(grid.origin)+(indices+.5)*np.array(grid.spacing)
    labels=voxels.vertida_id[tuple(indices.T)]
    if len(core_target)!=3 or not np.isfinite(core_target).all():raise ValueError('Sonda núcleo: tres coordenadas finitas')
    def cell(name,target,selected=None):
        options=np.arange(len(indices)) if selected is None else np.flatnonzero(selected)
        chosen=options[np.argmin(np.sum((xyz[options]-target)**2,axis=1))]
        key=tuple(indices[chosen]);point=xyz[chosen]
        return dict(name=name,index=list(map(int,key)),coordinate_m=point.tolist(),vertida_id=int(labels[chosen]),
                    kind='cell_center',target_m=list(map(float,target)))
    probes=[cell('nucleo',np.asarray(core_target))]
    core=np.array(probes[0]['coordinate_m'])
    faces=exposed_faces(voxels);centers=np.array(grid.origin)+(faces.indices+.5)*np.array(grid.spacing)
    centers[np.arange(len(centers)),faces.axis]+=faces.sign*np.array(grid.spacing)[faces.axis]/2
    def face(name,select,target):
        options=np.flatnonzero(select)
        if not len(options):raise ValueError('No existe superficie requerida: '+name)
        chosen=options[np.argmin(np.sum((centers[options]-target)**2,axis=1))]
        key=tuple(faces.indices[chosen]);direction='xyz'[faces.axis[chosen]]+('+' if faces.sign[chosen]>0 else '-')
        return dict(name=name,index=list(map(int,key)),coordinate_m=centers[chosen].tolist(),
                    cell_center_m=(np.array(grid.origin)+(np.array(key)+.5)*np.array(grid.spacing)).tolist(),
                    vertida_id=int(faces.pour_id[chosen]),kind='reconstructed_face',face=direction,
                    half_cell_m=grid.spacing[faces.axis[chosen]]/2,target_m=list(map(float,target)))
    probes.append(face('superficie_superior',(faces.axis==2)&(faces.sign==1),
                       np.array([core[0],core[1],xyz[:,2].max()+grid.spacing[2]/2])))
    probes.append(face('superficie_lateral',(faces.axis==0)&(faces.sign==1),
                       np.array([xyz[:,0].max()+grid.spacing[0]/2,core[1],core[2]])))
    probes.append(cell('cerca_base',np.array([core[0],core[1],xyz[:,2].min()])))
    for pid in sorted(voxels.guid_by_id):
        select=labels==pid
        probes.append(cell('centro_vertida_'+str(pid),xyz[select].mean(axis=0),select))
    return probes


def probe_values(temperature,active,probes,materials,boundaries):
    values=np.zeros(len(probes));valid=np.zeros(len(probes),dtype=bool)
    for i,p in enumerate(probes):
        key=tuple(p['index'])
        if not active[key]:continue
        tc=float(temperature[key]);valid[i]=True;values[i]=tc
        if p['kind']!='reconstructed_face':continue
        # Si todavía existe otra celda activa frente a la cara elegida,
        # la cara geométrica final no sería una superficie libre temporal.
        axis='xyz'.index(p['face'][0]);sign=1 if p['face'][1]=='+' else -1
        neighbor=list(key);neighbor[axis]+=sign
        if all(0<=j<n for j,n in zip(neighbor,active.shape)) and active[tuple(neighbor)]:
            valid[i]=False;values[i]=0.;continue
        boundary=boundaries[p['face']];resistance=p['half_cell_m']/materials[p['vertida_id']].k
        if isinstance(boundary,Robin):
            values[i]=(tc+boundary.h*resistance*boundary.ambient)/(1+boundary.h*resistance)
        elif isinstance(boundary,Dirichlet):values[i]=boundary.temperature
        elif isinstance(boundary,Neumann):values[i]=tc-boundary.outward_flux*resistance
    return values,valid


class FieldRecorder:
    def __init__(self,voxels,events,boundaries,core_target=(0.,0.,1.65)):
        self.voxels=voxels;self.probes=select_probes(voxels,core_target)
        self.materials={e.pour_id:e.material for e in events};self.boundaries=boundaries
        self.rows=[];self.values=[];self.valid=[]
        self.peak=None

    def __call__(self,time_s,temperature,active):
        values=temperature[active]
        if not np.isfinite(values).all():raise ValueError('Campo activo no finito')
        low,high,mean=(float(values.min()),float(values.max()),float(values.mean())) if values.size else (0.,0.,0.)
        pv,valid=probe_values(temperature,active,self.probes,self.materials,self.boundaries)
        self.rows.append([time_s,low,high,mean,int(values.size)])
        self.values.append(pv);self.valid.append(valid)
        if values.size and (self.peak is None or high>self.peak['temperature_C']):
            flat=int(np.argmax(np.where(active,temperature,-np.inf)))
            index=np.unravel_index(flat,active.shape)
            self.peak=dict(temperature_C=high,time_h=time_s/3600,index=list(map(int,index)),
                           coordinate_m=(np.array(self.voxels.grid.origin)+(np.array(index)+.5)*np.array(self.voxels.grid.spacing)).tolist(),
                           vertida_id=int(self.voxels.vertida_id[index]))

    def arrays(self):
        rows=np.array(self.rows)
        return dict(time_s=rows[:,0],Tmin_C=rows[:,1],Tmax_C=rows[:,2],Tmean_C=rows[:,3],
                    active_count=rows[:,4].astype(int),probe_temperature_C=np.array(self.values),
                    probe_valid=np.array(self.valid,dtype=bool))

    def summary(self):
        a=self.arrays();values=a['probe_temperature_C'];valid=a['probe_valid'];points=[]
        for j,p in enumerate(self.probes):
            options=np.flatnonzero(valid[:,j]);peak=options[np.argmax(values[options,j])] if len(options) else None
            points.append({**p,'final_C':float(values[-1,j]) if valid[-1,j] else None,
                           'maximum_C':float(values[peak,j]) if peak is not None else None,
                           'maximum_time_h':float(a['time_s'][peak]/3600) if peak is not None else None})
        both=valid[:,0]&valid[:,1];delta=values[:,0]-values[:,1]
        options=np.flatnonzero(both);j=options[np.argmax(delta[options])] if len(options) else None
        return dict(peak=self.peak,probes=points,
                    center_top_difference=dict(maximum_C=float(delta[j]) if j is not None else None,
                        time_h=float(a['time_s'][j]/3600) if j is not None else None,
                        final_C=float(delta[-1]) if both[-1] else None,
                        valid_from_h=float(a['time_s'][options[0]]/3600) if len(options) else None,
                        definition='nucleo - superficie_superior reconstruida por media celda y condición Robin; solo si ambas sondas existen'),
                    max_at_integration_steps=True)
