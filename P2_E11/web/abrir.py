"""Lanzador E11 con comprobación de identidad y cierre del proceso propio."""
import hashlib,json,os,subprocess,sys,time,urllib.request,webbrowser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];URL='http://127.0.0.1:8711/'

def running():
    try:
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(URL+'api/health',timeout=1) as response:data=json.load(response)
        return data.get('app')=='mcoc-e11-local' and data.get('root_sha')==hashlib.sha256(str(ROOT).encode()).hexdigest()
    except (OSError,ValueError):return False

def main():
    if '--check' in sys.argv:
        print('E11 activo' if running() else 'E11 no accesible');return 0 if running() else 1
    import numpy,ifcopenshell,pyvista
    process=None
    if not running():
        (ROOT/'.tmp').mkdir(exist_ok=True)
        env={**os.environ,'TMP':str(ROOT/'.tmp'),'TEMP':str(ROOT/'.tmp'),'PYTHONDONTWRITEBYTECODE':'1'}
        process=subprocess.Popen([sys.executable,'-X','utf8','-B',str(ROOT/'web/servidor.py'),'--watch-parent'],cwd=ROOT,env=env,stdin=subprocess.PIPE,
                                 creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        for _ in range(80):
            if running():break
            if process.poll() is not None:raise RuntimeError('No se pudo iniciar E11. El puerto 8711 puede estar ocupado.')
            time.sleep(.25)
        else:
            process.terminate();raise RuntimeError('E11 no respondió en 20 segundos')
    if '--no-open' not in sys.argv:webbrowser.open(URL)
    print('E11 lista: '+URL,flush=True)
    if process:
        print('Mantén abierto este lanzador. Cierra desde el botón de la aplicación o con Ctrl+C.',flush=True)
        try:
            code=process.wait()
            if code!=0:raise RuntimeError('El servidor finalizó con error; código '+str(code))
        except KeyboardInterrupt:
            try:
                opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
                with opener.open(URL+'api/bootstrap',timeout=2) as response:token=json.load(response)['token']
                req=urllib.request.Request(URL+'api/shutdown',b'{}',headers={'Content-Type':'application/json','X-E11-Token':token,'Origin':URL[:-1]})
                opener.open(req,timeout=3).close();process.wait(timeout=15)
            except Exception:process.terminate()
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (ImportError,OSError,RuntimeError) as exc:print('ERROR: '+str(exc)+'\nEjecuta Iniciar E11.bat para instalar/verificar el entorno.');raise SystemExit(1)
