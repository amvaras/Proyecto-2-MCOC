"""Verificación E07 completa y reproducible, sin escribir sobre resultados previos."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=Path('results')/('e07_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')))
    a=p.parse_args();out=a.output.resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):p.error('Destino existente con contenido')
    out.mkdir(parents=True,exist_ok=True)
    report=dict(status='running',started_utc=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),platform=platform.platform(),commands=[])
    def save():(out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    def run(name,args,expected=0):
        print('E07: '+name,flush=True);start=time.perf_counter()
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8','PYTHONNOUSERSITE':'1'};env.pop('PYTHONPATH',None)
        proc=subprocess.run([sys.executable,'-X','utf8','-B',*map(str,args)],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8')
        (out/(name+'.txt')).write_text(proc.stdout+proc.stderr,encoding='utf-8')
        report['commands'].append(dict(name=name,arguments=list(map(str,args)),returncode=proc.returncode,expected_returncode=expected,elapsed_s=time.perf_counter()-start));save()
        if proc.returncode!=expected:raise RuntimeError('Falló '+name)
        return proc
    try:
        import mcoc_p2
        import mcoc_p2.e07.voxel
        imported=Path(mcoc_p2.__file__).resolve()
        if imported.parent!=ROOT/'src/mcoc_p2':raise ValueError('Import ajeno a E07')
        report['imported_solver']=str(imported);report['packages']={n:importlib.metadata.version(n) for n in ('mcoc-p2','numpy','pytest','matplotlib','ifcopenshell')}
        base=json.loads((ROOT/'docs/E07_BASE_E06_INVENTARIO.json').read_text(encoding='utf-8'))['files']
        inherited=[k for k in base if k.endswith('.py') and k.split('/')[0] in ('src','scripts','examples','tests')]
        changed=[k for k in inherited if hashlib.sha256((ROOT/k).read_bytes()).hexdigest()!=base[k]['sha256']]
        report.update(inherited_python_checked=len(inherited),inherited_python_changed=changed)
        if changed:raise ValueError('Se modificó código heredado: '+str(changed))
        run('thermal_regression',['scripts/verify_e05.py','--output',out/'thermal_regression'])
        thermal=json.loads((out/'thermal_regression/verification.json').read_text(encoding='utf-8'))
        report['tests']=thermal['tests'];report['parameter_cases_passed']=thermal['parameter_cases_passed']
        run('demo',['examples/run_e07.py','--output',out/'demo'])
        run('modified',['examples/run_e07.py','--spacing',.4,.3,.275,'--margin',.1,'--interval-hours',3,'--heat-mj-m3',40,
             '--duration-hours',36,'--h',15,'--ambient',12,'--output',out/'modified'])
        nominal=json.loads((out/'demo/summary.json').read_text(encoding='utf-8'))
        modified=json.loads((out/'modified/summary.json').read_text(encoding='utf-8'))
        if not all(nominal['checks'].values()) or not all(modified['checks'].values()):raise ValueError('Checks de demostración fallidos')
        if nominal['nominal']['shape']==modified['nominal']['shape']:raise ValueError('Los parámetros no cambiaron la grilla')
        reject=run('invalid_resolution',['examples/run_e07.py','--spacing',0,'--output',out/'invalid'],expected=2)
        if 'Resolución' not in reject.stdout:raise ValueError('Motivo de rechazo incorrecto')
        report.update(status='passed',voxel_cases=2,volume_resolutions_m=[r['spacing_m'][0] for r in nominal['volume_study']],
                      e06_formal_status='COMMIT E06 PENDIENTE DE PUBLICACIÓN',e07_publication_status='No publicado; sin commit E07 verificado',
                      integration=nominal['integration'])
    except BaseException:
        report['status']='failed';raise
    finally:
        report['finished_utc']=datetime.now(timezone.utc).isoformat()
        report['input_sha256']={x.relative_to(ROOT).as_posix():hashlib.sha256(x.read_bytes()).hexdigest() for folder in ('src','tests','scripts','examples','configs','geometry') for x in (ROOT/folder).rglob('*') if x.is_file() and x.suffix in ('.py','.json','.ifc')}
        save()
    print(json.dumps({k:report[k] for k in ('status','tests','parameter_cases_passed','voxel_cases','volume_resolutions_m','integration')},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
