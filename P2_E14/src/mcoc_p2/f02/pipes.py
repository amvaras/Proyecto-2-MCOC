"""Temporary experiment: axially advected water and exact segment heat exchange."""
from dataclasses import dataclass
from math import log, pi, sqrt
import numpy as np

@dataclass(frozen=True)
class Design:
    layers: tuple
    pitch: float
    inlet: float
    flow_ls: float
    start_h: float
    stop_h: float
    cap_kW: float
    radius: float
    outer_m: float = .032
    inner_m: float = .026
    clearance_m: float = .18
    conductivity_pipe: float = .4

class Network:
    cp = 4182. # J/(kg K), near 20 C
    rho = 998. # kg/m3
    mu = .001002 # Pa s
    kw = .598 # W/(m K)
    concrete_k = 2.

    def __init__(self, vox, solids, design):
        self.design = design
        self.circuits=[]
        starts=[]; cell_lists=[]; lengths=[]
        spacing=np.array(vox.grid.spacing)
        origin=np.array(vox.grid.origin)
        for pid,z in design.layers:
            mesh=next(s.mesh for s in solids if s.pour_id==pid)
            assert mesh.convex
            # Exact convex half-space intersection with an inset for routing clearance.
            for j in range(-int(design.radius/design.pitch),int(design.radius/design.pitch)+1):
                y=j*design.pitch
                if y*y>=design.radius**2:continue
                xmax=sqrt(design.radius**2-y*y)
                mins=[-xmax];maxs=[xmax]
                for n,b in zip(mesh.normals,mesh.offsets):
                    rhs=b-design.clearance_m-n[1]*y-n[2]*z
                    if n[0] > 1e-10:maxs.append(rhs/n[0])
                    elif n[0] < -1e-10:mins.append(rhs/n[0])
                    elif rhs<0:break
                else:
                    x0,x1=max(mins),min(maxs)
                    if x1-x0<2.:continue
                    transverse=np.floor((np.array([y,z])-origin[1:])/spacing[1:]).astype(int)
                    ix=np.arange(vox.grid.shape[0])
                    left=origin[0]+ix*spacing[0]
                    overlap=np.maximum(0.,np.minimum(left+spacing[0],x1)-np.maximum(left,x0))
                    select=np.flatnonzero(overlap>1e-10)
                    if len(self.circuits)%2:select=select[::-1]
                    coords=(select,np.full(len(select),transverse[0]),np.full(len(select),transverse[1]))
                    gids=vox.vertida_id[coords]
                    if not np.all(gids==pid):
                        raise ValueError(f'Pipe not resolved in the correct pour: {pid,z,y,x0,x1,gids.tolist()}')
                    segment=overlap[select]
                    assert abs(segment.sum()-(x1-x0))<1e-8
                    self.circuits.append(dict(pour=pid,z_m=z,y_m=y,x_low_m=x0,x_high_m=x1,length_m=x1-x0,flow_direction=(-1 if len(self.circuits)%2 else 1)))
                    starts.append(pid)
                    cell_lists.append(np.ravel_multi_index(coords,vox.grid.shape))
                    lengths.append(segment)
        n=len(cell_lists);m=max(map(len,cell_lists))
        self.indices=np.zeros((n,m),dtype=int);ell=np.zeros((n,m))
        for j,(idx,seg) in enumerate(zip(cell_lists,lengths)):
            self.indices[j,:len(idx)]=idx;ell[j,:len(seg)]=seg
        self.mask=ell>0
        self.pid=np.array(starts)
        self.mass_flow=design.flow_ls*self.rho/1000
        diameter=design.inner_m
        velocity=(design.flow_ls/1000)/(pi*diameter**2/4)
        self.re=self.rho*velocity*diameter/self.mu
        assert 3000 < self.re < 5e6
        pr=self.cp*self.mu/self.kw
        self.friction=(.79*log(self.re)-1.64)**-2
        nu=(self.friction/8)*(self.re-1000)*pr/(1+12.7*sqrt(self.friction/8)*(pr**(2/3)-1))
        h=nu*self.kw/diameter
        self.h_water=h
        self.wall=log(design.outer_m/diameter)/(2*pi*design.conductivity_pipe)
        self.inside=1/(h*pi*diameter)
        # Equivalent cell radius approximates local spreading into the embedded tube.
        outer_radius=design.outer_m/2
        re_cell=sqrt(spacing[1]*spacing[2]/pi)
        self.spread=log(re_cell/outer_radius)/(2*pi*self.concrete_k)
        self.r_per_m=self.wall+self.inside+self.spread
        self.mass_cp=self.mass_flow*self.cp
        self.peak_kW=0.;self.max_return=design.inlet
        self.max_flow_ls=0.;self.pipe_cells_min=np.inf
        self.cache_key=None
        self.flow_velocity=velocity
        self.longest_straight_pressure_Pa=self.friction*max(c['length_m'] for c in self.circuits)/diameter*self.rho*velocity**2/2
        ua=ell/self.r_per_m
        a=np.exp(-ua/self.mass_cp)
        self.heat_conductance=self.mass_cp*(-np.expm1(-ua/self.mass_cp))
        self.product_in=np.concatenate((np.ones((n,1)),np.cumprod(a,axis=1)[:,:-1]),axis=1)
        self.product_out=np.cumprod(a,axis=1)
        self.recurrence=(1-a)/self.product_out

    def enabled(self,t):
        return self.design.start_h*3600 <= t < self.design.stop_h*3600

    def limit(self,assembly,t):
        if not self.enabled(t):
            return assembly.stable_dt
        if assembly is not self.cache_key:
            flat=assembly.active.ravel()
            self.live=np.any(flat[self.indices]&self.mask,axis=1)
            assert np.all((flat[self.indices] | ~self.mask)[self.live])
            self.cache_key=assembly
            idx=self.indices[self.live]
            self.cool_diagonal=np.bincount(idx.ravel(),weights=self.heat_conductance[self.live].ravel(),
                minlength=flat.size).reshape(assembly.active.shape)
        # Bound at time of solve: the self derivative is at most G for each segment.
        location=self.cool_diagonal>0
        if not location.any():return assembly.stable_dt
        d=assembly._internal_diagonal.copy()
        np.add.at(d,assembly.face_indices,assembly.face_g)
        return min(assembly.stable_dt,float(np.min(assembly.capacity[location]/(d+self.cool_diagonal)[location])))

    def apply(self,net,T,t):
        if not self.enabled(t) or not self.live.any():return 0.
        idx=self.indices[self.live]
        valid=self.mask[self.live]
        concrete=np.where(valid,T.ravel()[idx],self.design.inlet)
        cum=np.cumsum(concrete*self.recurrence[self.live],axis=1)
        temps_in=self.product_in[self.live]*(self.design.inlet+
                 np.concatenate((np.zeros((len(idx),1)),cum[:,:-1]),axis=1))
        return_full=self.product_out[self.live,-1]*(self.design.inlet+cum[:,-1])
        q=self.heat_conductance[self.live]*(concrete-temps_in)
        # Use whole-circuit bypass if water would heat concrete on net.
        forward=return_full>self.design.inlet
        q[~forward]=0.
        gross=float(q.sum())
        cap=1000*self.design.cap_kW
        duty=min(1.,cap/max(gross,1e-30))
        q*=duty
        water=float(((return_full[forward]-self.design.inlet)*self.mass_cp).sum()*duty)
        removed=float(q.sum())
        if not np.isclose(water,removed,atol=1e-6,rtol=1e-10):
            raise ArithmeticError('Circuit enthalpy does not match mesh sink')
        np.add.at(net.ravel(),idx.ravel(),-q.ravel())
        self.peak_kW=max(self.peak_kW,removed/1000)
        self.max_flow_ls=max(self.max_flow_ls,float(forward.sum())*self.design.flow_ls)
        if forward.any():
            self.max_return=max(self.max_return,float(return_full[forward].max()))
            self.pipe_cells_min=min(self.pipe_cells_min,float(concrete[forward][valid[forward]].min()))
        return removed
