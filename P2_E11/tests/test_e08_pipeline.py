"""IFC real y cambios de inputs; aplicación web usa el mismo cálculo Python."""
import importlib.util
import json
from pathlib import Path
import time
import numpy as np
import pytest
from mcoc_p2.e07.ifc import read_pours
from mcoc_p2.e08.inputs import validate_config
from mcoc_p2.e08.pipeline import run_pipeline

ROOT=Path(__file__).resolve().parents[1]


def quick():
    cfg=json.loads((ROOT/'configs/e08/demo.json').read_text(encoding='utf-8'))
    cfg.update(spacing_m=[.55,.55,.275],resolutions_m=[.55,.4,.275],t_end_s=108000.,save_interval_s=10800.)
    return cfg


def test_real_pipeline_schedule_and_placement_changes_affect_temperatures(tmp_path):
    cfg=quick();baseline=run_pipeline(ROOT/'geometry/foundation.ifc',cfg,tmp_path/'base',plots=False)
    warm=json.loads(json.dumps(cfg))
    for event in warm['events']:event['initial_C']+=8
    heated=run_pipeline(ROOT/'geometry/foundation.ifc',warm,tmp_path/'warm',plots=False)
    earlier=json.loads(json.dumps(cfg))
    for i,event in enumerate(earlier['events']):event['activation_s']=i*7200.
    fast=run_pipeline(ROOT/'geometry/foundation.ifc',earlier,tmp_path/'early',plots=False)
    assert baseline['activation_events'][1]['time_s']==21600
    assert fast['activation_events'][1]['time_s']==7200
    assert all(baseline['checks'].values()) and all(heated['checks'].values()) and all(fast['checks'].values())
    with np.load(tmp_path/'base/solution.npz') as a,np.load(tmp_path/'warm/solution.npz') as b,np.load(tmp_path/'early/solution.npz') as c:
        assert np.min(b['temperature_C'][-1]-a['temperature_C'][-1])>0
        assert np.max(abs(c['temperature_C'][-1]-a['temperature_C'][-1]))>.1
        # A history, not repeated placement temperatures: first pour heats up.
        assert baseline['temperature_range_C'][1]>25
    view=json.loads((tmp_path/'base/geometry.json').read_text(encoding='utf-8'))
    assert len(view['groups'])==5 and view['occupied_cells']==baseline['nominal']['occupied_cells']
    assert max(int(face[5]) for group in view['groups'] for face in group['faces'])<view['occupied_cells']
    with pytest.raises(ValueError,match='contenido'):run_pipeline(ROOT/'geometry/foundation.ifc',cfg,tmp_path/'base',plots=False)


@pytest.mark.parametrize('field,value',[
    ('spacing_m',[0,1,1]),('spacing_m',[1e-6]*3),('safety',1.1),('max_step_s',0),
    ('save_interval_s',0),('resolutions_m',[.5,.5,.2]),('t_end_s',float('nan')),
])
def test_invalid_inputs_rejected_before_allocation(field,value):
    cfg=quick();cfg[field]=value
    with pytest.raises((ValueError,TypeError)):validate_config(cfg,read_pours(ROOT/'geometry/foundation.ifc')[0])


def test_web_application_runs_python_and_serves_real_temperature_frames(tmp_path):
    spec=importlib.util.spec_from_file_location('e08_server_test',ROOT/'web/servidor.py')
    server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)
    app=server.Application(store=tmp_path/'jobs')
    cfg=quick();cfg['t_end_s']=7200.
    job=app.start(cfg,'default')
    deadline=time.monotonic()+45
    while time.monotonic()<deadline:
        status=app.snapshot(job['id'])
        if status['status'] not in ('queued','running'):break
        time.sleep(.05)
    assert status['status']=='passed',status
    report=server.read(app.folder(job['id'])/'summary.json')
    frame=np.frombuffer(app.frame(job['id'],len(report['times_s'])-1),dtype='<f4')
    assert len(frame)==report['nominal']['occupied_cells'] and np.isfinite(frame).any()
    assert frame[np.isfinite(frame)].max()>18
    restored=server.Application(store=tmp_path/'jobs')
    assert restored.snapshot(job['id'])['status']=='passed'
    assert restored.model_info(job['id'])[1]['pours'][0]['vertida_id']==1
    np.testing.assert_equal(restored.frame(job['id'],len(report['times_s'])-1),app.frame(job['id'],len(report['times_s'])-1))
