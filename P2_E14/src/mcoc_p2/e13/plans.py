"""Duración física, un recurso y activación térmica lumped al inicio de cada vertida."""
from copy import deepcopy
import math
from ..e08.inputs import number
def make_plan(identifier,volumes,rate_m3_h=50.,*,wait_h=.5,single=False,baseline=False,initial_C=12.,protected=True):
    number(rate_m3_h,'Capacidad',0,True);number(wait_h,'Espera',0)
    durations=[v/rate_m3_h for v in volumes];starts=[0.]
    for j in range(1,len(volumes)):starts.append(starts[-1]+durations[j-1]+wait_h)
    if baseline:starts=[0.,5.,10.,15.,20.]
    if single:starts=[0.]*len(volumes)
    plan=dict(id=identifier,label=identifier,partition='single' if single else 'five',rate_m3_h=rate_m3_h,
        start_h=starts,duration_h=durations,initial_C=[initial_C]*len(volumes),wait_min_h=.5,
        protected=protected,remove_at_h=240. if protected else 18.25,activation_rule='start',
        resource_assumption='Una bomba 50 m³/h y suministro continuo con relevos; capacidad hipotética, no dato docente. Equipo de enfriamiento disponible para todos; sin optimizar costes.',
        transition_assumption='0.5 h mínimo de cambio entre capas, hipótesis logística; no demuestra resistencia de junta ni factibilidad de obra')
    if baseline:plan['initial_C']=[18.,19.,20.,21.,22.]
    if single:plan['duration_h']=[sum(volumes)/rate_m3_h];plan['physical_start_h']=[0.]
    return validate_plan(plan,volumes)
def validate_plan(plan,volumes):
    p=deepcopy(plan)
    if set(p)-{'id','label','partition','rate_m3_h','start_h','duration_h','initial_C','wait_min_h','protected','remove_at_h','activation_rule','resource_assumption','transition_assumption','physical_start_h','D_h'}:raise ValueError('Claves de plan desconocidas')
    if not isinstance(p['id'],str) or not p['id'] or len(p['id'])>60:raise ValueError('ID de plan')
    if p['partition'] not in {'single','five'} or p['activation_rule'] not in {'start','midpoint','finish'}:raise ValueError('Partición/regla no admitida')
    r=number(p['rate_m3_h'],'Capacidad',0,True);number(p['wait_min_h'],'Espera mínima',0);number(p['remove_at_h'],'Retiro',0)
    if type(p['protected'])is not bool:raise ValueError('Protección booleana')
    for name in ('start_h','initial_C'):
        if len(p[name])!=5:raise ValueError('Cinco regiones IFC')
    for x in p['start_h']:number(x,'Inicio',0)
    for x in p['initial_C']:number(x,'Temperatura',-273.15,True)
    if p['partition']=='single':
        if len(set(p['start_h']))!=1 or len(set(p['initial_C']))!=1:raise ValueError('Vertida única exige edad y temperatura comunes')
        start=p['start_h'][0];expected=[sum(volumes)/r];p['physical_start_h']=[start]
        p['D_h']=start+expected[0]
    else:
        expected=[v/r for v in volumes]
        if any(p['start_h'][j]+expected[j]+p['wait_min_h']>p['start_h'][j+1]+1e-10 for j in range(4)):raise ValueError('Solapamiento/espera insuficiente para una bomba')
        p['D_h']=max(s+d for s,d in zip(p['start_h'],expected))
    if len(p['duration_h'])!=len(expected) or any(not math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-12) for a,b in zip(p['duration_h'],expected)):raise ValueError('Duración debe ser V/r, sin ignorar colocación física')
    return p
def family(volumes):
    return [make_plan('unica',volumes,single=True,initial_C=20,protected=False),
            make_plan('E12_referencia',volumes,baseline=True,protected=False),
            make_plan('protegido_rapido',volumes,wait_h=.5),make_plan('propuesto_6h',volumes,wait_h=6),make_plan('protegido_lento_12h',volumes,wait_h=12)]
def thermal_config(base,plan,scenario,*,spacing=None,horizon_h=408,max_step_s=900):
    c=deepcopy(base);p=c['physics'];p.update(t_end_s=horizon_h*3600,max_step_s=max_step_s,save_interval_s=12*3600)
    if spacing is not None:p['spacing_m']=list(spacing)
    factor={'start':0.,'midpoint':.5,'finish':1.}[plan['activation_rule']]
    durations=plan['duration_h']*5 if plan['partition']=='single' else plan['duration_h']
    p['events']=[dict(pour_id=j+1,activation_s=(plan['start_h'][j]+factor*durations[j])*3600,initial_C=plan['initial_C'][j]) for j in range(5)]
    c['experimental_source'].update(curve=scenario['curve'],tail='exponential',tau_s=scenario.get('tau_h',24)*3600)
    c['snapshot']=scenario['snapshot'];c['simulation_start_utc']='2026-11-19T11:00:00Z' # 08:00 Chile UTC−03.
    if plan['protected']:
        c['environment']['formwork']['orientations']=['x-','x+','y-','y+','z+']
    c['environment']['formwork']['remove_at_s']=plan['remove_at_h']*3600
    return c
