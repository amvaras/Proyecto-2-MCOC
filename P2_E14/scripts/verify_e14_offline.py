"""Revalidar el conjunto oficial sin Internet ni integrar temperatura.

--seal crea una sola vez el índice SHA256 y la tabla oficial. La ejecución
normal es de lectura; --report guarda una evidencia actual separada.
"""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import argparse,csv,hashlib,io,json,math,socket,subprocess,time
from contextlib import contextmanager,ExitStack
from unittest.mock import patch
import numpy as np
from PIL import Image
from mcoc_p2.e14.io import read,write,fingerprint,inside,source_hashes
from mcoc_p2.e14.model import Model
from mcoc_p2.e14.store import Store
from mcoc_p2.e14.workflow import load_manifest,validate_chunk,aggregate
from mcoc_p2.e14.sampling import sample_bank
from mcoc_p2.e12.source import read_sources,load_curve
from mcoc_p2.e13.weather import validate_snapshot,reduce_members,member_payload
from mcoc_p2.e10.weather import utc_time,WeatherWindow

CATALOG=ROOT/'results/e14/official.json'
TABLE=ROOT/'results/e14/plans.csv'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

@contextmanager
def offline_readonly():
    """Bloqueo del proceso propio; no cambia red o seguridad de Windows."""
    import urllib.request,requests.sessions
    import mcoc_p2.e08.solver as solver
    import mcoc_p2.e13.evaluator as evaluator
    import mcoc_p2.e14.workflow as workflow
    def network(*a,**kw):raise RuntimeError('Verificación offline: red bloqueada')
    def simulation(*a,**kw):raise RuntimeError('Verificación de lectura: simulación prohibida')
    with ExitStack() as stack:
        for obj,name in [(socket.socket,'connect'),(socket.socket,'connect_ex'),(socket,'create_connection'),(urllib.request,'urlopen'),(requests.sessions.Session,'request')]:stack.enter_context(patch.object(obj,name,network))
        for obj,name in [(solver,'simulate'),(evaluator,'simulate'),(Model,'evaluate'),(Store,'evaluate'),(workflow,'execute_chunk'),(workflow,'run_local')]:stack.enter_context(patch.object(obj,name,simulation))
        yield

def artifact_paths():
    paths=set()
    for name in ('data','configs','geometry','src','web','examples','scripts','tests','figures','vtk','results/e13','results/e14'):
        for p in (ROOT/name).rglob('*'):
            if p.is_symlink() or p.is_junction():raise ValueError('No seguir enlaces: '+str(p))
            if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc','.pyo','.lock'}:
                if p not in {CATALOG,TABLE} and not p.is_relative_to(ROOT/'results/e14/hpc'):paths.add(inside(p))
    for name in ('pyproject.toml','requirements-lock.txt','.gitattributes','.gitignore','AGENTS.md','README.md','Iniciar E14.bat','results/verification/controls.json','results/verification/benchmark.json','results/verification/fields_e14.json','results/verification/numerics_e14.json','results/verification/parallel.json'):
        paths.add(inside(ROOT/name))
    return sorted(paths,key=lambda p:p.relative_to(ROOT).as_posix())

def artifact_inventory():return [dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in artifact_paths()]

# On a successor checkout these paths have a separate live implementation.
# Match their archived bytes against the already sealed digest at the E14 tag.
E14_SUCCESSOR_FILES = {
    '.gitignore','README.md','scripts/clean_project.py','scripts/verify_e14_offline.py',
    'tests/test_e11_web.py','tests/test_e12.py','tests/test_e14_web.py',
    'web/app.js','web/charts.js','web/index.html','web/servidor.py','web/styles.css',
}

def check_inventory(rows, *, archived=False):
    if len({r['path'] for r in rows})!=len(rows):raise ValueError('Inventario con rutas duplicadas')
    for r in rows:
        p=inside(ROOT/r['path'])
        if p.is_file() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256']:
            continue
        if archived and r['path'] in E14_SUCCESSOR_FILES:
            blob=subprocess.run(['git','show','entrega-e14:P2_E14/'+r['path']], cwd=ROOT,
                                capture_output=True,check=True).stdout
            if len(blob)==r['bytes'] and hashlib.sha256(blob).hexdigest()==r['sha256']:
                continue
        raise ValueError('Artefacto E14 cambiado o ausente: '+r['path'])

def table_bytes(plans):
    out=io.StringIO(newline='');w=csv.DictWriter(out,fieldnames=['plan','D_h','horizon_h','Tmax_C','delta_C','g_T_C','g_Delta_C','Pf_exact','Pf_MC','CI95_low','CI95_high','feasible']);w.writeheader()
    for p in plans:w.writerow({k:p[k] for k in w.fieldnames})
    return out.getvalue().encode('utf8')

def same_report(saved, fresh, interval=False):
    # libm puede variar en los últimos ULP de la inversión binomial.
    if isinstance(saved,dict) and isinstance(fresh,dict):
        return saved.keys()==fresh.keys() and all(
            same_report(value,fresh[key],interval or key in ('CI','marginal_CI'))
            for key,value in saved.items())
    if isinstance(saved,list) and isinstance(fresh,list):
        return len(saved)==len(fresh) and all(same_report(a,b,interval) for a,b in zip(saved,fresh))
    if interval and isinstance(saved,float) and isinstance(fresh,float):
        return math.isclose(saved,fresh,abs_tol=2e-14,rel_tol=0)
    return saved==fresh

def inspect(*,fields=True,artifact_rows=None):
    """Lectura independiente de configuraciones, resultados y fuentes."""
    started=time.perf_counter();reports={};sets={};index=[];model=Model();store=Store()
    baseline=read(ROOT/'results/verification/closure_e14.json')
    if source_hashes()!=baseline['kernel_sha256']:raise ValueError('Kernel o datos distintos de E14 verificada')
    for kind in ('enumeration','monte_carlo'):
        folder=ROOT/'results/e14'/kind;m=load_manifest(folder/'manifest.json');saved=read(folder/'summary.json');fresh=aggregate(folder/'manifest.json')
        assert same_report(saved['plans'],fresh['plans']) and fresh['manifest_fingerprint']==saved['manifest_fingerprint']
        entries={}
        for i in range(len(m['chunks'])):
            path=folder/'chunks'/f'chunk-{i:04d}.json';chunk=validate_chunk(read(path),m,i);assert chunk['status']=='passed'
            for position,e in enumerate(chunk['entries']):
                r=e['row'];key=e['physics_key'];assert key not in entries;entries[key]=r
                assert r['fail_joint']==(r['Tmax_C']>70 or r['delta_C']>20)
                assert r['g_T']==70-r['Tmax_C'] and r['g_Delta']==20-r['delta_C']
                if kind=='enumeration':
                    task=next(t for t in m['tasks'] if t['physics_key']==key)
                    c,_=model.configuration(task['item'],task['scenario'],task['spacing_m'],task['step_s'])
                    assert c==r['configuration'] and model.key(c)==key
                    cached=store.get(key);assert cached is not None and cached['Tmax_C']==r['Tmax_C'] and cached['delta_C']==r['delta_C']
                    index.append(dict(physics_key=key,plan=r['plan'],scenario=r['scenario'],chunk=path.relative_to(ROOT).as_posix(),entry=position))
        assert len(entries)==192 and len(m['configuration']['plans'])==8
        for pi,p in enumerate(saved['plans']):
            rr=[entries[m['tasks'][j]['physics_key']] for j in m['mapping'][pi]]
            failures=[r['Tmax_C']>70 or r['delta_C']>20 for r in rr]
            expected=math.fsum(s['weight']*f for s,f in zip(m['scenarios'],failures)) if kind=='enumeration' else sum(failures)/len(failures)
            assert abs(expected-p['P_joint'])<2e-15
        if kind=='monte_carlo':assert m['bank']==sample_bank(m['configuration']['master_seed'],m['configuration']['N'],m['scenarios'])
        sets[kind]=entries;reports[kind]=saved
    assert sets['enumeration'].keys()==sets['monte_carlo'].keys()
    assert all(sets['enumeration'][k]['configuration']==sets['monte_carlo'][k]['configuration'] for k in sets['enumeration'])
    curves,meta=read_sources(ROOT/'data/hydration/source_terms.txt');assert len(curves)==8
    reduction=read(ROOT/'data/ensemble/reduction.json');raw=read(ROOT/'data/ensemble/raw.json')
    assert sha(ROOT/'data/ensemble/raw.json')==reduction['raw_sha256']
    payloads=[member_payload(raw,i) for i in range(31)]
    seconds=np.array(payloads[0]['hourly']['time']);start=utc_time(reduction['start_utc']).timestamp();use=(seconds>=start)&(seconds<=start+reduction['reduction_h']*3600)
    reduced=reduce_members(np.array([p['hourly']['temperature_2m'] for p in payloads])[:,use])
    for k in ('medoids','assignment','counts','weights'):assert reduced[k]==reduction[k]
    for path in reduction['snapshots']:
        snap=validate_snapshot(ROOT/path);WeatherWindow(snap,reduction['start_utc'],744*3600,tail=None)
    for r in sets['enumeration'].values():
        c=r['configuration'];assert c['snapshot'] in reduction['snapshots']
        curve,_=load_curve(ROOT/c['experimental_source']['file'],c['experimental_source']['curve'],c['experimental_source']['tail'],c['experimental_source']['tau_s'])
        assert c['physics']['hydration']['H_vol_J_m3']==curve.H_vol_J_m3
    figures=read(ROOT/'results/e14/figures.json');assert figures['count']==len(figures['figures'])==15
    for row in figures['figures']:
        p=ROOT/row['path'];assert sha(p)==row['sha256']
        with Image.open(p) as im:
            embedded=json.loads(im.info['provenance']);im.verify()
        assert embedded['source']==row['source'] and embedded['context']==row['context']
    cfg=read(ROOT/'configs/e14/study.json');plans=[]
    for item,p,q in zip(cfg['plans'],reports['enumeration']['plans'],reports['monte_carlo']['plans']):
        assert item['id']==p['plan']==q['plan'] and item['construction']['D_h']==p['D_h']==q['D_h']
        plans.append(dict(plan=p['plan'],D_h=p['D_h'],horizon_h=item['horizon_h'],Tmax_C=p['Tmax_C'],delta_C=p['delta_C'],g_T_C=70-p['Tmax_C'],g_Delta_C=20-p['delta_C'],Pf_exact=p['P_joint'],Pf_MC=q['P_joint'],CI95_low=q['CI'][0],CI95_high=q['CI'][1],feasible=p['P_joint']<=.05))
    assert not any(p['feasible'] for p in plans)
    previous=read(ROOT/'results/verification/fields_e14.json');field_report=None
    if fields:
        from mcoc_p2.e12.verification import verify
        field_report=verify(ROOT/'results/e14/representative',ROOT/'vtk/e14')
        assert field_report==previous
    else:assert previous['status']=='PASS'
    payload=dict(schema=1,role='Conjunto científico oficial E14 para preparar F02; sin informe final ni diapositivas',unique_thermal_cases=192,plans=plans,
        realization_N_per_plan=10000,master_seed=cfg['master_seed'],case_index=sorted(index,key=lambda r:(r['plan'],r['scenario'])),
        enumeration_fingerprint=reports['enumeration']['manifest_fingerprint'],monte_carlo_fingerprint=reports['monte_carlo']['manifest_fingerprint'],
        data=dict(source_sha256=meta['sha256'],curves=meta['curves'],ensemble_sha256=reduction['raw_sha256'],medoids=reduction['medoids'],climate_weights=reduction['weights']),
        limits=dict(Tmax_C=70,delta_C=20,Pf_joint=.05),criterion='OR estricto; ΔT global simultáneo sobre Ω activo y S25 aproximado',
        conclusion='Ninguno de los ocho planes evaluados cumple Pf<=5%; no demuestra imposibilidad global',
        caveat='Pesos/independencia hipotéticos; IC solo de muestreo condicional. Sin validación de obra ni convergencia numérica completa.',artifacts=artifact_inventory() if artifact_rows is None else artifact_rows)
    payload['fingerprint']=fingerprint(payload)
    return payload,dict(status='PASS',network='BLOCKED in process',thermal_integrator='BLOCKED in process',new_thermal_simulations=0,unique_cases_checked=192,plans_checked=8,curves_checked=8,climate_histories_checked=3,figures_checked=15,
        fields_reconstructed=fields,all_time_fields=previous['all_time_fields'],catalog_fingerprint=payload['fingerprint'],elapsed_s=time.perf_counter()-started)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--seal',action='store_true');p.add_argument('--report',type=Path);p.add_argument('--quick',action='store_true',help='Sin reconstrucción completa de S25; SHA de todos los campos siempre obligatorio');a=p.parse_args()
    if not a.seal:
        sealed=read(CATALOG);assert sealed['fingerprint']==fingerprint({k:v for k,v in sealed.items() if k!='fingerprint'});check_inventory(sealed['artifacts'], archived=True)
    with offline_readonly():payload,report=inspect(fields=not a.quick, artifact_rows=None if a.seal else sealed['artifacts'])
    if a.seal:
        raw=table_bytes(payload['plans'])
        if TABLE.exists() and TABLE.read_bytes()!=raw:raise ValueError('Preservar tabla diferente')
        write(CATALOG,payload)
        if not TABLE.exists():TABLE.write_bytes(raw)
    else:
        assert payload==sealed and TABLE.read_bytes()==table_bytes(payload['plans'])
    if a.report:
        target=inside(a.report)
        if target!=ROOT/'results/verification/offline_e14.json':raise ValueError('Usar results/verification/offline_e14.json; no sobrescribir artefactos oficiales')
        write(target,report,replace=True)
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
