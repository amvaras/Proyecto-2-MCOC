import numpy as np
from mcoc_p2.e07.geometry import ClosedMesh
from mcoc_p2.e07.ifc import PourSolid
from mcoc_p2.e07.voxel import VoxelGrid,Voxelization


def cube(low=(0,0,0),high=(1,1,1)):
    v=np.array([(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)],float)
    v=np.asarray(low)+v*(np.asarray(high)-low)
    f=np.array([(0,2,1),(0,3,2),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)])
    return ClosedMesh(v,f)


def solid(mesh,pid=1):return PourSolid(pid,'synthetic-guid-'+str(pid),'synthetic',mesh,{},np.eye(4))


def labelled(ids,spacing=(1.,1.,1.)):
    ids=np.array(ids,dtype=np.uint16)
    pids=set(map(int,np.unique(ids)))-{0}
    grid=VoxelGrid((0.,0.,0.),spacing,ids.shape)
    return Voxelization(grid,ids,{p:'guid-'+str(p) for p in pids},
                        {p:float(np.count_nonzero(ids==p))*grid.cell_volume for p in pids})
