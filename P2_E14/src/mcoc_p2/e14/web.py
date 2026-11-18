"""Soporte E14 en la aplicación existente: coste previo, jobs y cancelación cooperativa."""
from copy import deepcopy
from pathlib import Path
import json,math,os,subprocess,sys,threading,uuid
from datetime import datetime,timezone
from ..e11.pipeline import ROOT
from .io import read,write,fingerprint
from .model import Model,catalog
from .sampling import sample_bank
from .store import Store
def bootstrap(app):
    cfg=read(ROOT/'configs/e14/study.json');reports={}
    for name in ('enumeration','monte_carlo'):
        p=ROOT/'results/e14'/name/'summary.json';reports[name]=read(p) if p.exists() else None
    return dict(configuration=cfg,reports=reports,scenarios=catalog(),jobs=[j for j in app.jobs.values() if j.get('kind')=='e14'],
        model='Monte Carlo IID condicional a los 24 átomos y pesos hipotéticos E13; repetir una curva no crea ensayos nuevos',
        HPC='Workflow local y Slurm validado localmente; clúster real NO VERIFICADO')
def parameters(data):
    required={'plan_ids','N','master_seed','kind','spacing_m','temperature_C','insulation_m','remove_at_h'}
    if set(data)!=required or data['kind'] not in {'mc','enumeration'}:raise ValueError('Parámetros E14 incompletos')
    original=read(ROOT/'configs/e14/study.json');known={p['id']:p for p in original['plans']}
    if not isinstance(data['plan_ids'],list) or not 1<=len(data['plan_ids'])<=8 or len(set(data['plan_ids']))!=len(data['plan_ids']) or set(data['plan_ids'])-known.keys():raise ValueError('Planes reconocidos, sin duplicados')
    cfg={**original,'plans':[deepcopy(known[k]) for k in data['plan_ids']],'N':data['N'],'master_seed':data['master_seed'],'spacing_m':data['spacing_m']}
    if type(cfg['N'])is not int or not 1<=cfg['N']<=20000:raise ValueError('La web admite N entre 1 y 20000')
    # Las decisiones editables son experimentos; nunca reemplazan el oficial.
    custom=any(data[k] is not None for k in ('temperature_C','insulation_m','remove_at_h'))
    if custom:
        if len(cfg['plans'])!=1:raise ValueError('Editar un plan a la vez')
        p=cfg['plans'][0]
        if not p['design']:raise ValueError('Para editar protecciones seleccionar un plan E14')
        p['id']='experimento_'+p['id'];p['construction']['id']=p['id']
        if data['temperature_C'] is not None:p['construction']['initial_C']=[data['temperature_C']]*5
        if data['insulation_m'] is not None:p['design']['insulation_m']=data['insulation_m']
        if data['remove_at_h'] is not None:p['construction']['remove_at_h']=data['remove_at_h']
    return cfg
def estimate(data):
    cfg=parameters(data);m=Model();sc=catalog();bank=sample_bank(cfg['master_seed'],cfg['N'],sc) if data['kind']=='mc' else dict(samples=[dict(scenario_index=i) for i in range(24)])
    selected=sorted({s['scenario_index'] for s in bank['samples']});store=Store();keys=set();hits=set()
    for p in cfg['plans']:
        m.validate(p)
        for i in selected:
            c,_=m.configuration(p,sc[i],cfg['spacing_m'],cfg['step_s']);key=m.key(c);keys.add(key)
            if store.get(key) is not None:hits.add(key)
    cells=int(m.engine.grid(cfg['spacing_m']).occupation_mask.sum());per=read(ROOT/'results/verification/benchmark.json')['case']['elapsed_s']*(cells/28652)*max(p['horizon_h'] for p in cfg['plans'])/408
    seconds=(len(keys)-len(hits))*per+2
    if cells>180000 or seconds>1800:raise ValueError('Coste estimado superior al presupuesto web; usar CLI/HPC o malla de demo')
    fp=fingerprint(dict(configuration=cfg,kind=data['kind'],kernel=m.hashes))
    return dict(configuration=cfg,kind=data['kind'],fingerprint=fp,draws_per_plan=cfg['N'] if data['kind']=='mc' else 24,unique_physics=len(keys),cache_hits=len(hits),new_physics=len(keys)-len(hits),estimated_s=math.ceil(seconds),workers_web=1,
       meaning='La web usa un proceso con cancelación segura; CLI/HPC permite realizaciones en paralelo. El coste corresponde a inputs nuevos, no a cada remuestreo.')
def start(app,data,expected):
    est=estimate(data)
    if est['fingerprint']!=expected:raise ValueError('Parámetros cambiaron; estimar nuevamente')
    with app.lock:
        if app.closing or app.busy():raise ValueError('Esperar la tarea activa')
        if len(app.jobs)>=6:raise ValueError('Seis experimentos locales conservados; retirar uno con inventario antes de continuar')
        key=uuid.uuid4().hex;folder=app.store/key;folder.mkdir();write(folder/'inputs.json',est['configuration'])
        job=dict(id=key,kind='e14',legacy=False,status='queued',created_at=datetime.now(timezone.utc).isoformat(),message='Preparando muestras y chunks E14',configuration=est['configuration'],configuration_sha256=est['fingerprint'],estimate=est)
        app.jobs[key]=job;write(folder/'job.json',job);threading.Thread(target=worker,args=(app,key),daemon=True).start();return dict(job)
def worker(app,key):
    folder=app.store/key;job=app.jobs[key]
    try:
        with app.lock:
            if job['status']=='cancelled':return
            job.update(status='running',message='Python ejecuta inputs únicos y agrega todas las realizaciones');(ROOT/'.tmp').mkdir(exist_ok=True)
            env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','TEMP':str(ROOT/'.tmp'),'TMP':str(ROOT/'.tmp')};env.pop('PYTHONPATH',None)
            with (folder/'python.log').open('w',encoding='utf8') as log:
                command=[sys.executable,'-X','utf8','-B','examples/e14_web_worker.py','--config',str(folder/'inputs.json'),'--output',str(folder/'output'),'--kind',job['estimate']['kind'],'--cancel',str(folder/'cancel.request')]
                if job.get('resume'):command.append('--resume')
                p=subprocess.Popen(command,cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
            app.processes[key]=p;write(folder/'job.json',job,replace=True)
        try:code=p.wait(timeout=1800)
        except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=10);raise ValueError('Tiempo máximo web alcanzado; se conservan resultados físicos completos para reanudar')
        with app.lock:
            if job['status']=='cancelling' or code==2:job.update(status='cancelled',message='Cancelado; una muestra incompleta no produce Pf')
            elif code==0:
                r=read(folder/'output/summary.json')
                if r['status']!='PASS':raise ValueError('Salida no verificada')
                job.update(status='passed',message='Monte Carlo/enumeración terminados y validados')
            else:raise ValueError('Falló la ejecución; consultar registro propio y reanudar con huella idéntica')
    except Exception as exc:
        with app.lock:job.update(status='failed',message=str(exc).replace(str(ROOT),'E14'))
    finally:
        with app.lock:app.processes.pop(key,None);write(folder/'job.json',job,replace=True)
def cancel(app,key):
    with app.lock:
        job=app.jobs[key]
        if job['status']=='queued':job.update(status='cancelled',message='Cancelado antes de ejecutar')
        elif job['status']=='running':
            write(app.store/key/'cancel.request',dict(requested=True));job.update(status='cancelling',message='Cancelando al terminar el input actual; no quedan procesos hijos de pool en la web')
        write(app.store/key/'job.json',job,replace=True);return dict(job)

def resume(app,key):
    from .workflow import load_manifest
    with app.lock:
        if app.busy() or key not in app.jobs:raise ValueError('Esperar tarea activa o seleccionar job propio')
        job=app.jobs[key]
        if job.get('kind')!='e14' or job['status'] not in {'failed','cancelled'}:raise ValueError('Solo reanudar un lote propio interrumpido')
        folder=app.store/key;manifest=folder/'output/manifest.json'
        if manifest.exists():load_manifest(manifest)
        marker=folder/'cancel.request'
        if marker.exists():
            before=marker.read_bytes()
            if read(marker)!={'requested':True} or marker.read_bytes()!=before:raise ValueError('Preservar marcador desconocido')
            marker.unlink()
        job.update(status='queued',message='Reanudando inputs y semillas guardados; no aplicar inputs editados de la pantalla',resume=True)
        write(folder/'job.json',job,replace=True);threading.Thread(target=worker,args=(app,key),daemon=True).start();return dict(job)

def discard_plan(app,key):
    import hashlib,re
    from .io import inside
    if app.busy() or key not in app.jobs or app.jobs[key]['status'] not in {'passed','failed','cancelled'}:raise ValueError('Solo lotes propios terminados; nunca el oficial')
    folder=inside(app.store/key);rows=[]
    allowed={'job.json','inputs.json','python.log','cancel.request','output/manifest.json','output/progress.json','output/summary.json','output/errors.json'}
    for current,dirs,names in os.walk(folder,followlinks=False):
        for name in dirs:inside(Path(current)/name)
        for name in names:
            p=inside(Path(current)/name);rel=p.relative_to(folder).as_posix()
            if rel not in allowed and not re.fullmatch(r'output/chunks/chunk-\d{4}\.json',rel):raise ValueError('Preservar archivo desconocido: '+rel)
            rows.append(dict(path=rel,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
    rows.sort(key=lambda x:x['path'])
    return dict(id=key,files=rows,bytes=sum(r['bytes'] for r in rows),fingerprint=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest())
