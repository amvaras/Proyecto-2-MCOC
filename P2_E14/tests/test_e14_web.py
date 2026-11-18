"""Flujo E14 real por HTTP: banco, cache, procedencia y seguridad."""
from copy import deepcopy
import time
from test_e11_web import local
from mcoc_p2.e14.io import read,ROOT
from mcoc_p2.e14.statistics import clopper_pearson

def test_browser_provenance_comparison_with_actual_E14_configuration():
    import shutil,subprocess,json,pytest
    node=shutil.which('node')
    if node is None:pytest.skip('Node opcional para prueba JS; no dependencia de la aplicación')
    r=subprocess.run([node,str(ROOT/'tests/test_e14_provenance.mjs')],cwd=ROOT,capture_output=True,text=True,timeout=15)
    assert r.returncode==0,r.stdout+r.stderr
    assert json.loads(r.stdout)['status']=='PASS'

def inputs():return dict(plan_ids=['curado_frio5'],N=100,master_seed=20261119,kind='mc',spacing_m=[.45,.45,.11],temperature_C=None,insulation_m=None,remove_at_h=None)

def test_e14_field_cleanup_preserves_unknown_notes_and_requires_unchanged_inventory(local):
    from mcoc_p2.e14.io import write
    import pytest
    app,_,_=local;key='1'*32;folder=app.store/key;folder.mkdir();(folder/'figures').mkdir()
    app.jobs[key]=dict(id=key,status='passed',legacy=False);write(folder/'job.json',app.jobs[key])
    image=folder/'figures/e14_secciones.png';image.write_bytes(b'known QA placeholder')
    plan=app.discard_plan(key);assert len(plan['files'])==2
    note=folder/'nota_usuario.txt';note.write_text('conservar',encoding='utf8')
    with pytest.raises(ValueError,match='desconocido'):app.discard(key,plan['fingerprint'])
    assert note.exists() and image.exists()
    import os,stat
    own='2'*32;target=app.store/own;target.mkdir();(target/'figures').mkdir();app.jobs[own]=dict(id=own,status='passed',legacy=False)
    write(target/'job.json',app.jobs[own]);(target/'figures/e14_secciones.png').write_bytes(b'own known QA')
    plan=app.discard_plan(own)
    readonly=stat.S_IREAD | (stat.S_IXUSR if os.name!='nt' else 0)
    os.chmod(target/'figures',readonly);os.chmod(target,readonly)
    assert app.discard(own,plan['fingerprint'])['status']=='removed' and not target.exists()

def test_e14_preflight_sources_stale_inputs_and_same_local_interface(local):
    app,_,req=local;code,b,_=req('/api/e14/bootstrap');assert code==200 and len(b['configuration']['plans'])==8
    assert b['reports']['enumeration']['status']=='PASS' and 'NO VERIFICADO' in b['HPC']
    html=req('/')[1].decode();assert 'Pf(N)' in html and 'e14' in html and req('/e14.js')[0]==200 and req('/provenance.js')[0]==200
    d=inputs();code,e,_=req('/api/e14/estimate',dict(parameters=d));assert code==200 and e['new_physics']==0 and e['unique_physics']<=24
    bad=deepcopy(d);bad['N']+=1
    assert req('/api/e14/run',dict(parameters=bad,fingerprint=e['fingerprint']))[0]==400 and not app.jobs
    assert req('/api/e14/run',dict(parameters=d,fingerprint=e['fingerprint']),headers={'Origin':'https://evil.example'})[0]==400
    sample=req('/api/e14/samples/official')[1];assert sample['N']==10000 and len(sample['samples'])==8
    assert len({tuple(x['seed_words']) for x in sample['samples']})==8

def test_e14_actual_batch_worker_uses_saved_inputs_and_independent_OR(local):
    app,_,req=local;d=inputs();code,e,_=req('/api/e14/estimate',dict(parameters=d));assert code==200
    code,j,_=req('/api/e14/run',dict(parameters=d,fingerprint=e['fingerprint']));assert code==202,j
    deadline=time.monotonic()+60
    while time.monotonic()<deadline:
        current=app.snapshot(j['id'])
        if current['status'] not in {'queued','running','cancelling'}:break
        time.sleep(.04)
    assert current['status']=='passed',(current,(app.store/j['id']/'python.log').read_text(encoding='utf8',errors='replace'))
    code,r,_=req('/api/e14/results/'+j['id']);assert code==200 and r['status']=='PASS'
    p=r['plans'][0];folder=app.folder(j['id']);m=read(folder/'manifest.json');cases={v['physics_key']:v['row'] for f in (folder/'chunks').glob('*.json') for v in read(f)['entries']}
    draws=m['bank']['samples']
    # Verificar por índices de escenarios, sin reutilizar el agregador como verdad.
    flags={v['scenario']:(v['Tmax_C']>70 or v['delta_C']>20) for v in cases.values()}
    k=sum(flags[m['scenarios'][x['scenario_index']]['id']] for x in draws)
    assert p['failures']==k and p['P_joint']==k/100 and p['CI']==list(clopper_pearson(k,100))
    assert r['cache_hits']==r['unique_physics'] and not app.processes
    # Un archivo desconocido bloquea la retirada segura del experimento.
    note=app.store/j['id']/'nota_usuario.txt';note.write_text('conservar',encoding='utf8')
    assert req('/api/discard-plan',dict(result=j['id']))[0]==400
    assert note.read_text(encoding='utf8')=='conservar'
