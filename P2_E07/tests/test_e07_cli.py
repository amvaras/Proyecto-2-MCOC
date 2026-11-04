from pathlib import Path
import json
import subprocess
import sys
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]


def run(*args):
    return subprocess.run([sys.executable,'-X','utf8','-B','examples/run_e07.py',*map(str,args)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')


def test_cli_changes_geometry_parameters_and_calendar(tmp_path):
    out=tmp_path/'changed'
    p=run('--output',out,'--spacing',.5,.4,.275,'--interval-hours',0,'--heat-mj-m3',20,
          '--duration-hours',12,'--t-end-hours',1,'--max-step',700,'--no-plots')
    assert p.returncode==0,p.stdout+p.stderr
    r=json.loads((out/'summary.json').read_text(encoding='utf-8'))
    assert r['nominal']['spacing_m']==[.5,.4,.275] and r['timeline'][0]['active_ids']==[1,2,3,4,5]
    assert r['hydration']['H_vol_J_m3']==20e6 and r['hydration']['duration_s']==43200
    assert all(r['checks'].values())
    with np.load(out/'voxels.npz') as v:
        assert set(np.unique(v['vertida_id']))=={0,1,2,3,4,5}
    before=(out/'summary.json').read_bytes();again=run('--output',out,'--no-plots')
    assert again.returncode==2 and (out/'summary.json').read_bytes()==before


@pytest.mark.parametrize('args',[['--spacing','0'],['--spacing','1e-6'],['--duration-hours','0'],['--interval-hours','-1']])
def test_cli_rejects_invalid_input(tmp_path,args):
    p=run('--output',tmp_path/'invalid','--no-plots',*args)
    assert p.returncode==2 and 'ERROR:' in p.stdout


def test_inspection_dumps_actual_geometry_and_guid(tmp_path):
    out=tmp_path/'inspect';p=run('--inspect-only','--output',out);assert p.returncode==0
    doc=json.loads((out/'geometry.json').read_text(encoding='utf-8'))
    assert len(doc['pours'])==5 and doc['coordinates']=='world SI m'
    with np.load(out/'geometry.npz') as arrays:assert len(arrays.files)==10


def test_per_pour_material_and_heat_parameters_are_used(tmp_path):
    cfg=json.loads((ROOT/'configs/e07/demo.json').read_text(encoding='utf-8'))
    cfg['events'][1]['material']={'cp':1000.}
    cfg['events'][4]['hydration']={'H_vol_J_m3':0.}
    config=tmp_path/'different_pours.json';config.write_text(json.dumps(cfg),encoding='utf-8');out=tmp_path/'per_pour'
    result=run('--config',config,'--output',out,'--interval-hours',0,'--t-end-hours',1,'--no-plots')
    assert result.returncode==0,result.stdout+result.stderr
    with np.load(out/'voxels.npz') as v,np.load(out/'construction.npz') as c:
        volume=float(np.prod(v['spacing_m']))
        np.testing.assert_allclose(c['capacity_J_K'][v['vertida_id']==2],2400*1000*volume)
        np.testing.assert_array_equal(c['hydration_source_W_m3'][v['vertida_id']==5],0)
