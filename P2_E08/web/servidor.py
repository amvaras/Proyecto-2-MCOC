"""Servidor local E08: escenarios Python, fotogramas reales y visor sin CDN."""
from argparse import ArgumentParser
from datetime import datetime,timezone
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import io
import json
import mimetypes
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
from urllib.parse import urlparse
import uuid
import webbrowser
import zipfile
import numpy as np
from mcoc_p2.e07.ifc import read_pours
from mcoc_p2.e08.inputs import validate_config

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write(path,data):Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


class Application:
    def __init__(self,store=None):
        self.store=Path(store or ROOT/'results/interfaz_e08');self.store.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock();self.jobs={};self.processes={};self.cache={}
        self.models={'default':ROOT/'geometry/foundation.ifc'}
        self.reference=ROOT/'evidencias/e08/nominal'
        if (self.reference/'model.ifc').is_file():self.models['reference']=self.reference/'model.ifc'
        for path in self.store.glob('*/job.json'):
            item=read(path)
            if item['status'] in ('queued','running'):item.update(status='cancelled',message='Ejecución interrumpida al cerrar el servidor.')
            self.jobs[item['id']]=item
            if (path.parent/'model.ifc').is_file():self.models[item['id']]=path.parent/'model.ifc'

    def model_info(self,key='default'):
        if key not in self.models:raise ValueError('Selecciona nuevamente el IFC')
        solids,meta=read_pours(self.models[key])
        return solids,dict(id=key,name=self.models[key].name,metadata=meta,
            pours=[dict(vertida_id=s.pour_id,name=s.name,volume_m3=s.mesh.volume) for s in solids])

    def folder(self,key):
        if key=='reference' and (self.reference/'summary.json').is_file():return self.reference
        if key not in self.jobs or self.jobs[key]['status']!='passed':raise ValueError('El escenario aún no tiene resultados completos')
        return self.store/key/'output'

    def snapshot(self,key):
        with self.lock:
            if key not in self.jobs:raise ValueError('Escenario desconocido')
            result=dict(self.jobs[key])
            progress=self.store/key/'output/progress.json'
            if progress.exists():
                try:result['progress']=read(progress)
                except (OSError,ValueError):pass
            log=self.store/key/'python.log'
            if log.exists():result['log']=log.read_text(encoding='utf-8',errors='replace')[-10000:]
            return result

    def start(self,cfg,model_id):
        with self.lock:
            if any(j['status'] in ('queued','running') for j in self.jobs.values()):raise ValueError('Espera o cancela el escenario en curso')
            solids,info=self.model_info(model_id);cfg=validate_config(cfg,solids)
            key=uuid.uuid4().hex;folder=self.store/key;folder.mkdir()
            write(folder/'inputs.json',cfg);(folder/'model.ifc').write_bytes(self.models[model_id].read_bytes())
            self.models[key]=folder/'model.ifc'
            job=dict(id=key,status='queued',message='Preparando simulación',created_at=datetime.now(timezone.utc).isoformat(),
                     configuration=cfg,model_name=info['name'])
            self.jobs[key]=job;write(folder/'job.json',job)
            threading.Thread(target=self.worker,args=(key,),daemon=True).start()
            return dict(job)

    def worker(self,key):
        folder=self.store/key;job=self.jobs[key]
        try:
            with self.lock:
                if job['status']=='cancelled':return
                job.update(status='running',message='Integrando temperatura por etapas…')
                env={**os.environ,'PYTHONNOUSERSITE':'1','PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8'}
                env.pop('PYTHONPATH',None)
                with (folder/'python.log').open('w',encoding='utf-8') as log:
                    process=subprocess.Popen([sys.executable,'-X','utf8','-B',str(ROOT/'examples/run_e08.py'),
                        '--config',str(folder/'inputs.json'),'--ifc',str(folder/'model.ifc'),
                        '--output',str(folder/'output')],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
                self.processes[key]=process
            code=process.wait()
            with self.lock:
                if job['status']!='cancelled':
                    if code==0 and (folder/'output/summary.json').is_file():
                        report=read(folder/'output/summary.json')
                        if report['status']!='PASS' or not all(report['checks'].values()):raise ValueError('Una verificación científica falló')
                        job.update(status='passed',message='Simulación terminada y balance verificado')
                    else:
                        lines=(folder/'python.log').read_text(encoding='utf-8',errors='replace').splitlines()
                        job.update(status='failed',message=next((v for v in reversed(lines) if v.startswith('ERROR:')),'Python no pudo terminar; revisa el registro'))
        except Exception as exc:
            with self.lock:job.update(status='failed',message=str(exc))
        finally:
            with self.lock:
                self.processes.pop(key,None);job['finished_at']=datetime.now(timezone.utc).isoformat();write(folder/'job.json',job)

    def cancel(self,key):
        with self.lock:
            if key not in self.jobs:raise ValueError('Escenario desconocido')
            job=self.jobs[key]
            if job['status'] in ('queued','running'):
                job.update(status='cancelled',message='Ejecución cancelada')
                process=self.processes.get(key)
                if process and process.poll() is None:process.terminate()
                write(self.store/key/'job.json',job)
            return dict(job)

    def frame(self,key,index):
        folder=self.folder(key)
        with self.lock:
            if key not in self.cache:
                with np.load(folder/'solution.npz',allow_pickle=False) as data:self.cache[key]=data['temperature_C']
                while len(self.cache)>2:self.cache.pop(next(iter(self.cache)))
            data=self.cache[key]
            if index<0 or index>=len(data):raise ValueError('Fotograma fuera de rango')
            return data[index].astype('<f4').tobytes()


def handler_for(app):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,data,status=200,kind='application/json; charset=utf-8',download=None):
            if not isinstance(data,bytes):data=json.dumps(data,ensure_ascii=False,allow_nan=False).encode('utf-8')
            self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            if download:self.send_header('Content-Disposition',f'attachment; filename="{download}"')
            self.end_headers();self.wfile.write(data)
        def guard(self):
            port=self.server.server_port
            if self.headers.get('Host') not in (f'localhost:{port}',f'127.0.0.1:{port}'):raise ValueError('Usa localhost')
            origin=self.headers.get('Origin')
            if origin and origin not in (f'http://localhost:{port}',f'http://127.0.0.1:{port}'):raise ValueError('Origen no permitido')
        def do_GET(self):
            try:
                self.guard();path=urlparse(self.path).path
                if path in ('/','/app.js','/styles.css'):
                    file=HERE/('index.html' if path=='/' else path[1:]);return self.send(file.read_bytes(),kind=mimetypes.guess_type(file)[0] or 'text/plain')
                if path=='/api/bootstrap':
                    _,info=app.model_info()
                    return self.send(dict(configuration=read(ROOT/'configs/e08/demo.json'),model=info,
                        reference=(app.reference/'summary.json').exists(),jobs=sorted(app.jobs.values(),key=lambda j:j['created_at'],reverse=True)))
                if match:=re.fullmatch(r'/api/jobs/([a-f0-9]{32})',path):return self.send(app.snapshot(match[1]))
                if match:=re.fullmatch(r'/api/results/(reference|[a-f0-9]{32})/(summary|geometry)',path):
                    return self.send((app.folder(match[1])/(match[2]+'.json')).read_bytes())
                if match:=re.fullmatch(r'/api/results/(reference|[a-f0-9]{32})/frame/(\d+)',path):
                    return self.send(app.frame(match[1],int(match[2])),kind='application/octet-stream')
                if match:=re.fullmatch(r'/files/(reference|[a-f0-9]{32})/(.+)',path):
                    folder=app.folder(match[1]);name=match[2]
                    allowed={'inputs.json','summary.json','voxels.npz','solution.npz','model.ifc','geometry.json',
                             *['figures/'+s for s in ('e08_temperaturas.png','e08_energia.png','e08_volumen.png','e08_final_3d.png')]}
                    if name not in allowed:raise ValueError('Archivo no permitido')
                    file=folder/name;kind=mimetypes.guess_type(file)[0] or 'application/octet-stream'
                    return self.send(file.read_bytes(),kind=kind,download=file.name if file.suffix not in ('.png',) else None)
                if match:=re.fullmatch(r'/download/(reference|[a-f0-9]{32})',path):
                    folder=app.folder(match[1]);buffer=io.BytesIO()
                    with zipfile.ZipFile(buffer,'w',zipfile.ZIP_DEFLATED) as archive:
                        for file in folder.rglob('*'):
                            if file.is_file():archive.write(file,file.relative_to(folder))
                    return self.send(buffer.getvalue(),kind='application/zip',download='E08_escenario.zip')
                self.send(dict(error='Ruta no encontrada'),404)
            except (ValueError,KeyError,IndexError,OSError) as exc:self.send(dict(error=str(exc)),400)
        def do_POST(self):
            try:
                self.guard();path=urlparse(self.path).path
                size=int(self.headers.get('Content-Length','0'))
                if size<0 or size>20*1024*1024:raise ValueError('Archivo o solicitud demasiado grande')
                raw=self.rfile.read(size)
                if path=='/api/models':
                    key=uuid.uuid4().hex;folder=app.store/'models';folder.mkdir(exist_ok=True)
                    file=folder/(key+'.ifc');file.write_bytes(raw)
                    read_pours(file);app.models[key]=file
                    return self.send(app.model_info(key)[1],201)
                if size>2*1024*1024:raise ValueError('JSON demasiado grande')
                data=json.loads(raw)
                if path=='/api/run':return self.send(app.start(data['configuration'],data.get('model_id','default')),202)
                if match:=re.fullmatch(r'/api/cancel/([a-f0-9]{32})',path):return self.send(app.cancel(match[1]))
                self.send(dict(error='Ruta no encontrada'),404)
            except (ValueError,KeyError,TypeError,OSError,RuntimeError) as exc:self.send(dict(error=str(exc)),400)
    return Handler


def main():
    p=ArgumentParser(description=__doc__);p.add_argument('--port',type=int,default=8768);p.add_argument('--open',action='store_true')
    args=p.parse_args();app=Application();server=ThreadingHTTPServer(('127.0.0.1',args.port),handler_for(app))
    url=f'http://127.0.0.1:{args.port}/';print('E08 lista: '+url,flush=True)
    if args.open:
        chrome=next((Path(base)/'Google/Chrome/Application/chrome.exe' for base in
                     [os.environ.get('PROGRAMFILES',''),os.environ.get('PROGRAMFILES(X86)',''),os.environ.get('LOCALAPPDATA','')]
                     if (Path(base)/'Google/Chrome/Application/chrome.exe').is_file()),None)
        if chrome:subprocess.Popen([str(chrome),url])
        else:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()
