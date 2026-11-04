"""Pertenencia a mallas triangulares cerradas, sin depender de IFC."""
from collections import Counter
import numpy as np


class ClosedMesh:
    def __init__(self,vertices,triangles):
        v=np.asarray(vertices,dtype=float);f=np.asarray(triangles)
        if v.ndim!=2 or v.shape[1]!=3 or len(v)<4 or not np.isfinite(v).all():raise ValueError('Vértices finitos Nx3')
        if f.ndim!=2 or f.shape[1]!=3 or not np.issubdtype(f.dtype,np.integer) or len(f)<4:raise ValueError('Triángulos enteros Mx3')
        if f.min()<0 or f.max()>=len(v):raise ValueError('Índices fuera de malla')
        if len(np.unique(np.sort(f,axis=1),axis=0))!=len(f):raise ValueError('Triángulos duplicados')
        if set(f.ravel())!=set(range(len(v))):raise ValueError('Vértices sin uso')
        directed=Counter((int(a),int(b)) for face in f for a,b in zip(face,np.roll(face,-1)))
        if any(directed[(a,b)]!=1 or directed[(b,a)]!=1 for a,b in directed):raise ValueError('Malla abierta, no manifold u orientación inconsistente')
        adjacent={i:set() for i in range(len(v))}
        for a,b in directed:adjacent[a].add(b)
        pending=[0];visited=set()
        while pending:
            a=pending.pop()
            if a not in visited:visited.add(a);pending.extend(adjacent[a]-visited)
        if len(visited)!=len(v):raise ValueError('Malla desconectada; separar sólidos')
        self.low=v.min(axis=0);self.high=v.max(axis=0)
        self.tolerance=max(1e-10,1e-9*float(np.max(self.high-self.low)))
        tri=v[f];norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
        if np.any(np.linalg.norm(norm,axis=1)<=self.tolerance**2):raise ValueError('Triángulo degenerado')
        # Trasladar antes de la suma de volumen mejora estabilidad lejos del origen.
        centered=tri-v.mean(axis=0)
        volume=float(np.einsum('ij,ij->i',centered[:,0],np.cross(centered[:,1],centered[:,2])).sum()/6)
        if abs(volume)<=self.tolerance**3:raise ValueError('Volumen nulo')
        self.orientation_reversed=volume<0
        if volume<0:f=f[:,::-1]
        self.vertices=v.copy();self.triangles=f.astype(np.int64,copy=True);self.volume=abs(volume)
        self.tri=v[self.triangles]
        normals=np.cross(self.tri[:,1]-self.tri[:,0],self.tri[:,2]-self.tri[:,0])
        normals/=np.linalg.norm(normals,axis=1)[:,None]
        offsets=np.einsum('ij,ij->i',normals,self.tri[:,0])
        # Solo acelerar por semiespacios si TODOS los vértices satisfacen TODOS los planos.
        self.convex=bool(np.all(v@normals.T-offsets<=self.tolerance))
        _,unique=np.unique(np.round(np.column_stack((normals,offsets)),12),axis=0,return_index=True)
        self.normals=normals[unique];self.offsets=offsets[unique]

    def classify(self,points,*,method='auto'):
        """-1 exterior, 0 frontera incluida, +1 interior. Aristas/vértices son frontera.

        Convexos: máximo de distancias firmadas a planos triangulares.
        General: ángulo sólido orientado (sin rayos), con prueba de frontera previa.
        Presupone una superficie simple cerrada sin auto-intersecciones.
        """
        points=np.asarray(points,dtype=float)
        if points.ndim!=2 or points.shape[1]!=3 or not np.isfinite(points).all():raise ValueError('Puntos finitos Nx3')
        if method not in ('auto','winding'):raise ValueError('Método desconocido')
        answer=np.full(len(points),-1,dtype=np.int8)
        candidates=np.flatnonzero(np.all((points>=self.low-self.tolerance)&(points<=self.high+self.tolerance),axis=1))
        for start in range(0,len(candidates),256):
            ix=candidates[start:start+256];p=points[ix]
            if self.convex and method=='auto':
                maximum=(p@self.normals.T-self.offsets).max(axis=1)
                answer[ix]=np.where(maximum < -self.tolerance,1,np.where(maximum<=self.tolerance,0,-1))
                continue
            boundary=np.zeros(len(p),dtype=bool);omega=np.zeros(len(p))
            for tr in self.tri:
                edge1=tr[1]-tr[0];edge2=tr[2]-tr[0];normal=np.cross(edge1,edge2);normal/=np.linalg.norm(normal)
                distance=(p-tr[0])@normal;project=p-distance[:,None]*normal
                u=project-tr[0];d00=edge1@edge1;d01=edge1@edge2;d11=edge2@edge2
                d20=u@edge1;d21=u@edge2;den=d00*d11-d01*d01
                b=(d11*d20-d01*d21)/den;c=(d00*d21-d01*d20)/den
                btol=self.tolerance/max(np.linalg.norm(edge1),np.linalg.norm(edge2))
                boundary |= (abs(distance)<=self.tolerance)&(b>=-btol)&(c>=-btol)&(b+c<=1+btol)
                a,bv,cv=(tr[i]-p for i in range(3));la=np.linalg.norm(a,axis=1);lb=np.linalg.norm(bv,axis=1);lc=np.linalg.norm(cv,axis=1)
                det=np.einsum('ij,ij->i',a,np.cross(bv,cv))
                denominator=la*lb*lc+np.einsum('ij,ij->i',a,bv)*lc+np.einsum('ij,ij->i',bv,cv)*la+np.einsum('ij,ij->i',cv,a)*lb
                omega+=2*np.arctan2(det,denominator)
            answer[ix]=np.where(boundary,0,np.where(abs(omega)>2*np.pi,1,-1))
        return answer
