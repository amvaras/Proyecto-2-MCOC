"""Instala una copia física externa sin red y reproduce E07 sin entregas previas."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=Path('evidencias/e07_independencia'))
    a=p.parse_args();out=a.output.resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):p.error('Destino con contenido')
    out.mkdir(parents=True,exist_ok=True)
    temporary=Path(tempfile.mkdtemp(prefix='mcoc_e07_independiente_'));replica=temporary/'P2_E07_autonomo'
    report=dict(status='running',started_utc=datetime.now(timezone.utc).isoformat(),temporary_root=str(temporary),commands=[])
    def save():(out/'independence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8','PYTHONNOUSERSITE':'1',
         'PIP_NO_INDEX':'1','PIP_DISABLE_PIP_VERSION_CHECK':'1','PIP_CONFIG_FILE':os.devnull}
    env.pop('PYTHONPATH',None)
    def run(name,cmd):
        print('E07 independiente: '+name,flush=True)
        r=subprocess.run(list(map(str,cmd)),cwd=replica,env=env,capture_output=True,text=True,encoding='utf-8')
        (out/(name+'.txt')).write_text(r.stdout+r.stderr,encoding='utf-8')
        report['commands'].append(dict(name=name,arguments=list(map(str,cmd)),returncode=r.returncode));save()
        if r.returncode:raise RuntimeError('Falló '+name)
    try:
        selected=[]
        for base,dirs,names in os.walk(ROOT):
            dirs[:]=[d for d in dirs if d not in ('.git','__pycache__','.pytest_cache') and not d.startswith('.venv') and not d.endswith('.egg-info') and (Path(base)/d).resolve()!=out]
            for d in dirs:
                if (Path(base)/d).is_symlink() or (Path(base)/d).is_junction():raise ValueError('Enlace de directorio')
            for name in names:
                f=Path(base)/name
                if f.suffix in ('.pyc','.pyo','.tmp'):continue
                if f.is_symlink() or f.is_junction():raise ValueError('Enlace de archivo')
                selected.append(f)
        for f in selected:
            dest=replica/f.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest)
            if os.path.samefile(f,dest) or hashlib.sha256(f.read_bytes()).digest()!=hashlib.sha256(dest.read_bytes()).digest():raise ValueError('Copia no independiente')
        report['copied_files']=len(selected);save()
        run('crear_entorno',[sys.executable,'-B','-m','venv',temporary/'venv'])
        python=temporary/'venv/Scripts/python.exe' if os.name=='nt' else temporary/'venv/bin/python'
        run('dependencias',[python,'-m','pip','install','--no-index','--find-links','vendor/wheels','-r','requirements-lock.txt'])
        run('paquete',[python,'-m','pip','install','--no-index','--no-build-isolation','--no-deps','-e','.[dev,plot,bim]'])
        # Misma profundidad relativa que la evidencia devuelta: enlaces Markdown portables.
        relative_result=out.relative_to(ROOT)/'resultados'
        run('verificacion',[python,'-X','utf8','-B','scripts/verify_e07.py','--output',relative_result])
        data=replica/relative_result;verification=json.loads((data/'verification.json').read_text(encoding='utf-8'))
        imported=Path(verification['imported_solver']).resolve()
        if not imported.is_relative_to(replica) or verification['status']!='passed':raise ValueError('Verificación externa incorrecta')
        shutil.copytree(data,out/'resultados',copy_function=shutil.copyfile)
        report.update(status='passed',tests=verification['tests'],parameter_cases_passed=verification['parameter_cases_passed'],
                      imported_solver=str(imported),offline_installation=True,
                      previous_delivery_runtime_dependencies=False,input_sha256=verification['input_sha256'])
    except BaseException:
        report['status']='failed';raise
    finally:
        report['finished_utc']=datetime.now(timezone.utc).isoformat();save()
    print(json.dumps({k:report[k] for k in ('status','tests','parameter_cases_passed')},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
