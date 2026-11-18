"""Integración E12 real en la misma API: fuente y resultados nuevos."""
from copy import deepcopy
import json
from pathlib import Path
import numpy as np
from test_e11_web import local,complete
from mcoc_p2.e12.pipeline import run,arrays
ROOT=Path(__file__).resolve().parents[1]

def config():return json.loads((ROOT/'configs/e12/baseline.json').read_text(encoding='utf8'))

def test_E12_default_configuration_source_energy_and_336h_coverage(local):
    app,server,req=local;_,b,_=req('/api/bootstrap')
    assert b['configuration']['physics']['t_end_s']==336*3600 and b['weather']['coverage']['tail_hours']==0
    status,data,_=req('/api/validate',{'configuration':config()});assert status==200 and data['status']=='PASS'
    status,source,_=req('/api/source',{'source':config()['experimental_source']})
    assert status==200 and source['report']['selected']=='M2_SS' and abs(source['H_MJ_m3']-95.715221706)<1e-9
    assert len(source['Q_W_m3'])==1443
    bad=deepcopy(config()['experimental_source']);bad['file']='../../source_terms.txt'
    assert req('/api/source',{'source':bad})[0]==400

def test_E12_API_executes_same_corrected_source_solver_as_Python(local,tmp_path):
    app,server,req=local;c=config();c['physics'].update(spacing_m=[.9,.9,.275],t_end_s=10800,max_step_s=600,save_interval_s=3600);c['export_hours']=[0,1.5,3]
    for i,e in enumerate(c['physics']['events']):e['activation_s']=i*1800
    status,job,_=req('/api/run',{'configuration':c});assert status==202
    out=complete(app,job);direct=tmp_path/'direct';run(job['configuration'],direct,plots=False,export=False)
    for file in ['fields.npz','all_steps.npz','statistics.npz','weather_steps.npz','constant_steps.npz']:
        a,b=arrays(out/file),arrays(direct/file)
        for key in a:np.testing.assert_array_equal(a[key],b[key])
    status,report,_=req('/api/verify',{'kind':'result','result':job['id']})
    assert status==200 and report['status']=='PASS' and report['same_units']
    status,p,_=req('/api/results/'+job['id']+'/data')
    assert status==200 and p['summary']['delivery']=='E12' and p['summary']['source']['selected']=='M2_SS'
    assert 'weather_delta25_C' in p['statistics'] and p['summary']['global_delta25_maximum']['value_C']>0
    assert req('/files/'+job['id']+'/e12.pvd')[0]==200

