"""Abre la demo en Chrome y reutiliza el servidor local si ya está activo."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT=Path(__file__).resolve().parents[1]
URL='http://127.0.0.1:8768/'


def running():
    try:
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(URL+'api/bootstrap',timeout=1) as response:
            return 'save_interval_s' in json.load(response).get('configuration',{})
    except (OSError,ValueError):return False


def main():
    if '--check' in sys.argv:
        active=running();print('Servidor E08 activo' if active else 'Servidor E08 no accesible');return 0 if active else 1
    if not running():
        process=subprocess.Popen([sys.executable,'-X','utf8','-B',str(ROOT/'web/servidor.py')],cwd=ROOT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        for _ in range(40):
            if running():break
            if process.poll() is not None:raise RuntimeError('No se pudo iniciar el servidor. Revisa si el puerto 8768 está ocupado.')
            time.sleep(.25)
        else:raise RuntimeError('El servidor no respondió. Ejecuta web/servidor.py para ver el registro.')
    chrome=next((Path(base)/'Google/Chrome/Application/chrome.exe' for base in
        [os.environ.get('PROGRAMFILES',''),os.environ.get('PROGRAMFILES(X86)',''),os.environ.get('LOCALAPPDATA','')]
        if (Path(base)/'Google/Chrome/Application/chrome.exe').is_file()),None)
    if chrome:subprocess.Popen([str(chrome),URL])
    else:webbrowser.open(URL)
    print('E08 lista: '+URL);return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,RuntimeError) as exc:print('ERROR: '+str(exc));raise SystemExit(1)
