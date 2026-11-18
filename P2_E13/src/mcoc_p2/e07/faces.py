"""Caras expuestas y contactos; exterior activo y exterior final son distintos."""
from dataclasses import dataclass
import numpy as np


@dataclass
class FaceTable:
    indices:np.ndarray
    axis:np.ndarray
    sign:np.ndarray
    areas:np.ndarray
    normals:np.ndarray
    pour_id:np.ndarray
    classification:np.ndarray

    def report(self):
        return dict(count=len(self.areas),area_m2=float(self.areas.sum()),
                    area_by_orientation_m2={a+s:float(self.areas[(self.axis==i)&(self.sign==n)].sum()) for i,a in enumerate('xyz') for s,n in (('-',-1),('+',1))},
                    area_by_pour_m2={str(int(p)):float(self.areas[self.pour_id==p].sum()) for p in np.unique(self.pour_id)},
                    count_by_class={str(c):int(np.count_nonzero(self.classification==c)) for c in np.unique(self.classification)})


def exposed_faces(voxels,active=None):
    ids=voxels.vertida_id;solid=ids>0
    if active is None:active=solid
    active=np.asarray(active,dtype=bool)
    if active.shape!=ids.shape or np.any(active&~solid):raise ValueError('Máscara activa incompatible con sólido')
    rows=[]
    for axis,dx in enumerate(voxels.grid.spacing):
        for sign in (-1,1):
            neighbor=np.zeros(ids.shape,dtype=bool);future=np.zeros(ids.shape,dtype=bool)
            here=[slice(None)]*3;there=here.copy()
            here[axis]=slice(None,-1) if sign==1 else slice(1,None)
            there[axis]=slice(1,None) if sign==1 else slice(None,-1)
            here,there=tuple(here),tuple(there)
            neighbor[here]=active[there];future[here]=(ids[there]>0)&~active[there]
            index=np.argwhere(active&~neighbor);area=voxels.grid.cell_volume/dx
            for p in index:
                key=tuple(p);normal=np.zeros(3,dtype=int);normal[axis]=sign
                kind='future_pour' if future[key] else ('top' if axis==2 and sign==1 else 'bottom' if axis==2 else 'lateral')
                rows.append((p,axis,sign,area,normal,ids[key],kind))
    if not rows:return FaceTable(np.empty((0,3),int),np.array([],int),np.array([],int),np.array([]),np.empty((0,3),int),np.array([],int),np.array([],dtype='U16'))
    return FaceTable(np.array([r[0] for r in rows]),np.array([r[1] for r in rows]),np.array([r[2] for r in rows]),np.array([r[3] for r in rows]),np.array([r[4] for r in rows]),np.array([r[5] for r in rows]),np.array([r[6] for r in rows]))


def contacts(voxels,active=None,*,different_only=True):
    ids=voxels.vertida_id
    if active is None:active=ids>0
    active=np.asarray(active,dtype=bool)
    if active.shape!=ids.shape or np.any(active&(ids==0)):raise ValueError('Máscara activa inválida')
    first=[];second=[];axes=[];areas=[];labels=[]
    for axis,dx in enumerate(voxels.grid.spacing):
        lo=[slice(None)]*3;hi=lo.copy();lo[axis]=slice(None,-1);hi[axis]=slice(1,None);lo,hi=tuple(lo),tuple(hi)
        valid=active[lo]&active[hi]
        if different_only:valid &= ids[lo]!=ids[hi]
        i=np.argwhere(valid);j=i.copy();j[:,axis]+=1
        first.extend(i);second.extend(j);axes.extend([axis]*len(i));areas.extend([voxels.grid.cell_volume/dx]*len(i))
        labels.extend(zip(ids[tuple(i.T)],ids[tuple(j.T)]))
    return dict(first=np.asarray(first,dtype=int).reshape(-1,3),second=np.asarray(second,dtype=int).reshape(-1,3),
                axis=np.asarray(axes,dtype=int),area_m2=np.asarray(areas),pour_ids=np.asarray(labels,dtype=int).reshape(-1,2))
