"""Reutilización, integridad, reanudación, errores y agregación sin censura."""
from pathlib import Path
from copy import deepcopy
import hashlib
import pytest
from mcoc_p2.e11.pipeline import ROOT
from mcoc_p2.e14.model import Model,catalog,baseline_plans
from mcoc_p2.e14.store import Store
from mcoc_p2.e14.io import read,write,fingerprint,inside
from mcoc_p2.e14.workflow import prepare,run_local,load_manifest,aggregate
def config():return dict(plans=baseline_plans()[:1],spacing_m=[.45,.45,.11],step_s=900,N=30,master_seed=20261119)
def test_atomic_output_survives_transient_windows_reader_lock(monkeypatch,tmp_path):
    import mcoc_p2.e14.io as io
    destination=tmp_path/'progress.json';write(destination,{'completed':1});original=io.os.replace;attempts=[]
    def transient(a,b):
        attempts.append(a)
        if len(attempts)<3:
            assert read(destination)=={'completed':1}
            raise PermissionError('Lector Windows temporal')
        return original(a,b)
    monkeypatch.setattr(io.os,'replace',transient)
    write(destination,{'completed':2},replace=True)
    assert len(attempts)==3 and read(destination)=={'completed':2} and not list(tmp_path.glob('*.tmp-*'))
def test_reuse_known_E13_input_without_solver_and_protect_corrupt_cache(monkeypatch,tmp_path):
    m=Model();p=baseline_plans()[0];s=catalog()[0];store=Store()
    def forbidden(*a,**kw):raise AssertionError('No repetir física ya verificada')
    monkeypatch.setattr(m,'evaluate',forbidden)
    row=store.evaluate(m,p,s);assert row['cache_hit'] and row['g_T']==70-row['Tmax_C']
    local=Store(tmp_path/'cache');entry=dict(physics_key=row['physics_key'],row=row,row_sha256=fingerprint(row));write(local.root/(row['physics_key']+'.json'),entry)
    entry['row']['Tmax_C']+=1;write(local.root/(row['physics_key']+'.json'),entry,replace=True)
    with pytest.raises(ValueError,match='alterado'):local.get(row['physics_key'])
    with pytest.raises(ValueError):inside(ROOT.parent/'P2_E13/unknown.json')
def test_manifest_reproducible_chunks_resume_and_shared_random_bank(tmp_path):
    out=tmp_path/'run';m=prepare(config(),out,chunk_size=3);assert m['estimate']['new']==0 and m['estimate']['reused']>0
    result=run_local(out/'manifest.json',1);assert result['plans'][0]['P_joint']==1 and result['plans'][0]['N']==30
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'chunks').glob('*.json')}
    repeat=run_local(out/'manifest.json',1);assert repeat['plans']==result['plans']
    assert before=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'chunks').glob('*.json')}
    bad=read(out/'manifest.json');bad['configuration']['master_seed']+=1;write(out/'manifest.json',bad,replace=True)
    with pytest.raises(ValueError,match='alterado'):load_manifest(out/'manifest.json')
def test_failure_is_not_a_thermal_success_and_retry_is_explicit(monkeypatch,tmp_path):
    import mcoc_p2.e14.workflow as w
    c=config();c['N']=2;out=tmp_path/'failure';prepare(c,out,chunk_size=1)
    original=w._execute_task
    monkeypatch.setattr(w,'_execute_task',lambda task,force=False:dict(status='failed',physics_key=task['physics_key'],error='synthetic numeric failure',error_type='RuntimeError'))
    with pytest.raises(ValueError,match='errores'):run_local(out/'manifest.json',1)
    assert read(out/'errors.json')['status']=='failed' and not (out/'summary.json').exists()
    monkeypatch.setattr(w,'_execute_task',original)
    result=run_local(out/'manifest.json',1,retry_failed=True);assert result['status']=='PASS' and result['plans'][0]['N']==2
    assert read(out/'errors.json')['status']=='resolved' and read(out/'errors.json')['unresolved']==0
def test_missing_chunk_and_cross_run_outputs_are_rejected(tmp_path):
    out=tmp_path/'missing';prepare(config(),out)
    with pytest.raises(ValueError,match='Falta chunk'):aggregate(out/'manifest.json')

def test_enumeration_aggregates_existing_metrics_without_duplicate_keywords(tmp_path):
    out=tmp_path/'enumeration';m=prepare(config(),out,kind='enumeration',chunk_size=8);r=run_local(out/'manifest.json',1)
    p=r['plans'][0];assert p['P_joint']==1 and p['scenarios']==24 and p['Tmax_C']>60 and p['delta_C']>40
    assert 'Ninguno' in p['interval_type'] and m['estimate']['new']==0
