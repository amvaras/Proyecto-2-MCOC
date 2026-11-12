"""Servidor local E11: solver existente, rutas cerradas y un trabajo a la vez."""
from argparse import ArgumentParser
from datetime import datetime,timezone
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import hashlib,hmac,io,json,mimetypes,os,re,secrets,subprocess,sys,threading,uuid,zipfile
from pathlib import Path
from urllib.parse import urlparse
import numpy as np
from mcoc_p2.e07.ifc import read_pours
from mcoc_p2.e08.inputs import validate_config
from mcoc_p2.e11 import webdata
from mcoc_p2.e11.pipeline import write_json as write

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
read=webdata.read
APP_ID='mcoc-e11-local'
def now():return datetime.now(timezone.utc).isoformat()
def inside(path):
    path=Path(path).absolute()
    if not path.is_relative_to(ROOT):raise ValueError('Ruta fuera de E11')
    for part in [path,*path.parents]:
        if part==ROOT:break
        if part.is_symlink() or part.is_junction():raise ValueError('No se admiten enlaces')
    if not path.resolve().is_relative_to(ROOT):raise ValueError('Ruta no permitida')
    return path

class Application:
    def __init__(self,store=None):
        self.store=inside(store or ROOT/'results/web_runs');self.store.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock();self.jobs={};self.processes={};self.cache={};self.token=secrets.token_urlsafe(32)
        self.models={'default':ROOT/'geometry/foundation.ifc'};self.reference=ROOT/'results/e11';self.verification=None;self.closing=False;self.native_process=None
        self.snapshots={p.relative_to(ROOT).as_posix():p for p in (ROOT/'data/weather').iterdir() if p.is_dir() and not p.is_symlink()}
        for path in self.store.glob('*/job.json'):
            item=read(path)
            if not re.fullmatch('[a-f0-9]{32}',item.get('id','')):continue
            if item['status'] in ('queued','running','cancelling'):item.update(status='cancelled',message='Interrumpido al cerrar el servidor');write(path,item)
            self.jobs[item['id']]=item
            model=ROOT/item.get('configuration',{}).get('ifc','geometry/foundation.ifc')
            if (path.parent/'model.ifc').is_file():model=path.parent/'model.ifc'
            self.models[item['id']]=inside(model)

    def model_info(self,key='default'):
        if key not in self.models:raise ValueError('Modelo desconocido')
        solids,meta=read_pours(self.models[key])
        return solids,dict(id=key,name=self.models[key].name,metadata=meta,pours=[dict(vertida_id=s.pour_id,name=s.name,volume_m3=s.mesh.volume) for s in solids])

    def folder(self,key):
        if key in ('official','reference'):return self.reference
        if key not in self.jobs or self.jobs[key]['status']!='passed':raise ValueError('La ejecución aún no tiene resultados completos')
        return inside(self.store/key/'output')

    def vtk_folder(self,key):return ROOT/'vtk/e11' if key in ('official','reference') else inside(self.store/key/'vtk')
    def busy(self):return self.verification is not None or any(j['status'] in ('queued','running','cancelling') for j in self.jobs.values())

    def start(self,cfg,model_id='default'):
        with self.lock:
            if self.closing or self.busy():raise ValueError('Ya hay un cálculo o verificación en ejecución')
            if len(self.jobs)>=6:raise ValueError('Hay seis ejecuciones conservadas; retira una ejecución para continuar')
            if model_id not in self.models:raise ValueError('Modelo desconocido')
            legacy='physics' not in cfg
            cfg=validate_config(cfg,self.model_info(model_id)[0]) if legacy else webdata.validate_web(cfg,self.models[model_id],self.snapshots)
            key=uuid.uuid4().hex;folder=self.store/key;folder.mkdir()
            if legacy:
                (folder/'model.ifc').write_bytes(self.models[model_id].read_bytes());self.models[key]=folder/'model.ifc'
            else:
                cfg['ifc']=self.models[model_id].relative_to(ROOT).as_posix();self.models[key]=self.models[model_id]
            write(folder/'inputs.json',cfg)
            job=dict(id=key,status='queued',message='Validado; preparando Python',created_at=now(),configuration=cfg,legacy=legacy,
                     configuration_sha256=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest(),
                     ifc_sha256=webdata.digest(self.models[key]),code_sha256=webdata.digest(ROOT/'src/mcoc_p2/e11/pipeline.py'))
            self.jobs[key]=job;write(folder/'job.json',job)
            threading.Thread(target=self.worker,args=(key,),daemon=True).start();return dict(job)

    def worker(self,key):
        folder=self.store/key;job=self.jobs[key]
        try:
            with self.lock:
                if job['status']=='cancelled':return
                job.update(status='running',message='Python integra la fundación: clima variable y control constante');write(folder/'job.json',job)
                (ROOT/'.tmp').mkdir(exist_ok=True)
                env={**os.environ,'PYTHONNOUSERSITE':'1','PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8','TMP':str(ROOT/'.tmp'),'TEMP':str(ROOT/'.tmp')}
                env.pop('PYTHONPATH',None)
                if job['legacy']:
                    args=['examples/run_e08.py','--config',str(folder/'inputs.json'),'--ifc',str(folder/'model.ifc'),'--output',str(folder/'output')]
                else:
                    args=['examples/run_e11.py','--config',str(folder/'inputs.json'),'--output',str(folder/'output'),'--vtk-dir',str(folder/'vtk'),'--figures-dir',str(folder/'figures')]
                with (folder/'python.log').open('w',encoding='utf-8') as log:
                    process=subprocess.Popen([sys.executable,'-X','utf8','-B',*args],cwd=ROOT,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
                self.processes[key]=process
            try:code=process.wait(timeout=180)
            except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=10);raise ValueError('Se superaron 180 s; usa una grilla más gruesa')
            with self.lock:
                if job['status'] in ('cancelled','cancelling'):job.update(status='cancelled',message='Cálculo cancelado; no se muestran campos parciales')
                elif code==0:
                    report=read(folder/'output/summary.json');checks=report['checks']
                    passed=all(checks.values()) if job['legacy'] else all(all(v.values()) for v in checks.values())
                    if report['status']!='PASS' or not passed:raise ValueError('Falló una comprobación científica')
                    job.update(status='passed',message='Completado: campos nuevos, VTK y balances verificados')
                else:
                    lines=(folder/'python.log').read_text(encoding='utf-8',errors='replace').splitlines()
                    message=next((line for line in reversed(lines) if re.match(r'^[A-Za-z]+(?:Error|Exception):|^ERROR:',line)),'Python no pudo completar el cálculo')
                    job.update(status='failed',message=message.replace(str(ROOT),'E11'))
        except Exception as exc:
            with self.lock:job.update(status='failed',message=str(exc).replace(str(ROOT),'E11'))
        finally:
            with self.lock:self.processes.pop(key,None);job['finished_at']=now();write(folder/'job.json',job)

    def snapshot(self,key):
        with self.lock:
            if key not in self.jobs:raise ValueError('Ejecución desconocida')
            return dict(self.jobs[key])

    def cancel(self,key):
        with self.lock:
            if key not in self.jobs:raise ValueError('Ejecución desconocida')
            job=self.jobs[key]
            if job['status']=='queued':job.update(status='cancelled',message='Cancelado antes de integrar')
            elif job['status']=='running':
                job.update(status='cancelling',message='Cancelando proceso propio…')
                process=self.processes.get(key)
                if process and process.poll() is None:process.terminate()
            write(self.store/key/'job.json',job);return dict(job)

    def discard_plan(self,key):
        if self.busy() or (self.native_process and self.native_process.poll() is None):raise ValueError('Cierra la tarea o PyVista antes de retirar una ejecución')
        if key not in self.jobs or self.jobs[key]['status'] not in ('passed','failed','cancelled'):raise ValueError('Solo se retiran ejecuciones propias terminadas; nunca la oficial')
        root=inside(self.store/key);rows=[]
        allowed={'job.json','inputs.json','python.log','model.ifc','native_session.json','e11_native_interactive.png',
                 *['output/'+n for n in ('inputs.json','summary.json','grid.npz','fields.npz','statistics.npz','weather_steps.npz','constant_steps.npz')],
                 *['figures/'+n for n in ('e11_ambiente.png','e11_tmax.png','e11_comparacion.png','e11_flujos.png','e11_campos_finales.png')]}
        for p in sorted(root.rglob('*')):
            inside(p)
            if p.is_dir():continue
            name=p.relative_to(root).as_posix()
            if name not in allowed and not re.fullmatch(r'vtk/(state_\d{2}\.vti|e11\.pvd|manifest\.json)',name):raise ValueError('Se conserva un archivo desconocido: '+name)
            rows.append(dict(path=name,sha256=webdata.digest(p),bytes=p.stat().st_size))
        fingerprint=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
        return dict(id=key,files=rows,bytes=sum(r['bytes'] for r in rows),fingerprint=fingerprint)

    def discard(self,key,fingerprint):
        with self.lock:
            plan=self.discard_plan(key)
            if not hmac.compare_digest(plan['fingerprint'],fingerprint):raise ValueError('Los archivos cambiaron; revisar nuevamente antes de retirar')
            root=inside(self.store/key)
            for row in plan['files']:inside(root/row['path']).unlink()
            for p in sorted((p for p in root.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):inside(p).rmdir()
            root.rmdir();self.jobs.pop(key);self.models.pop(key,None);self.cache.pop(key,None)
            return dict(status='removed',id=key,files=len(plan['files']))

    def fields(self,key):
        with self.lock:
            if key not in self.cache:
                self.cache[key]=webdata.arrays(self.folder(key)/'fields.npz')
                while len(self.cache)>2:self.cache.pop(next(iter(self.cache)))
            return self.cache[key]

    def frame(self,key,index,scenario='weather'):
        if key in self.jobs and self.jobs[key]['legacy']:data=webdata.arrays(self.folder(key)/'solution.npz')['temperature_C']
        else:
            if scenario not in ('weather','constant','difference'):raise ValueError('Escenario desconocido')
            f=self.fields(key);data=f['weather_C']-f['constant_C'] if scenario=='difference' else f[scenario+'_C']
        if not isinstance(index,int) or not 0<=index<len(data):raise ValueError('Tiempo fuera del resultado')
        return data[index].astype('<f4').tobytes()

    def verify(self,kind,cfg,key):
        with self.lock:
            if self.busy():raise ValueError('Espera al cálculo o verificación en curso')
            if kind not in ('weather','result','tests'):raise ValueError('Verificación desconocida')
            self.verification=kind
        stamp=now()
        try:
            if kind=='weather':
                cfg=webdata.validate_web(cfg,self.models['default'],self.snapshots);report=webdata.weather_data(cfg)
            elif kind=='result':report=webdata.verify_result(self.folder(key),self.vtk_folder(key))
            else:
                destination=self.store/'verification';destination.mkdir(exist_ok=True)
                command=[sys.executable,'-X','utf8','-B','-m','pytest','tests/test_e11.py','tests/test_e11_web.py','-q','-p','no:cacheprovider','--junitxml='+str(destination/'tests.xml')]
                result=subprocess.run(command,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=150,encoding='utf-8',errors='replace')
                (destination/'tests.txt').write_text(result.stdout,encoding='utf-8')
                import xml.etree.ElementTree as ET
                suite=ET.parse(destination/'tests.xml').getroot().find('testsuite')
                report=dict(status='PASS' if result.returncode==0 else 'FAIL',command='pytest tests/test_e11.py tests/test_e11_web.py',
                            counts={k:int(suite.get(k,'0')) for k in ('tests','failures','errors','skipped')},output=result.stdout[-2500:].replace(str(ROOT),'E11'))
            report.update(executed_at=stamp,kind=kind);write(self.store/'verification_last.json',report);return report
        finally:
            with self.lock:self.verification=None

    def close(self):
        self.closing=True
        if self.native_process and self.native_process.poll() is None:self.native_process.terminate()
        for key in list(self.processes):self.cancel(key)
        for process in list(self.processes.values()):
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:process.kill()

def handler_for(app):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):super().setup();self.connection.settimeout(180)
        def log_message(self,*args):pass
        def send(self,data,status=200,kind='application/json; charset=utf-8',download=None):
            if not isinstance(data,bytes):data=json.dumps(data,ensure_ascii=False,allow_nan=False).encode('utf-8')
            self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)))
            for name,value in [('Cache-Control','no-store'),('X-Content-Type-Options','nosniff'),('Cross-Origin-Resource-Policy','same-origin'),
                               ('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")]:self.send_header(name,value)
            if download:self.send_header('Content-Disposition',f'attachment; filename="{download}"')
            self.end_headers()
            try:self.wfile.write(data)
            except (BrokenPipeError,ConnectionResetError):pass
        def guard(self,mutating=False):
            port=self.server.server_port;origins=(f'http://127.0.0.1:{port}',f'http://localhost:{port}')
            if self.headers.get('Host') not in (f'127.0.0.1:{port}',f'localhost:{port}'):raise ValueError('Host local no permitido')
            origin=self.headers.get('Origin')
            if origin and origin not in origins:raise ValueError('Origen no permitido')
            if self.headers.get('Sec-Fetch-Site')=='cross-site':raise ValueError('Solicitud externa rechazada')
            if mutating and (origin not in origins or not hmac.compare_digest(self.headers.get('X-E11-Token',''),app.token)):raise ValueError('Sesión local u origen no válido; recarga la aplicación')
        def do_GET(self):
            try:
                self.guard();path=urlparse(self.path).path
                static={'/':'index.html','/app.js':'app.js','/viewer.js':'viewer.js','/charts.js':'charts.js','/styles.css':'styles.css'}
                if path in static:
                    file=HERE/static[path];return self.send(file.read_bytes(),kind=mimetypes.guess_type(file)[0] or 'text/plain')
                if path=='/api/health':return self.send(dict(app=APP_ID,root_sha=hashlib.sha256(str(ROOT).encode()).hexdigest(),busy=app.busy()))
                if path=='/api/bootstrap':
                    _,info=app.model_info();cfg=read(ROOT/'configs/e11/demo.json')
                    return self.send(dict(app=APP_ID,token=app.token,configuration=cfg,model=info,snapshots=list(app.snapshots),weather=webdata.weather_data(cfg),
                                          jobs=sorted(app.jobs.values(),key=lambda j:j['created_at'],reverse=True),historical_tests=read(ROOT/'results/verification/environment.json')['final_regression']))
                if match:=re.fullmatch('/api/jobs/([a-f0-9]{32})',path):return self.send(app.snapshot(match[1]))
                if match:=re.fullmatch('/api/results/(official|reference|[a-f0-9]{32})/(data|geometry)',path):
                    key,part=match.groups();return self.send(webdata.presentation(app.folder(key)) if part=='data' else webdata.geometry(app.folder(key)))
                if match:=re.fullmatch('/api/results/(official|[a-f0-9]{32})/frame/(\\d+)/(weather|constant|difference)',path):
                    return self.send(app.frame(match[1],int(match[2]),match[3]),kind='application/octet-stream')
                if match:=re.fullmatch('/api/weather/(raw|metadata|csv)',path):
                    cfg=read(ROOT/'configs/e11/demo.json');folder=ROOT/cfg['snapshot'];name={'raw':'weather.json','metadata':'metadata.json','csv':'temperature.csv'}[match[1]]
                    return self.send((folder/name).read_bytes(),kind='text/plain; charset=utf-8')
                if match:=re.fullmatch('/files/(official|[a-f0-9]{32})/(.+)',path):
                    key,name=match.groups();base=app.folder(key)
                    allowed={'inputs.json','summary.json','grid.npz','fields.npz','statistics.npz','weather_steps.npz','constant_steps.npz'}
                    if name in allowed:file=base/name
                    elif name=='model.ifc':file=app.models['default'] if key=='official' else app.models[key]
                    elif re.fullmatch(r'(state_\d{2}\.vti|e11\.pvd|manifest\.json)',name):file=app.vtk_folder(key)/name
                    else:raise ValueError('Archivo no permitido')
                    file=inside(file);return self.send(file.read_bytes(),kind=mimetypes.guess_type(file)[0] or 'application/octet-stream',download=file.name)
                if match:=re.fullmatch('/download/(official|[a-f0-9]{32})',path):
                    key=match[1];buffer=io.BytesIO()
                    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as z:
                        for base,prefix in [(app.folder(key),'resultados'),(app.vtk_folder(key),'vtk')]:
                            for p in base.iterdir():
                                if p.is_file() and p.suffix in ('.npz','.json','.vti','.pvd'):z.write(inside(p),prefix+'/'+p.name)
                    return self.send(buffer.getvalue(),kind='application/zip',download='E11_resultados.zip')
                return self.send(dict(error='Ruta no disponible'),404)
            except (ValueError,KeyError,IndexError,OSError,AssertionError) as exc:self.send(dict(error=str(exc).replace(str(ROOT),'E11')),400)
        def do_POST(self):
            try:
                self.guard(True);path=urlparse(self.path).path;size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=20*1024*1024:raise ValueError('Solicitud vacía o demasiado grande')
                raw=self.rfile.read(size)
                if len(raw)!=size:raise ValueError('Solicitud incompleta')
                if path=='/api/models':
                    if len(raw)>2*1024*1024:raise ValueError('IFC web máximo 2 MB')
                    key=uuid.uuid4().hex;folder=app.store/'models';folder.mkdir(exist_ok=True);file=folder/(key+'.ifc');file.write_bytes(raw)
                    try:read_pours(file)
                    except Exception:file.unlink();raise ValueError('El IFC no contiene vertidas válidas')
                    app.models[key]=file;return self.send(app.model_info(key)[1],201)
                if size>100000 or self.headers.get('Content-Type')!='application/json':raise ValueError('Se requiere JSON de hasta 100 kB')
                data=json.loads(raw)
                if path=='/api/run':
                    if set(data)-{'configuration','model_id'} or 'physics' not in data['configuration']:raise ValueError('Se requiere configuración E11')
                    return self.send(app.start(data['configuration'],data.get('model_id','default')),202)
                if match:=re.fullmatch('/api/cancel/([a-f0-9]{32})',path):return self.send(app.cancel(match[1]))
                if path=='/api/validate':return self.send(dict(status='PASS',configuration=webdata.validate_web(data['configuration'],app.models[data.get('model_id','default')],app.snapshots)))
                if path=='/api/weather':return self.send(webdata.weather_data(webdata.validate_web(data['configuration'],app.models['default'],app.snapshots)))
                if path=='/api/weather-file':
                    if data['snapshot'] not in app.snapshots:raise ValueError('Snapshot desconocido')
                    name={'raw':'weather.json','metadata':'metadata.json','csv':'temperature.csv'}[data['file']]
                    webdata.validate(app.snapshots[data['snapshot']])
                    return self.send(dict(filename=name,content=(app.snapshots[data['snapshot']]/name).read_text(encoding='utf-8')))
                if path=='/api/volume':
                    with app.lock:
                        if app.busy():raise ValueError('Espera al cálculo en curso')
                        cfg=webdata.validate_web(data['configuration'],app.models[data.get('model_id','default')],app.snapshots);app.verification='volume'
                    try:
                        from mcoc_p2.e07.voxel import voxelize
                        solids,_=read_pours(app.models[data.get('model_id','default')])
                        reports=[voxelize(solids,h,margin=cfg['physics']['margin_m']).report() for h in cfg['physics']['resolutions_m']]
                        return self.send(dict(status='PASS',resolutions=[dict(spacing_m=r['spacing_m'],occupied_cells=r['occupied_cells'],volume_m3=r['volume_voxel_m3'],relative_error=r['relative_error']) for r in reports]))
                    finally:
                        with app.lock:app.verification=None
                if path=='/api/verify':return self.send(app.verify(data['kind'],data.get('configuration'),data.get('result','official')))
                if path=='/api/discard-plan':
                    with app.lock:return self.send(app.discard_plan(data['result']))
                if path=='/api/discard':return self.send(app.discard(data['result'],data['fingerprint']))
                if path=='/api/native':
                    with app.lock:
                        if app.busy():raise ValueError('Espera al cálculo en curso')
                        key=data['result'];folder=app.folder(key)
                        if app.native_process and app.native_process.poll() is None:return self.send(dict(status='already_open'))
                        log=ROOT/'results/verification/native_web_session.json' if key=='official' else app.store/key/'native_session.json'
                        app.native_process=subprocess.Popen([sys.executable,'-X','utf8','-B','scripts/view_e11_pyvista.py','--result',str(folder),'--vtk-dir',str(app.vtk_folder(key)),'--session-log',str(log)],cwd=ROOT,stdin=subprocess.DEVNULL,
                                                           creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
                    return self.send(dict(status='opened',message='Ventana PyVista solicitada para '+key))
                if path=='/api/shutdown':
                    self.send(dict(status='closing'));threading.Thread(target=self.server.shutdown,daemon=True).start();return
                return self.send(dict(error='Acción no disponible'),404)
            except (ValueError,KeyError,TypeError,OSError,RuntimeError,AssertionError,subprocess.TimeoutExpired) as exc:self.send(dict(error=str(exc).replace(str(ROOT),'E11')),400)
    return Handler

def main():
    p=ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8711);p.add_argument('--watch-parent',action='store_true');p.add_argument('--store',type=Path);args=p.parse_args()
    if not 1024<=args.port<=65535:raise ValueError('Puerto local entre 1024 y 65535')
    app=Application(args.store);server=ThreadingHTTPServer(('127.0.0.1',args.port),handler_for(app));server.daemon_threads=True
    if args.watch_parent:
        def parent_closed():
            os.read(sys.stdin.fileno(),1)  # EOF sin retener el lock del BufferedReader al cerrar Python.
            server.shutdown()
        threading.Thread(target=parent_closed,daemon=True).start()
    print(f'E11 lista: http://127.0.0.1:{server.server_port}/',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:app.close();server.server_close()
if __name__=='__main__':main()

