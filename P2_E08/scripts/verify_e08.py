"""Batería E08 completa: regresión, IFC real, dos transientes y trazabilidad."""
import argparse
from datetime import datetime,timezone
import hashlib
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
    p.add_argument('--output',type=Path,default=ROOT/'results'/('e08_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')))
    args=p.parse_args();out=args.output.resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):p.error('Destino con contenido; usar uno nuevo')
    out.mkdir(parents=True,exist_ok=True)
    report=dict(status='running',started_utc=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),commands=[])
    def save():(out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    def run(name,arguments):
        print('E08: '+name,flush=True);start=time.perf_counter()
        env={**os.environ,'PYTHONNOUSERSITE':'1','PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8'};env.pop('PYTHONPATH',None)
        proc=subprocess.run([sys.executable,'-X','utf8','-B',*map(str,arguments)],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8')
        (out/(name+'.txt')).write_text(proc.stdout+proc.stderr,encoding='utf-8')
        report['commands'].append(dict(name=name,returncode=proc.returncode,arguments=list(map(str,arguments)),elapsed_s=time.perf_counter()-start));save()
        if proc.returncode:raise RuntimeError('Falló '+name+'; consultar su log')
    try:
        import mcoc_p2
        if Path(mcoc_p2.__file__).resolve().parent!=ROOT/'src/mcoc_p2':raise ValueError('El entorno importa otra entrega')
        report['imported_solver']=str(Path(mcoc_p2.__file__).resolve())
        baseline=json.loads((ROOT/'docs/E08_BASE_E07_INVENTARIO.json').read_text(encoding='utf-8'))['files']
        inherited=[n for n in baseline if n.endswith('.py') and n.split('/')[0] in ('src','tests','scripts','examples')]
        changed=[n for n in inherited if hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=baseline[n]['sha256']]
        if changed:raise ValueError('Cambios inesperados sobre la base E07: '+str(changed))
        report.update(inherited_python_checked=len(inherited),inherited_python_changed=changed)
        run('thermal_regression',['scripts/verify_e05.py','--output',out/'thermal_regression'])
        thermal=json.loads((out/'thermal_regression/verification.json').read_text(encoding='utf-8'))
        report.update(tests=thermal['tests'],parameter_cases_passed=thermal['parameter_cases_passed'])
        run('nominal',['examples/run_e08.py','--output',out/'nominal'])
        run('modified',['examples/run_e08.py','--spacing',.55,.55,.275,'--interval-hours',3,'--placement-offset',5,'--output',out/'modified'])
        nominal=json.loads((out/'nominal/summary.json').read_text(encoding='utf-8'))
        modified=json.loads((out/'modified/summary.json').read_text(encoding='utf-8'))
        if not all(nominal['checks'].values()) or not all(modified['checks'].values()):raise ValueError('Checks E08 no satisfechos')
        if nominal['nominal']['shape']==modified['nominal']['shape']:raise ValueError('La resolución no cambió la grilla')
        if nominal['temperature_range_C']==modified['temperature_range_C']:raise ValueError('Los cambios no modificaron la temperatura')
        if len({r['time_s'] for r in nominal['activation_events']})<2:raise ValueError('La demo debe incluir activaciones distintas')
        report.update(status='passed',stage_simulations_passed=2,frames_nominal=len(nominal['frames']),
            peak_nominal_C=nominal['temperature_range_C'][1],peak_modified_C=modified['temperature_range_C'][1],
            energy_nominal=nominal['energy'],formal_status='Cambios locales; commit E08 pendiente de publicación')
    except BaseException:
        report['status']='failed';raise
    finally:
        report['finished_utc']=datetime.now(timezone.utc).isoformat()
        report['input_sha256']={file.relative_to(ROOT).as_posix():hashlib.sha256(file.read_bytes()).hexdigest()
            for directory in ('src','tests','scripts','examples','configs','geometry','web')
            for file in (ROOT/directory).rglob('*') if file.is_file() and file.suffix in ('.py','.json','.ifc','.html','.js','.css')}
        save()
    print(json.dumps({k:report[k] for k in ('status','tests','parameter_cases_passed','stage_simulations_passed','frames_nominal','peak_nominal_C','peak_modified_C','formal_status')},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
