"""Enumeración exacta del modelo discreto; evento OR, nunca producto de marginales."""
import math
import numpy as np
from ..e12.source import NAMES
def weights(values):
    a=np.asarray(values,float)
    if a.ndim!=1 or len(a)==0 or not np.isfinite(a).all() or (a<0).any() or not math.isclose(float(a.sum()),1.,rel_tol=0,abs_tol=1e-12):raise ValueError('Pesos no negativos finitos con suma uno')
    return a
def scenarios(reduction,material_weights=(.2,.2,.2,.2,.05,.05,.05,.05)):
    p=weights(material_weights);q=weights(reduction['weights'])
    if len(p)!=8 or len(q)!=3:raise ValueError('Ocho materiales y tres climas')
    if len(set(reduction['medoids']))!=3 or len(set(reduction['snapshots']))!=3:raise ValueError('No duplicar escenarios climáticos')
    return [dict(id=f'{curve}_m{member:02d}',curve=curve,campaign='SS' if i<4 else '22A',member=member,snapshot=snapshot,
        material_weight=float(p[i]),climate_weight=float(q[k]),weight=float(p[i]*q[k]),tau_h=24.)
        for i,curve in enumerate(NAMES) for k,(member,snapshot) in enumerate(zip(reduction['medoids'],reduction['snapshots']))]
def probability(rows,scenario_weights=None):
    if not rows:raise ValueError('Escenarios vacíos')
    w=weights([r['weight'] for r in rows] if scenario_weights is None else scenario_weights)
    if len(w)!=len(rows):raise ValueError('Un peso por escenario')
    t=np.array([r['Tmax_C'] for r in rows]);d=np.array([r['delta_C'] for r in rows])
    if not np.isfinite(t).all() or not np.isfinite(d).all():raise ValueError('Métricas finitas')
    ft=t>70;fd=d>20;joint=ft|fd
    return dict(P_T=float(w[ft].sum()),P_delta=float(w[fd].sum()),P_joint=float(w[joint].sum()),
        failures=int(joint.sum()),scenarios=len(rows),feasible=bool(w[joint].sum()<=.05+1e-14),
        Tmax_C=float(t.max()),delta_C=float(d.max()),meaning='Exacto para los pesos hipotéticos del modelo discreto; sin intervalo Monte Carlo ni garantía de confiabilidad de obra')
def select(plans,rows):
    summaries=[]
    for p in plans:
        selected=[r for r in rows if r['plan']==p['id']]
        summaries.append(dict(plan=p['id'],D_h=p['D_h'],**probability(selected)))
    feasible=sorted((r for r in summaries if r['feasible']),key=lambda r:(r['D_h'],r['P_joint'],r['plan']))
    return summaries,feasible[0] if feasible else None
