"""Panel único: coste previo, seguridad, enumeración y equivalencia real Python/API."""
from copy import deepcopy
from pathlib import Path
import time
import numpy as np
from test_e11_web import local
from mcoc_p2.e13.weather import read
from mcoc_p2.e13.evaluator import Evaluator
from mcoc_p2.e13.risk import scenarios,probability
ROOT=Path(__file__).resolve().parents[1]
def test_e13_panel_sources_climate_cost_and_modified_input_fingerprint(local):
    app,_,req=local;code,info,_=req('/api/e13/bootstrap');assert code==200
    assert len(info['sources'])==8 and len(info['climate'])==3 and len(info['scenarios'])==24
    html=req('/')[1].decode();assert 'Decisión y riesgo E13' in html and 'e13-table' in html
    assert req('/e13.js')[0]==200
    c=read(ROOT/'configs/e13/study.json');c['plans']=c['plans'][2:3];c['spacing_m']=[1.2,1.2,.275];c['horizon_h']=336
    status,estimate,_=req('/api/e13/estimate',{'configuration':c});assert status==200 and estimate['cases']==24 and estimate['estimated_s']>0
    bad=deepcopy(c);bad['plans'][0]['initial_C']=[14]*5
    status,_,_=req('/api/e13/run',{'configuration':bad,'fingerprint':estimate['fingerprint']});assert status==400 and not app.jobs
    assert req('/api/e13/run',{'configuration':c,'fingerprint':estimate['fingerprint']},headers={'Origin':'https://evil.example'})[0]==400
def test_real_e13_batch_API_equals_direct_case_and_independent_OR(local):
    app,_,req=local;c=read(ROOT/'configs/e13/study.json');c['plans']=c['plans'][:1];c['spacing_m']=[1.2,1.2,.275];c['horizon_h']=336
    status,est,_=req('/api/e13/estimate',{'configuration':c});assert status==200
    status,j,_=req('/api/e13/run',{'configuration':c,'fingerprint':est['fingerprint']});assert status==202
    deadline=time.monotonic()+120
    while time.monotonic()<deadline:
        current=app.snapshot(j['id'])
        if current['status'] not in ('queued','running','cancelling'):break
        time.sleep(.05)
    assert current['status']=='passed',current
    status,data,_=req('/api/e13/results/'+j['id']);assert status==200 and len(data['cases'])==24 and data['summary']['all_balances_pass']
    rows=data['cases'];expected=sum(r['weight'] for r in rows if r['Tmax_C']>70 or r['delta_C']>20)
    assert data['summary']['plans'][0]['P_joint']==expected
    s=scenarios(read(ROOT/'data/ensemble/reduction.json'))[3];row,_,_,_=Evaluator().case(c['plans'][0],s,spacing=c['spacing_m'],horizon_h=336)
    found=next(r for r in rows if r['scenario']==s['id'])
    assert row['Tmax_C']==found['Tmax_C'] and row['delta_C']==found['delta_C']
    assert row['configuration']==found['configuration'] and all(found['checks'].values())

def test_nondefault_tail_energy_is_verified_with_actual_tau(tmp_path):
    from mcoc_p2.e12.pipeline import run
    from mcoc_p2.e12.verification import verify
    c=read(ROOT/'configs/e12/baseline.json');c['physics'].update(spacing_m=[1.2,1.2,.275],save_interval_s=24*3600)
    c['experimental_source'].update(curve='M1_SS',tail='exponential',tau_s=48*3600)
    out=tmp_path/'tail48';s=run(c,out,plots=False,vtk_dir=out/'vtk');report=verify(out,out/'vtk')
    assert report['status']=='PASS' and s['source']['tail_tau_s']==48*3600
    assert s['source']['tail_additional_MJ_m3']==1.57*48*3600/1e6
