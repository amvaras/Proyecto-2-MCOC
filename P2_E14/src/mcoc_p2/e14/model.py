"""Adaptación de planes/protecciones, misma Evaluator E13 y mismo integrador E08."""
from copy import deepcopy
from pathlib import Path
from time import perf_counter
import math,hashlib
import numpy as np
from ..e11.pipeline import ROOT
from ..e13.evaluator import Evaluator
from ..e13.plans import make_plan,validate_plan,thermal_config
from ..e13.risk import scenarios
from ..e12.source import load_curve
from ..e11.weather import validate
from ..e10.weather import WeatherWindow
from .io import read,write,fingerprint,source_hashes,inside
from .statistics import limit_states
def catalog():return scenarios(read(ROOT/'data/ensemble/reduction.json'))
def baseline_plans():
    c=read(ROOT/'configs/e13/study.json')
    return [dict(id=p['id'],construction=p,design={},horizon_h=c['horizon_h'],provenance='E13 reutilizado') for p in c['plans']]
def new_plan(identifier,volumes,*,wait_h,initial_C=8.,insulation_m=.08,remove_at_h=None,horizon_h=None):
    p=make_plan(identifier,volumes,50.,wait_h=wait_h,initial_C=initial_C,protected=True)
    horizon_h=horizon_h or min(744.,24*math.ceil((max(p['start_h'])+336)/24))
    p['remove_at_h']=float(remove_at_h if remove_at_h is not None else horizon_h-96)
    return dict(id=identifier,construction=p,design=dict(insulation_m=insulation_m,insulation_k_W_mK=.04,
        basis='Mismo aislante k=0.04 de E13; espesor/curado son decisiones, no mediciones nuevas. Máximo 0.10 m, suministro frío >=5°C, una bomba 50 m³/h.',
        structural_admissibility='Supuestos logísticos/temperatura/protecciones requieren aprobación; no resistencia de juntas ni capacidad frigorífica demostradas'),horizon_h=horizon_h,provenance='Exploración E14 dirigida')
class Model:
    def __init__(self):
        self.engine=Evaluator();self.base=deepcopy(self.engine.base);self.hashes=source_hashes();self.weather={}
    def validate(self,item):
        p=validate_plan(item['construction'],self.engine.volumes)
        if item['id']!=p['id']:raise ValueError('Identidad de plan inconsistente')
        d=item['design'];allowed={'insulation_m','insulation_k_W_mK','basis','structural_admissibility'}
        if set(d)-allowed:raise ValueError('Diseño desconocido')
        if d:
            if not .025<=d['insulation_m']<=.10 or d['insulation_k_W_mK']!=.04:raise ValueError('Material existente y espesor acotado 25–100 mm')
            if min(p['initial_C'])<5 or max(p['initial_C'])>22:raise ValueError('Suministro declarado entre 5 y 22°C')
        h=item['horizon_h']
        if not 336<=h<=744 or p['remove_at_h']>h-48 or max(p['start_h'])+240>h:raise ValueError('Horizonte insuficiente para colocación, hidratación o retiro')
        return p
    def configuration(self,item,scenario,spacing=(.45,.45,.11),step_s=900):
        p=self.validate(item);base=deepcopy(self.base);d=item['design']
        if d:base['environment']['formwork']['layers']=[dict(name='tablero',thickness_m=.018,conductivity_W_mK=.13),dict(name='aislacion',thickness_m=d['insulation_m'],conductivity_W_mK=d['insulation_k_W_mK'])]
        cfg=thermal_config(base,p,scenario,spacing=spacing,horizon_h=item['horizon_h'],max_step_s=step_s)
        curve,_=load_curve(ROOT/cfg['experimental_source']['file'],scenario['curve'],tail='exponential',tau_s=scenario.get('tau_h',24)*3600)
        cfg['physics']['hydration']=dict(H_vol_J_m3=curve.H_vol_J_m3,duration_s=curve.duration_s)
        if cfg['snapshot'] not in self.weather:self.weather[cfg['snapshot']]=validate(ROOT/cfg['snapshot'])
        WeatherWindow(self.weather[cfg['snapshot']],cfg['simulation_start_utc'],item['horizon_h']*3600,tail=None)
        return cfg,base
    def key(self,cfg,area_factors=None):
        c=deepcopy(cfg);c['physics'].pop('description',None)
        return fingerprint(dict(configuration=c,area_factors=area_factors,kernel=self.hashes,metric='cell-max and E12 S25 v1'))
    def evaluate(self,item,scenario,*,spacing=(.45,.45,.11),step_s=900,area_factors=None):
        cfg,base=self.configuration(item,scenario,spacing,step_s);self.engine.base=base
        row,stats,record,solution=self.engine.case(item['construction'],scenario,spacing=spacing,horizon_h=item['horizon_h'],max_step_s=step_s,area_factors=area_factors)
        assert cfg==row['configuration']
        field_hash=hashlib.sha256(solution.times_s.tobytes()+solution.temperature_C.tobytes()).hexdigest()
        g=limit_states(row['Tmax_C'],row['delta_C']);row.update(g_T=float(g['g_T']),g_Delta=float(g['g_Delta']),fail_joint=bool(g['fail_joint']),physics_key=self.key(cfg,area_factors),design=item['design'],construction=item['construction'],saved_fields_sha256=field_hash)
        return row,stats,record,solution
