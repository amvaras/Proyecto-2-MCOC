"""Repite E06 en un destino nuevo; conserva el solver y el dossier de referencia."""
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

from audit_integrity import inspect_inventory
from check_e06_dossier import inspect_dossier

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=Path('results')/('e06_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')))
    p.add_argument('--freeze',action='store_true',help='Crear dossier y figuras de referencia, solo si no existen')
    a=p.parse_args();out=a.output.resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):p.error('Destino con contenido; no se sobrescribe evidencia')
    if a.freeze and (ROOT/'docs/E06_DOSSIER.md').exists():p.error('El dossier de referencia ya existe')
    out.mkdir(parents=True,exist_ok=True)
    report=dict(status='running',started_utc=datetime.now(timezone.utc).isoformat(),
                python=platform.python_version(),platform=platform.platform(),commands=[])
    def save():(out/'e06.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    def run(name,args):
        print('E06: '+name,flush=True);start=time.perf_counter()
        cmd=[sys.executable,'-X','utf8','-B',*map(str,args)]
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8','PYTHONNOUSERSITE':'1'}
        env.pop('PYTHONPATH',None)
        result=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8')
        (out/(name+'.txt')).write_text(result.stdout+result.stderr,encoding='utf-8')
        report['commands'].append(dict(name=name,arguments=list(map(str,args)),returncode=result.returncode,elapsed_s=time.perf_counter()-start));save()
        if result.returncode:raise RuntimeError('Falló '+name+'; consultar su log')
    try:
        import mcoc_p2
        if Path(mcoc_p2.__file__).resolve().parent!=ROOT/'src/mcoc_p2':raise ValueError('Import ajeno a E06')
        report['imported_solver']=str(Path(mcoc_p2.__file__).resolve())
        report['packages']={n:importlib.metadata.version(n) for n in ('numpy','pytest','matplotlib','ifcopenshell','mcoc-p2')}
        base=json.loads((ROOT/'docs/E06_BASE_E05_INVENTARIO.json').read_text(encoding='utf-8'))
        inherited=[k for k in base['files'] if k.endswith('.py') and k.split('/')[0] in ('src','tests','scripts','examples')]
        report['inherited_integrity']=inspect_inventory(ROOT,base['files'],inherited)
        report.update(inherited_python_files_checked=len(inherited),
                      inherited_python_changed=[r['path'] for r in report['inherited_integrity']['documented_revisions']])
        # Si existe inventario final, cotejar todos sus contenidos antes de ejecutar.
        inventory=ROOT/'E06_INVENTARIO_SHA256.json'
        if inventory.exists():
            frozen=json.loads(inventory.read_text(encoding='utf-8'))['files']
            report['frozen_integrity']=inspect_inventory(ROOT,frozen)
            report['frozen_files_checked']=len(frozen)
        save()
        run('thermal',['scripts/verify_e05.py','--output',out/'thermal'])
        thermal=json.loads((out/'thermal/verification.json').read_text(encoding='utf-8'))
        report.update(tests=thermal['tests'],parameter_cases_passed=thermal['parameter_cases_passed'])
        run('robin25',['examples/run_e05.py','--case','robin','--dim',3,'--n',12,'--h',25,'--initial',50,'--ambient',20,'--t-end',10000,'--output',out/'robin25'])
        run('reconstruir_ifc',['scripts/create_preliminary_ifc.py','--output',out/'foundation_rebuilt.ifc'])
        run('verificar_ifc_reconstruido',['scripts/check_ifc.py',out/'foundation_rebuilt.ifc','--json',out/'ifc_rebuilt.json'])
        original=json.loads((out/'thermal/ifc_check.json').read_text(encoding='utf-8'))
        rebuilt=json.loads((out/'ifc_rebuilt.json').read_text(encoding='utf-8'))
        if original!=rebuilt:raise ValueError('El IFC reconstruido no coincide geométricamente')
        report['ifc_rebuilt_equivalent']=True;save()
        document=ROOT/'docs/E06_DOSSIER.md' if a.freeze else out/'artifacts/E06_DOSSIER.md'
        figures=ROOT/'figures' if a.freeze else out/'artifacts/figures'
        run('dossier_figuras',['scripts/build_e06.py','--evidence',out,'--document',document,'--figures',figures])
        count=json.loads((out/'dossier_check.json').read_text(encoding='utf-8'))
        report.update(prose_words=count['prose_words'],all_visible_words=count['all_visible_words'],
                      document=os.path.relpath(document,ROOT).replace(os.sep,'/'),
                      status='passed',technical_status='COMPLETA',formal_status=count['formal_status'])
    except BaseException:
        report['status']='failed';raise
    finally:
        report['finished_utc']=datetime.now(timezone.utc).isoformat()
        report['input_sha256']={x.relative_to(ROOT).as_posix():hashlib.sha256(x.read_bytes()).hexdigest()
                               for folder in ('src','tests','scripts','examples','configs','geometry')
                               for x in (ROOT/folder).rglob('*') if x.is_file() and x.suffix in ('.py','.json','.ifc')}
        save()
    # build_e06 inspeccionó el enlace al manifiesto mientras aún estaba en
    # ejecución. Congelar las huellas solo después de escribir su estado final.
    try:
        final_count=inspect_dossier(document)
        (out/'dossier_check.json').write_text(json.dumps(final_count,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    except BaseException:
        report['status']='failed';save();raise
    print(json.dumps({k:report[k] for k in ('status','tests','parameter_cases_passed','prose_words','formal_status')},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
