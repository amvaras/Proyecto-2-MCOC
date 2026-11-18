"""Sampler → inputs únicos → chunks independientes → validación → agregación.

No ejecuta el solver para un átomo ya comprobado. Las realizaciones repetidas
siguen siendo draws matemáticos independientes, no nuevos ensayos materiales.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import datetime,timezone
import hashlib,json,math,os,time,traceback
import numpy as np
from ..e11.pipeline import ROOT
from ..e13.risk import probability
from .io import read,write,fingerprint,inside,source_hashes
from .model import Model,catalog,baseline_plans
from .store import Store,claim,validate_record
from .sampling import sample_bank
from .statistics import limit_states,running_probability,clopper_pearson,zero_failure_upper

_MODEL=None;_STORE=None
def initialize(cache):
    global _MODEL,_STORE
    _MODEL=Model();_STORE=Store(cache)
def runtime_signature():
    import sys
    files=['src/mcoc_p2/e14/model.py','src/mcoc_p2/e14/statistics.py','src/mcoc_p2/e14/sampling.py','src/mcoc_p2/e14/store.py','src/mcoc_p2/e14/workflow.py','src/mcoc_p2/e13/evaluator.py','src/mcoc_p2/e13/plans.py']
    return dict(python=sys.version.split()[0],numpy=np.__version__,kernel=source_hashes(),workflow={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in files})
def prepare(config,output,*,kind='mc',chunk_size=4,cache=None):
    out=inside(output)
    if out.exists():raise ValueError('Destino nuevo requerido; para continuar usar run --resume sobre manifest.json')
    if kind not in {'mc','enumeration'} or type(chunk_size)is not int or not 1<=chunk_size<=24:raise ValueError('Tipo de ejecución/chunk inválido')
    required={'plans','spacing_m','step_s','N','master_seed'}
    if set(config)!=required or not 1<=len(config['plans'])<=12 or len({p['id'] for p in config['plans']})!=len(config['plans']):raise ValueError('Configuración completa; planes únicos y familia acotada')
    model=Model();sc=catalog()
    for item in config['plans']:model.validate(item)
    if len(config['spacing_m'])!=3 or any(type(x)not in (int,float) or not math.isfinite(x) or not .055<=x<=1.2 for x in config['spacing_m']):raise ValueError('Malla fuera de presupuesto')
    if type(config['step_s'])not in (int,float) or not 300<=config['step_s']<=1800:raise ValueError('Paso fuera de presupuesto')
    bank=sample_bank(config['master_seed'],config['N'],sc) if kind=='mc' else dict(N=24,master_seed=config['master_seed'],samples=[dict(realization=i,scenario_index=i,scenario=s['id'],seed_words=np.random.SeedSequence([config['master_seed'],i]).generate_state(4).tolist()) for i,s in enumerate(sc)],meaning='Enumeración ponderada exacta, sin error de muestreo')
    tasks=[];lookup={};mapping=[]
    for item in config['plans']:
        plan_map=[];scenario_task={}
        for draw in bank['samples']:
            if draw['scenario_index'] in scenario_task:
                plan_map.append(scenario_task[draw['scenario_index']]);continue
            scenario=sc[draw['scenario_index']];cfg,_=model.configuration(item,scenario,config['spacing_m'],config['step_s']);key=model.key(cfg)
            if key not in lookup:
                lookup[key]=len(tasks);tasks.append(dict(physics_key=key,item=item,scenario=scenario,spacing_m=config['spacing_m'],step_s=config['step_s'],representative_realization=draw['realization'],seed_words=draw['seed_words']))
            scenario_task[draw['scenario_index']]=lookup[key];plan_map.append(lookup[key])
        mapping.append(plan_map)
    store=Store(cache);hits=sum(store.get(t['physics_key']) is not None for t in tasks);new=len(tasks)-hits
    reference=read(ROOT/'results/verification/benchmark.json')['case']['elapsed_s']
    cells=int(model.engine.grid(config['spacing_m']).occupation_mask.sum());max_h=max(p['horizon_h'] for p in config['plans'])
    seconds_per=reference*(cells/28652)*(max_h/408)*(900/config['step_s'])
    manifest=dict(schema=1,kind=kind,configuration=config,scenarios=sc,bank=bank,tasks=tasks,mapping=mapping,chunk_size=chunk_size,
        chunks=[list(range(i,min(i+chunk_size,len(tasks)))) for i in range(0,len(tasks),chunk_size)],cache=str(inside(cache or ROOT/'results/e14/cache').relative_to(ROOT)),
        versions=runtime_signature(),estimate=dict(draws_per_plan=bank['N'],unique_physics=len(tasks),reused=hits,new=new,serial_s=seconds_per*new,method='Benchmark real E13 escalado por celdas/horizonte/pasos; estimación, no tiempo garantizado'),
        created_at_utc=datetime.now(timezone.utc).isoformat())
    manifest['fingerprint']=fingerprint({k:v for k,v in manifest.items() if k!='created_at_utc'})
    out.mkdir(parents=True);write(out/'manifest.json',manifest);return manifest
def load_manifest(path):
    m=read(path);actual=fingerprint({k:v for k,v in m.items() if k not in ('fingerprint','created_at_utc')})
    if actual!=m['fingerprint']:raise ValueError('Manifest alterado')
    # Versiones de Python/NumPy se registran; código y kernel deben coincidir.
    current=runtime_signature()
    if current['kernel']!=m['versions']['kernel'] or current['workflow']!=m['versions']['workflow']:raise ValueError('Inputs/código cambiaron; no reanudar resultados obsoletos')
    return m
def _execute_task(task,force=False):
    try:
        row=_STORE.evaluate(_MODEL,task['item'],task['scenario'],spacing=task['spacing_m'],step_s=task['step_s'],force=force)
        if row['physics_key']!=task['physics_key']:raise ValueError('Input efectivo distinto del manifest')
        validate_record(row)
        return dict(status='passed',physics_key=task['physics_key'],representative_realization=task['representative_realization'],seed_words=task['seed_words'],row=row)
    except Exception as exc:
        return dict(status='failed',physics_key=task['physics_key'],error_type=type(exc).__name__,error=str(exc).replace(str(ROOT),'E14'))
def execute_chunk(manifest_path,index,*,force=False,retry_failed=False):
    path=inside(manifest_path);m=load_manifest(path)
    if type(index)is not int or not 0<=index<len(m['chunks']):raise ValueError('Índice de chunk fuera de rango')
    out=path.parent/'chunks'/f'chunk-{index:04d}.json';start=time.perf_counter()
    with claim(out.with_suffix('.lock')):
        if out.exists():
            old=read(out);validate_chunk(old,m,index)
            if old['status']=='passed' or not retry_failed:return old
        if _MODEL is None or _STORE is None or _STORE.root!=inside(ROOT/m['cache']):initialize(ROOT/m['cache'])
        entries=[_execute_task(m['tasks'][j],force) for j in m['chunks'][index]]
        report=dict(manifest_fingerprint=m['fingerprint'],index=index,status='passed' if all(e['status']=='passed' for e in entries) else 'failed',entries=entries,elapsed_s=time.perf_counter()-start,pid=os.getpid(),host=__import__('socket').gethostname())
        report['content_sha256']=fingerprint({k:v for k,v in report.items() if k!='content_sha256'})
        write(out,report,replace=out.exists());return report
def validate_chunk(chunk,m,index):
    if chunk['manifest_fingerprint']!=m['fingerprint'] or chunk['index']!=index or fingerprint({k:v for k,v in chunk.items() if k!='content_sha256'})!=chunk['content_sha256']:raise ValueError('Chunk corrupto o de otro run')
    keys=[m['tasks'][j]['physics_key'] for j in m['chunks'][index]]
    if [e['physics_key'] for e in chunk['entries']]!=keys:raise ValueError('Tareas faltantes/duplicadas en chunk')
    for e in chunk['entries']:
        if e['status']=='passed':validate_record(e['row'])
        elif e['status']!='failed':raise ValueError('Estado desconocido')
    if chunk['status']!=('passed' if all(e['status']=='passed' for e in chunk['entries']) else 'failed'):raise ValueError('Estado de chunk inconsistente')
    return chunk
def run_local(manifest_path,workers=1,*,force=False,retry_failed=False,progress=None):
    if type(workers)is not int or not 1<=workers<=4:raise ValueError('De 1 a 4 procesos locales independientes')
    path=inside(manifest_path);m=load_manifest(path);start=time.perf_counter();jobs=list(range(len(m['chunks'])));done=0
    for n in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='1'
    def observe(report):
        nonlocal done
        done+=1;state=dict(status='running',completed_chunks=done,total_chunks=len(jobs),last_status=report['status'],elapsed_s=time.perf_counter()-start)
        write(path.parent/'progress.json',state,replace=True)
        if progress:progress(state)
    if workers==1:
        initialize(ROOT/m['cache'])
        for i in jobs:observe(execute_chunk(path,i,force=force,retry_failed=retry_failed))
    else:
        with ProcessPoolExecutor(max_workers=workers,initializer=initialize,initargs=(ROOT/m['cache'],)) as pool:
            future={pool.submit(execute_chunk,path,i,force=force,retry_failed=retry_failed):i for i in jobs}
            for f in as_completed(future):observe(f.result())
    result=aggregate(path);result['execution']=dict(mode='local',workers=workers,elapsed_s=time.perf_counter()-start,real_cluster=False)
    write(path.parent/'summary.json',result,replace=True);write(path.parent/'progress.json',dict(status='passed',completed_chunks=len(jobs),total_chunks=len(jobs)),replace=True);return result
def aggregate(manifest_path):
    path=inside(manifest_path);m=load_manifest(path);entries={};failed=[]
    for i,indices in enumerate(m['chunks']):
        p=path.parent/'chunks'/f'chunk-{i:04d}.json'
        if not p.exists():raise ValueError('Falta chunk: no estimar Pf con una muestra incompleta')
        chunk=validate_chunk(read(p),m,i)
        for e in chunk['entries']:
            if e['physics_key'] in entries:raise ValueError('Resultado físico duplicado en chunks')
            entries[e['physics_key']]=e
            if e['status']!='passed':failed.append(e)
    if failed:
        write(path.parent/'errors.json',dict(status='failed',failed=failed,meaning='No contar fallo numérico como éxito térmico ni omitir realizaciones'),replace=True)
        raise ValueError('Realizaciones con errores: revisar errors.json y reanudar con retry-failed')
    if (path.parent/'errors.json').exists():
        old=read(path.parent/'errors.json');write(path.parent/'errors.json',{**old,'status':'resolved','unresolved':0},replace=True)
    reports=[]
    for pi,item in enumerate(m['configuration']['plans']):
        rows=[entries[m['tasks'][j]['physics_key']]['row'] for j in m['mapping'][pi]];states=limit_states([r['Tmax_C'] for r in rows],[r['delta_C'] for r in rows])
        if m['kind']=='enumeration':
            adjusted=[{**r,'weight':m['scenarios'][i]['weight']} for i,r in enumerate(rows)];stats=probability(adjusted);stats['interval_type']='Ninguno: enumeración exacta del modelo discreto'
        else:
            n=len(rows);stats={name:float(states[key].mean()) for name,key in [('P_T','fail_T'),('P_delta','fail_delta'),('P_joint','fail_joint')]}
            stats.update(N=n,failures=int(states['fail_joint'].sum()),CI=clopper_pearson(int(states['fail_joint'].sum()),n),Pf_N=running_probability(states['fail_joint']),marginal_CI={name:clopper_pearson(int(states[key].sum()),n) for name,key in [('P_T','fail_T'),('P_delta','fail_delta')]},interval_type='Clopper–Pearson bilateral 95%, condicional al modelo y draws IID; no IC de error numérico/epistemológico',feasible_estimate=stats['P_joint']<=.05,zero_failures_one_sided_upper95=zero_failure_upper(n) if not states['fail_joint'].any() else None)
        reports.append({**stats,'plan':item['id'],'D_h':item['construction']['D_h'],'Tmax_C':max(r['Tmax_C'] for r in rows),'delta_C':max(r['delta_C'] for r in rows)})
    return dict(status='PASS',kind=m['kind'],manifest_fingerprint=m['fingerprint'],plans=reports,unique_physics=len(entries),cache_hits=sum(e['row'].get('cache_hit',False) for e in entries.values()),
        scenario_model='24 átomos E13, mismos pesos hipotéticos e independencia material/clima',sampling_caveat='Remuestreo de funciones deterministas de ocho curvas y tres historias; no nuevos ensayos ni confiabilidad real de obra',master_seed=m['configuration']['master_seed'])
