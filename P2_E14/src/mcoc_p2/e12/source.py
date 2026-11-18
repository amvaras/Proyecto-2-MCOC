"""Fuentes experimentales W/m³; interpolación lineal e integral exacta por tramo."""
from pathlib import Path
import hashlib
import numpy as np
from ..e07.hydration import AdiabaticCurve

NAMES=('M1_SS','M2_SS','M3_SS','M4_SS','M1_22A','M2_22A','M3_22A','M4_22A')
NOMINAL_MJ=(88.1,95.7,94.1,100.2,61.2,82.4,73.3,73.6)

def read_sources(path):
    path=Path(path);raw=path.read_bytes();header=raw.decode('utf8').splitlines()[:28]
    if not any('Q in watts per cubic metre' in line for line in header):raise ValueError('Unidades de fuente no reconocidas')
    data=np.loadtxt(path)
    if data.ndim!=2 or data.shape[1]!=9 or len(data)<3:raise ValueError('Se requieren tiempo y ocho fuentes')
    t=data[:,0]*3600
    if not np.isfinite(t).all() or t[0]!=0 or not np.all(np.diff(t)>0):raise ValueError('Tiempo creciente desde cero')
    curves={};report={}
    for i,name in enumerate(NAMES):
        q=data[:,i+1]
        if np.isinf(q).any():raise ValueError('Fuente infinita no admitida')
        valid=np.isfinite(q);n=int(valid.sum())
        if n<2 or not valid[:n].all() or valid[n:].any():raise ValueError('NaN solo al final del registro')
        if name.endswith('_SS') and not valid.all():raise ValueError('SS debe estar completa')
        if np.any(q[:n]<0):raise ValueError('Fuente negativa no admitida')
        energy=float(np.trapezoid(q[:n],t[:n]))
        if abs(energy/1e6-NOMINAL_MJ[i])>.06:raise ValueError('Energía no coincide con nominal redondeado: '+name)
        curves[name]=(t[:n].copy(),q[:n].copy())
        report[name]=dict(campaign='SS' if name.endswith('_SS') else '22A',samples=n,missing_tail=int(len(q)-n),
                         coverage_h=[float(t[0]/3600),float(t[n-1]/3600)],integrated_MJ_m3=energy/1e6,nominal_MJ_m3=NOMINAL_MJ[i],
                         final_W_m3=float(q[n-1]),quality='mayor confianza; RMSE 0.1–0.2 K' if name.endswith('_SS') else 'menor confianza; RMSE ~0.4 K')
    return curves,dict(file=path.name,sha256=hashlib.sha256(raw).hexdigest(),time_units='h convertidas a s',source_units='W/m³',
                       curves=report,time_zero='inicio ventana conservada; registro original +2 h; no se reconstruyen las primeras 2 h',
                       specimen=dict(radius_m=.0375,height_m=.15,rho_kg_m3=2476,cp_J_kgK=1023,cement_kg_m3=350.77,beta_W_m2K=2.5))

def select_representative(curves):
    names=NAMES[:4];times=curves[names[0]][0]
    if any(not np.array_equal(curves[n][0],times) for n in names):raise ValueError('SS debe compartir tiempos')
    scores={n:sum(float(np.trapezoid((curves[n][1]-curves[m][1])**2,times)) for m in names) for n in names}
    return min(names,key=lambda n:(scores[n],n)),scores

class ExperimentalCurve(AdiabaticCurve):
    """Compatible con el integrador vigente: released devuelve J/m³, source W/m³."""
    def __init__(self,times_s,source_W_m3,*,tail='zero',tau_s=86400.,name='experimental'):
        t=np.asarray(times_s,dtype=float).copy();q=np.asarray(source_W_m3,dtype=float).copy()
        if t.ndim!=1 or q.shape!=t.shape or len(t)<2 or not np.isfinite(t).all() or not np.isfinite(q).all() or np.any(q<0) or t[0]!=0 or not np.all(np.diff(t)>0):raise ValueError('Curva experimental inválida')
        if tail not in {'zero','exponential'}:raise ValueError('Cola explícita zero/exponential')
        if tail=='zero' and (q[-1]!=0 or np.max(q[t>=t[-1]-12*3600])>.05):raise ValueError('Cola cero requiere final nulo y últimas 12 h <=0.05 W/m³')
        if isinstance(tau_s,bool) or not isinstance(tau_s,(int,float)) or not np.isfinite(tau_s) or tau_s<=0:raise ValueError('tau positiva finita')
        c=np.r_[0.,np.cumsum(.5*(q[:-1]+q[1:])*np.diff(t))]
        additional=float(q[-1]*tau_s) if tail=='exponential' else 0.
        super().__init__(float(c[-1]+additional),float(t[-1]))
        for key,value in dict(times_s=t,source_W_m3=q,cumulative_J_m3=c,tail=tail,tau_s=float(tau_s),name=name,tail_potential_J_m3=additional).items():object.__setattr__(self,key,value)
        for a in (t,q,c):a.flags.writeable=False
    def source(self,age_s):
        a=np.asarray(age_s,dtype=float)
        if not np.isfinite(a).all():raise ValueError('Edad finita')
        value=np.interp(a,self.times_s,self.source_W_m3,left=0.,right=0.)
        if self.tail=='exponential':value=np.where(a>self.duration_s,self.source_W_m3[-1]*np.exp(-np.maximum(0,a-self.duration_s)/self.tau_s),value)
        return value
    def primitive(self,age_s):
        a=np.asarray(age_s,dtype=float)
        if not np.isfinite(a).all():raise ValueError('Edad finita')
        b=np.clip(a,0,self.duration_s);i=np.clip(np.searchsorted(self.times_s,b,side='right')-1,0,len(self.times_s)-2)
        dx=b-self.times_s[i];slope=(self.source_W_m3[i+1]-self.source_W_m3[i])/(self.times_s[i+1]-self.times_s[i])
        value=self.cumulative_J_m3[i]+self.source_W_m3[i]*dx+.5*slope*dx**2
        if self.tail=='exponential':value+=self.tail_potential_J_m3*(-np.expm1(-np.maximum(0,a-self.duration_s)/self.tau_s))
        return value
    def released(self,age0_s,age1_s):
        if np.any(np.asarray(age1_s)<np.asarray(age0_s)):raise ValueError('Edades deben aumentar')
        return self.primitive(age1_s)-self.primitive(age0_s)
    def degree(self,age_s):return self.primitive(age_s)/self.H_vol_J_m3 if self.H_vol_J_m3 else np.zeros_like(np.asarray(age_s,dtype=float))

def load_curve(path,name='M2_SS',tail='zero',tau_s=86400.):
    curves,report=read_sources(path)
    if name not in curves:raise ValueError('Curva desconocida')
    curve=ExperimentalCurve(*curves[name],tail=tail,tau_s=tau_s,name=name)
    selected,scores=select_representative(curves)
    return curve,{**report,'selected':name,'representative_SS_medoid':selected,'SS_L2_scores_W2_s_m6':scores,
                  'tail_policy':tail,'tail_tau_s':tau_s,'tail_additional_MJ_m3':curve.tail_potential_J_m3/1e6,
                  'selected_total_MJ_m3':curve.H_vol_J_m3/1e6}

