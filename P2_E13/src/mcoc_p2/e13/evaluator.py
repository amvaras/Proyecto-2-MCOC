"""Orquestación eficiente; llama al integrador E08 y al observador global E12."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from time import perf_counter
from unittest.mock import patch
import hashlib,json,math
import numpy as np
from ..e07.ifc import read_pours
from ..e07.voxel import voxelize
from ..e08.inputs import events_from_config,validate_config
from ..e08.solver import simulate
from ..e11.pipeline import make_environment,write_json,ROOT
from ..e11.weather import window,iso_utc
from ..e10.weather import utc_time
from ..e12.source import load_curve
from ..e12.metrics import GlobalRecorder
from .plans import validate_plan,thermal_config
from .risk import scenarios,select,weights
from .weather import read

class CaseRecorder(GlobalRecorder):
    def __call__(self,t,T,active):
        if active.any():super().__call__(t,T,active)

class AreaSensitivity:
    """Solo sensibilidad: área aire/suelo reescalada; no es cut-cell ni corrección validada."""
    def __init__(self,environment,air_factor,ground_factor):
        self.environment=environment;self.air_factor=air_factor;self.ground_factor=ground_factor
    def __getattr__(self,name):return getattr(self.environment,name)
    def __call__(self,a,t):
        if not hasattr(a,'e13_original_areas'):a.e13_original_areas=a.faces.areas.copy()
        f=a.faces;ground=(f.axis==2)&(f.sign==-1)&(f.indices[:,2]==self.base_index)
        factor=np.where(ground,self.ground_factor,np.where(f.classification=='future_pour',1.,self.air_factor))
        a.faces.areas=a.e13_original_areas*factor
        return self.environment(a,t)

class Evaluator:
    def __init__(self,base='configs/e12/baseline.json'):
        self.base=read(ROOT/base);self.solids,self.ifc_meta=read_pours(ROOT/self.base['ifc']);self.cache={};self.curves={}
        self.volumes=[s.mesh.volume for s in self.solids]
    def grid(self,spacing):
        key=tuple(spacing)
        if key not in self.cache:self.cache[key]=voxelize(self.solids,spacing,margin=self.base['physics']['margin_m'])
        return self.cache[key]
    def case(self,plan,scenario,*,spacing=(.45,.45,.11),horizon_h=408,max_step_s=900,area_factors=None,capture=False):
        start=perf_counter();plan=validate_plan(plan,self.volumes)
        cfg=thermal_config(self.base,plan,scenario,spacing=spacing,horizon_h=horizon_h,max_step_s=max_step_s)
        vox=self.grid(spacing);spec=cfg['experimental_source'];key=(spec['curve'],spec['tau_s'])
        if key not in self.curves:self.curves[key]=load_curve(ROOT/spec['file'],spec['curve'],spec['tail'],spec['tau_s'])
        curve,report=self.curves[key];cfg['physics']['hydration']=dict(H_vol_J_m3=curve.H_vol_J_m3,duration_s=curve.duration_s)
        cfg['physics']=validate_config(cfg['physics'],self.solids)
        events=[replace(e,hydration=curve) for e in events_from_config(cfg['physics'])]
        weather=window(ROOT/cfg['snapshot'],cfg['simulation_start_utc'],horizon_h*3600)
        env=make_environment(vox,weather,cfg['environment'])
        if area_factors is not None:env=AreaSensitivity(env,*area_factors)
        record=CaseRecorder(vox,events,env,cfg['core_target_m'],capture_all=capture)
        def offline(*args,**kwargs):raise RuntimeError('Red prohibida durante la simulación E13')
        with patch('urllib.request.urlopen',offline),patch('mcoc_p2.e10.weather.urlopen',offline):
            result=simulate(vox,events,t_end_s=horizon_h*3600,max_step_s=max_step_s,save_interval_s=12*3600,safety=.8,energy_reference_C=20,
                observer=record,boundary_update=env,boundary_change_times_s=env.change_times_s)
        a=record.arrays();t=a['time_s'];first=t<=336*3600;late=t>=max(t[0],t[-1]-86400)
        peak={**record.peak,'utc':iso_utc(weather.start+record.peak_time_s),'time_s':record.peak_time_s}
        delta={**record.delta_peak,'utc':iso_utc(weather.start+record.delta_time_s),'time_s':record.delta_time_s}
        row=dict(plan=plan['id'],scenario=scenario['id'],weight=scenario['weight'],curve=scenario['curve'],member=scenario['member'],
            material_weight=scenario['material_weight'],climate_weight=scenario['climate_weight'],D_h=plan['D_h'],
            Tmax_C=float(a['Tmax_C'].max()),delta_C=float(a['delta25_C'].max()),first336_Tmax_C=float(a['Tmax_C'][first].max()),first336_delta_C=float(a['delta25_C'][first].max()),
            peak=peak,delta_peak=delta,horizon_h=horizon_h,last_pour_age_h=horizon_h-max(e.activation_s for e in events)/3600,
            trend_last24_Tmax_C=float(a['Tmax_C'][-1]-a['Tmax_C'][np.flatnonzero(late)[0]]),
            Tmax_peak_in_last24h=record.peak_time_s>t[-1]-86400,delta_peak_in_last24h=record.delta_time_s>t[-1]-86400,
            fail_T=bool(a['Tmax_C'].max()>70),fail_delta=bool(a['delta25_C'].max()>20),
            energy=result.energy,checks=result.checks,steps=len(result.steps),elapsed_s=perf_counter()-start,
            source_total_MJ_m3=curve.H_vol_J_m3/1e6,source_tail_added_MJ_m3=curve.tail_potential_J_m3/1e6,
            configuration=cfg,spacing_m=list(spacing),area_sensitivity=area_factors,coverage=weather.coverage())
        return row,a,record,result

def validate_study(cfg,evaluator):
    c=deepcopy(cfg)
    required={'base','start_utc','horizon_h','spacing_m','max_step_s','material_weights','plans','uncertainty_label'}
    if set(c)!=required or c['base']!='configs/e12/baseline.json':raise ValueError('Estudio E13 incompleto o con claves desconocidas')
    if c['start_utc']!='2026-11-19T11:00:00Z':raise ValueError('Origen común: 19/11/2026 08:00 Chile =11:00 UTC')
    if not isinstance(c['plans'],list) or not 1<=len(c['plans'])<=5:raise ValueError('Una a cinco propuestas por evaluación')
    c['plans']=[validate_plan(p,evaluator.volumes) for p in c['plans']]
    if len({p['id'] for p in c['plans']})!=len(c['plans']) or len({p['rate_m3_h'] for p in c['plans']})!=1:raise ValueError('IDs únicos y capacidad común para comparar')
    w=weights(c['material_weights'])
    if len(w)!=8:raise ValueError('Ocho pesos de material')
    if type(c['horizon_h'])not in (int,float) or not math.isfinite(c['horizon_h']) or not 336<=c['horizon_h']<=600:raise ValueError('Horizonte entre 336 y 600 h, con cobertura')
    if any(p['remove_at_h']>c['horizon_h']-48 for p in c['plans']):raise ValueError('Evaluar al menos 48 h después de retirar protecciones; ampliar horizonte o adelantar retiro')
    if any(max(p['start_h'])+max(p['duration_h'])>c['horizon_h']-240 for p in c['plans']):raise ValueError('Horizonte insuficiente para edad de las últimas vertidas')
    if len(c['spacing_m'])!=3 or any(type(x)not in (int,float) or not math.isfinite(x) or x<.055 or x>1.2 for x in c['spacing_m']):raise ValueError('Resolución fuera de presupuesto')
    if type(c['max_step_s'])not in (int,float) or not 300<=c['max_step_s']<=1800:raise ValueError('Paso máximo entre 300 y 1800 s')
    vox=evaluator.grid(c['spacing_m'])
    if vox.occupation_mask.sum()>180000:raise ValueError('Más de 180000 celdas: ejecutar una sensibilidad dirigida, no una familia completa')
    return c
def signature(cfg):
    files=['src/mcoc_p2/e08/solver.py','src/mcoc_p2/e07/coupling.py','src/mcoc_p2/e10/boundaries.py','src/mcoc_p2/e12/metrics.py','src/mcoc_p2/e12/source.py','src/mcoc_p2/e13/evaluator.py','src/mcoc_p2/e13/plans.py','src/mcoc_p2/e13/risk.py','src/mcoc_p2/e13/weather.py','geometry/foundation.ifc','data/hydration/source_terms.txt','data/ensemble/raw.json','data/ensemble/reduction.json']
    hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in files}
    return dict(configuration=cfg,sha256=hashes,fingerprint=hashlib.sha256(json.dumps([cfg,hashes],sort_keys=True).encode()).hexdigest())
def run_study(cfg,output,*,resume=False,progress=None):
    start=perf_counter();evaluator=Evaluator();cfg=validate_study(cfg,evaluator);sc=scenarios(read(ROOT/'data/ensemble/reduction.json'),cfg['material_weights']);out=Path(output).resolve()
    if not out.is_relative_to(ROOT):raise ValueError('Salida dentro de E13')
    inputs=signature(cfg)
    if out.exists():
        if not resume or read(out/'inputs.json')['fingerprint']!=inputs['fingerprint']:raise ValueError('Destino existente; conservar y elegir otro o resume con inputs idénticos')
    else:out.mkdir(parents=True);write_json(out/'inputs.json',inputs)
    rows=read(out/'cases.json') if (out/'cases.json').exists() else [];done={(r['plan'],r['scenario']) for r in rows};total=len(sc)*len(cfg['plans'])
    for plan in cfg['plans']:
        for scenario in sc:
            if (plan['id'],scenario['id']) in done:continue
            row,_,_,_=evaluator.case(plan,scenario,spacing=cfg['spacing_m'],horizon_h=cfg['horizon_h'],max_step_s=cfg['max_step_s'])
            rows.append(row);write_json(out/'cases.json',rows)
            state=dict(status='running',completed=len(rows),total=total,plan=plan['id'],scenario=scenario['id'],last_elapsed_s=row['elapsed_s'])
            write_json(out/'progress.json',state)
            if progress:progress(state)
    summaries,best=select(cfg['plans'],rows)
    least=min(summaries,key=lambda p:(p['P_joint'],p['delta_C'],p['D_h']))
    report=dict(status='PASS',delivery='E13',model_label=cfg['uncertainty_label'],start_utc=cfg['start_utc'],horizon_h=cfg['horizon_h'],
        plans=summaries,best_feasible=best,illustrative_plan=(best or least)['plan'],illustrative_is_recommendation=best is not None,
        conclusion='Plan de menor duración dentro de la familia discreta evaluada' if best else 'No se encontró un plan factible bajo la familia y el modelo de incertidumbre evaluados',
        scenarios=sc,comparability='Escenarios de incertidumbre de modelo con pesos hipotéticos; no se demostró que las ocho probetas sean réplicas equiprobables',
        independence='Independencia material/clima asumida para w=p*q; sensibilidad de pesos por separado',
        enumeration_cases=len(rows),elapsed_s=perf_counter()-start,all_balances_pass=all(all(r['checks'].values()) for r in rows),
        requires_horizon_review=any(r['Tmax_peak_in_last24h'] or r['delta_peak_in_last24h'] for r in rows))
    write_json(out/'summary.json',report);write_json(out/'progress.json',dict(status='passed',completed=len(rows),total=total))
    return report
