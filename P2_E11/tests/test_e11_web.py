"""API local, cambios físicos reales, seguridad y equivalencia con Python."""
from copy import deepcopy
import hashlib,importlib.util,json,threading,time
from http.client import HTTPConnection
from pathlib import Path
import numpy as np
import pytest
from mcoc_p2.e11.pipeline import run
from mcoc_p2.e11 import webdata

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('e11_web_test',ROOT/'web/servidor.py')
server=importlib.util.module_from_spec(spec);spec.loader.exec_module(server)


def quick():
    c=webdata.read(ROOT/'configs/e11/demo.json');c['physics'].update(spacing_m=[.9,.9,.275],t_end_s=10800,max_step_s=600,save_interval_s=1800)
    for i,e in enumerate(c['physics']['events']):e['activation_s']=i*1800
    c['export_hours']=[0,1.5,3]
    return c


def test_javascript_filters_synthetic_coordinates_fields_and_non_mutation():
    import shutil,subprocess
    node=shutil.which('node')
    if node is None:pytest.skip('Node opcional solo para la prueba unitaria JS; no requerido por la aplicación')
    result=subprocess.run([node,str(ROOT/'tests/test_e11_viewer.mjs')],cwd=ROOT,capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stdout+result.stderr
    assert json.loads(result.stdout)['status']=='PASS'


@pytest.fixture
def local(tmp_path):
    app=server.Application(tmp_path/'jobs');http=server.ThreadingHTTPServer(('127.0.0.1',0),server.handler_for(app));thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
    def request(path,body=None,headers=None,method=None):
        connection=HTTPConnection('127.0.0.1',http.server_port,timeout=45)
        default={'Origin':f'http://127.0.0.1:{http.server_port}','Content-Type':'application/json','X-E11-Token':app.token}
        default.update(headers or {});payload=json.dumps(body).encode() if body is not None else None
        connection.request(method or ('POST' if body is not None else 'GET'),path,payload,default);response=connection.getresponse();raw=response.read();status=response.status;head=dict(response.getheaders());connection.close()
        return status,json.loads(raw) if head.get('Content-Type','').startswith('application/json') else raw,head
    yield app,http,request
    app.close();http.shutdown();http.server_close();thread.join(timeout=5)


def complete(app,job):
    deadline=time.monotonic()+45
    while time.monotonic()<deadline:
        j=app.snapshot(job['id'])
        if j['status'] not in ('queued','running','cancelling'):break
        time.sleep(.04)
    assert j['status']=='passed',(j,(app.store/job['id']/'python.log').read_text(encoding='utf-8',errors='replace')[-3500:])
    return app.folder(job['id'])


def test_bootstrap_html_modules_metadata_and_snapshot_validation(local):
    app,http,req=local
    assert http.server_address[0]=='127.0.0.1'
    for route in ('/','/app.js','/viewer.js','/charts.js','/styles.css'):
        status,body,headers=req(route);assert status==200 and len(body)>100
        assert "connect-src 'self'" in headers['Content-Security-Policy'] and 'Access-Control-Allow-Origin' not in headers
    status,b,_=req('/api/bootstrap');assert status==200 and b['app']=='mcoc-e11-local' and len(b['model']['pours'])==5
    assert b['configuration']['environment']['air']['h_still_W_m2K']==8
    status,w,_=req('/api/verify',dict(kind='weather',configuration=quick()));assert status==200 and w['status']=='PASS' and w['samples']==72
    assert all(w['checks'].values()) and w['metadata']['kind']=='forecast'
    status,raw,_=req('/api/weather-file',dict(snapshot=b['configuration']['snapshot'],file='raw'))
    assert status==200 and hashlib.sha256(raw['content'].encode()).hexdigest()==w['metadata']['raw_sha256']


@pytest.mark.parametrize('variant',[0,1])
def test_api_and_direct_python_have_exactly_identical_arrays(local,tmp_path,variant):
    app,http,req=local;c=quick()
    if variant:
        c['environment']['air']['h_still_W_m2K']=19;c['constant_reference_C']=27;c['physics']['events'][1]['activation_s']=900;c['physics']['events'][0]['initial_C']=24
    status,job,_=req('/api/run',dict(configuration=c,model_id='default'));assert status==202
    out=complete(app,job);effective=webdata.read(out/'inputs.json');direct=tmp_path/'direct'
    run(effective,direct,plots=False,export=False)
    for name in ('grid.npz','fields.npz','statistics.npz','weather_steps.npz','constant_steps.npz'):
        a,b=webdata.arrays(out/name),webdata.arrays(direct/name);assert a.keys()==b.keys()
        for key in a:np.testing.assert_array_equal(a[key],b[key])
    assert job['configuration']==effective
    assert webdata.read(app.store/job['id']/'job.json')['configuration_sha256']==hashlib.sha256(json.dumps(effective,sort_keys=True).encode()).hexdigest()
    status,check,_=req('/api/verify',dict(kind='result',result=job['id']));assert status==200 and all(check['checks'].values())
    data=webdata.presentation(out);g=webdata.geometry(out);f=webdata.arrays(out/'fields.npz')
    assert len(data['frames'])>=3 and len(data['centers'])==5 and len(g['probes'])==3
    assert data['frames'][0]['active_ids']==[1] and data['frames'][-1]['active_ids']==[1,2,3,4,5]
    status,raw,_=req('/api/results/'+job['id']+'/frame/'+str(len(f['times_s'])-1)+'/weather')
    assert status==200;np.testing.assert_array_equal(np.frombuffer(raw,dtype='<f4'),f['weather_C'][-1].astype('<f4'))
    for pid in range(1,6):assert any(label==pid for label in g['labels'])
    assert np.isfinite(f['weather_C']).all() and np.isfinite(f['constant_C']).all()


@pytest.mark.parametrize('change',['h','ambient','initial','activation','spacing','hydration','soil','formwork'])
def test_browser_inputs_change_actual_thermal_solution(local,tmp_path,change):
    app,http,req=local;c=quick();base=tmp_path/'baseline';run(c,base,plots=False,export=False)
    modified=deepcopy(c)
    if change=='h':modified['environment']['air']['h_still_W_m2K']=25
    if change=='ambient':modified['constant_reference_C']=32
    if change=='initial':modified['physics']['events'][0]['initial_C']+=5
    if change=='activation':modified['physics']['events'][1]['activation_s']=600
    if change=='spacing':modified['physics']['spacing_m']=[1.1,1.1,.275]
    if change=='hydration':modified['physics']['hydration']['H_vol_J_m3']=0
    if change=='soil':modified['environment']['soil']['adiabatic']=True
    if change=='formwork':modified['environment']['formwork']['remove_at_s']=0
    status,job,_=req('/api/run',dict(configuration=modified));assert status==202
    out=complete(app,job);a=webdata.arrays(base/'fields.npz');b=webdata.arrays(out/'fields.npz')
    if change=='spacing':assert a['weather_C'].shape[1]!=b['weather_C'].shape[1]
    elif change=='ambient':
        np.testing.assert_array_equal(a['weather_C'],b['weather_C']);assert np.max(abs(a['constant_C'][-1]-b['constant_C'][-1]))>1e-6
    else:assert np.max(abs(a['weather_C'][-1]-b['weather_C'][-1]))>1e-6
    report=webdata.read(out/'summary.json');assert all(all(v.values()) for v in report['checks'].values())


@pytest.mark.parametrize('headers',[{'Origin':'https://evil.example'},{'X-E11-Token':''},{'Host':'evil.example'},{'Sec-Fetch-Site':'cross-site'}])
def test_cross_origin_and_forged_mutations_are_rejected(local,headers):
    app,http,req=local;status,body,_=req('/api/run',dict(configuration=quick()),headers=headers)
    assert status==400 and not app.jobs


@pytest.mark.parametrize('path',['/../../pyproject.toml','/files/official/../../AGENTS.md','/files/official/.env','/api/results/nope/data','/web/servidor.py'])
def test_only_explicit_file_routes_are_readable(local,path):
    _,_,req=local;status,body,_=req(path);assert status in (400,404)


@pytest.mark.parametrize('mutate',['resolution','missing','snapshot','h','command','coverage'])
def test_invalid_configuration_rejected_before_job_creation(local,mutate):
    app,_,req=local;c=quick()
    if mutate=='resolution':c['physics']['spacing_m']=[.001]*3
    if mutate=='missing':c.pop('environment')
    if mutate=='snapshot':c['snapshot']='../../secrets'
    if mutate=='h':c['environment']['air']['h_still_W_m2K']=-1
    if mutate=='command':c['command']='whoami'
    if mutate=='coverage':c['simulation_start_utc']='2020-01-01T00:00:00Z'
    status,body,_=req('/api/run',dict(configuration=c));assert status==400 and not app.jobs


def test_concurrent_runs_cancel_and_partial_results_not_exposed(local):
    app,_,req=local;status,job,_=req('/api/run',dict(configuration=quick()));assert status==202
    status,_,_=req('/api/run',dict(configuration=quick()));assert status==400
    assert req('/api/results/'+job['id']+'/data')[0]==400
    assert req('/api/cancel/'+job['id'],{})[0]==200
    deadline=time.monotonic()+10
    while app.busy() and time.monotonic()<deadline:time.sleep(.05)
    assert app.snapshot(job['id'])['status']=='cancelled' and not app.busy()


def test_official_result_is_immutable_and_web_exposes_real_probe_faces(local):
    app,_,req=local;before=webdata.digest(ROOT/'results/e11/fields.npz')
    status,data,_=req('/api/results/official/data');assert status==200
    assert data['summary']['probes'][0]['kind']=='cell_center' and data['summary']['probes'][1]['kind']=='reconstructed_face'
    assert data['frames'][0]['probes']['weather'][1] is None
    assert req('/api/verify',dict(kind='result',result='official'))[1]['status']=='PASS'
    assert webdata.digest(ROOT/'results/e11/fields.npz')==before


def test_retiring_own_run_requires_fresh_inventory_and_preserves_unknown_files(local):
    app,_,req=local;assert req('/api/discard-plan',dict(result='official'))[0]==400
    _,job,_=req('/api/run',dict(configuration=quick()));out=complete(app,job);key=job['id']
    status,plan,_=req('/api/discard-plan',dict(result=key));assert status==200 and len(plan['files'])>10
    unknown=out/'user_notes.txt';unknown.write_text('preserve',encoding='utf-8')
    assert req('/api/discard',dict(result=key,fingerprint=plan['fingerprint']))[0]==400
    assert unknown.read_text()=='preserve';unknown.unlink()  # Archivo sintético propio de este test.
    modified=app.store/key/'python.log';modified.write_text(modified.read_text(encoding='utf-8')+'\nchanged',encoding='utf-8')
    assert req('/api/discard',dict(result=key,fingerprint=plan['fingerprint']))[0]==400
    status,current,_=req('/api/discard-plan',dict(result=key));assert status==200
    assert req('/api/discard',dict(result=key,fingerprint=current['fingerprint']))[1]['status']=='removed'
    assert key not in app.jobs and not (app.store/key).exists() and (ROOT/'results/e11/fields.npz').exists()


@pytest.mark.parametrize('closing',['parent_eof','http_shutdown'])
def test_parent_pipe_closes_server_without_orphan_process(tmp_path,closing):
    import socket,subprocess,sys
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    process=subprocess.Popen([sys.executable,'-X','utf8','-B','web/servidor.py','--port',str(port),'--store',str(tmp_path/'watchdog'),'--watch-parent'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    try:
        deadline=time.monotonic()+10;ready=False
        while time.monotonic()<deadline:
            try:
                connection=HTTPConnection('127.0.0.1',port,timeout=.5);connection.request('GET','/api/health');response=connection.getresponse();ready=json.loads(response.read())['app']=='mcoc-e11-local';connection.close()
                if ready:break
            except (OSError,ValueError):time.sleep(.05)
        assert ready
        # El proceso de cálculo NO debe heredar el pipe de vigilancia del padre.
        connection=HTTPConnection('127.0.0.1',port,timeout=5);connection.request('GET','/api/bootstrap');token=json.loads(connection.getresponse().read())['token'];connection.close()
        headers={'Content-Type':'application/json','X-E11-Token':token,'Origin':f'http://127.0.0.1:{port}'}
        cfg=quick();cfg['physics']['t_end_s']=3600
        connection=HTTPConnection('127.0.0.1',port,timeout=5);connection.request('POST','/api/run',json.dumps(dict(configuration=cfg)).encode(),headers);response=connection.getresponse();job=json.loads(response.read());assert response.status==202;connection.close()
        deadline=time.monotonic()+45
        while time.monotonic()<deadline:
            connection=HTTPConnection('127.0.0.1',port,timeout=5);connection.request('GET','/api/jobs/'+job['id']);current=json.loads(connection.getresponse().read());connection.close()
            if current['status'] not in ('queued','running'):break
            time.sleep(.05)
        assert current['status']=='passed',current
        if closing=='parent_eof':process.stdin.close()
        else:
            connection=HTTPConnection('127.0.0.1',port,timeout=5);connection.request('GET','/api/bootstrap');token=json.loads(connection.getresponse().read())['token'];connection.close()
            connection=HTTPConnection('127.0.0.1',port,timeout=5);connection.request('POST','/api/shutdown',b'{}',{'Content-Type':'application/json','X-E11-Token':token,'Origin':f'http://127.0.0.1:{port}'});assert connection.getresponse().status==200;connection.close()
        assert process.wait(timeout=10)==0
    finally:
        if process.poll() is None:process.terminate();process.wait(timeout=5)
