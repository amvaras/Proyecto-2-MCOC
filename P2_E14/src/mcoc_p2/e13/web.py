"""Acciones E13 de la única aplicación local; costes antes de crear procesos."""
from pathlib import Path
from copy import deepcopy
from time import perf_counter
import json,math,os,secrets,subprocess,sys,threading,uuid
from ..e11.pipeline import ROOT,write_json
from ..e12.source import read_sources
from .weather import read
from .plans import make_plan,thermal_config
from .evaluator import Evaluator,validate_study,signature
from .risk import scenarios

def bootstrap():
    c=read(ROOT/'configs/e13/study.json');red=read(ROOT/'data/ensemble/reduction.json');curves,meta=read_sources(ROOT/'data/hydration/source_terms.txt')
    climate=[]
    for member,path,w in zip(red['medoids'],red['snapshots'],red['weights']):
        raw=read(ROOT/path/'weather.json');m=read(ROOT/path/'metadata.json')
        climate.append(dict(member=member,weight=w,seconds=raw['hourly']['time'],temperature_C=raw['hourly']['temperature_2m'],metadata=m))
    official=read(ROOT/'results/e13/summary.json') if (ROOT/'results/e13/summary.json').exists() else None
    return dict(configuration=c,official=official,scenarios=scenarios(red,c['material_weights']),climate=climate,reduction=red,
        sources={n:dict(hours=(t/3600).tolist(),Q_W_m3=q.tolist(),metadata=meta['curves'][n]) for n,(t,q) in curves.items()},
        limits=dict(Tmax_C=70,delta_C=20,P_joint=.05),meaning=c['uncertainty_label'])
def prepare(data):
    required={'plan','rate_m3_h','wait_h','initial_C','remove_at_h','spacing_m','horizon_h'}
    if set(data)!=required:raise ValueError('Completar parámetros E13')
    ev=Evaluator();original=read(ROOT/'configs/e13/study.json');known={p['id']:p for p in original['plans']}
    if data['plan'] not in known:raise ValueError('Plan reconocido requerido')
    template=known[data['plan']];p=make_plan(template['id'],ev.volumes,data['rate_m3_h'],wait_h=data['wait_h'],single=template['partition']=='single',
        baseline=template['id']=='E12_referencia',initial_C=data['initial_C'],protected=template['protected'])
    p['resource_assumption']=f"Una bomba {p['rate_m3_h']:g} m³/h y suministro continuo con relevos; capacidad hipotética, no dato docente. Equipo de enfriamiento disponible para todos; sin optimizar costes."
    p['remove_at_h']=data['remove_at_h'];cfg={**original,'plans':[p],'spacing_m':data['spacing_m'],'horizon_h':data['horizon_h']}
    return validate_study(cfg,ev)
def estimate(cfg):
    ev=Evaluator();cfg=validate_study(cfg,ev);bench=read(ROOT/'results/verification/benchmark.json')
    cells=int(ev.grid(cfg['spacing_m']).occupation_mask.sum());ref=28652
    seconds=bench['case']['elapsed_s']*24*len(cfg['plans'])*(cells/ref)*(cfg['horizon_h']/408)*(900/cfg['max_step_s'])
    if seconds>1800:raise ValueError('Estimación superior a 30 min; usar malla de demostración o evaluar menos planes')
    return dict(configuration=cfg,fingerprint=signature(cfg)['fingerprint'],estimated_s=math.ceil(seconds),cases=24*len(cfg['plans']),
                occupied_cells=cells,D_h=[p['D_h'] for p in cfg['plans']],assumptions='Estimación proporcional a celdas/horizonte/pasos con benchmark medido; no garantiza tiempo exacto')
def start(app,cfg,fingerprint):
    checked=estimate(cfg)
    if checked['fingerprint']!=fingerprint:raise ValueError('Inputs cambiaron: estimar nuevamente antes de ejecutar')
    with app.lock:
        if app.closing or app.busy():raise ValueError('Espera al cálculo en curso')
        if len(app.jobs)>=6:raise ValueError('Conservar como máximo seis pruebas locales')
        key=uuid.uuid4().hex;folder=app.store/key;folder.mkdir();write_json(folder/'inputs.json',checked['configuration'])
        from datetime import datetime,timezone
        job=dict(id=key,kind='e13',legacy=False,status='queued',message='Evaluación ponderada E13 preparada',created_at=datetime.now(timezone.utc).isoformat(),configuration=cfg,configuration_sha256=fingerprint,estimate=checked)
        app.jobs[key]=job;write_json(folder/'job.json',job)
        threading.Thread(target=worker,args=(app,key),daemon=True).start();return dict(job)
def worker(app,key):
    job=app.jobs[key];folder=app.store/key
    try:
        with app.lock:
            if job['status']=='cancelled':return
            job.update(status='running',message='Python evalúa escenarios; consulta progreso calculado')
            (ROOT/'.tmp').mkdir(exist_ok=True)
            env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','TMP':str(ROOT/'.tmp'),'TEMP':str(ROOT/'.tmp')};env.pop('PYTHONPATH',None)
            with (folder/'python.log').open('w',encoding='utf8') as log:
                process=subprocess.Popen([sys.executable,'-X','utf8','-B','examples/run_e13.py','--config',str(folder/'inputs.json'),'--output',str(folder/'output')],cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            app.processes[key]=process;write_json(folder/'job.json',job)
        try:code=process.wait(timeout=1800)
        except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=10);raise ValueError('Límite de 30 min alcanzado; campos parciales no son evaluación completa')
        with app.lock:
            if job['status'] in ('cancelled','cancelling'):job.update(status='cancelled',message='Evaluación cancelada')
            elif code==0:
                result=read(folder/'output/summary.json')
                if result['status']!='PASS' or not result['all_balances_pass']:raise ValueError('Falló la verificación científica')
                job.update(status='passed',message=result['conclusion'])
            else:raise ValueError('Python no completó la evaluación; revisar registro local')
    except Exception as exc:
        with app.lock:job.update(status='failed',message=str(exc))
    finally:
        with app.lock:app.processes.pop(key,None);write_json(folder/'job.json',job)
def result(app,key):
    folder=ROOT/'results/e13' if key=='official' else app.folder(key)
    return dict(summary=read(folder/'summary.json'),cases=read(folder/'cases.json'),inputs=read(folder/'inputs.json'))
