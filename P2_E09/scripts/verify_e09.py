"""Regresión completa y auditoría del baseline/dossier E09 ya calculado."""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
import xml.etree.ElementTree as ET
from mcoc_p2.e09.verification import validate_saved_result
from mcoc_p2.housekeeping import configure_runtime
from check_e09_dossier import inspect_dossier
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--result',type=Path,default=ROOT/'results/e09_baseline')
    p.add_argument('--output',type=Path,default=ROOT/'results/verification')
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT):p.error('Evidencia dentro de E09')
    out.mkdir(parents=True,exist_ok=True);report=dict(status='running',commands=[])
    def run(name,args):
        t=time.perf_counter()
        proc=subprocess.run([sys.executable,'-X','utf8','-B',*map(str,args)],cwd=ROOT,
            env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','MPLCONFIGDIR':str(ROOT/'.mplconfig')},
            capture_output=True,text=True,encoding='utf-8')
        # El IFC ya se conserva como JSON; no duplicar el mismo stdout.
        if name!='ifc' or proc.returncode:(out/(name+'.txt')).write_text(proc.stdout+proc.stderr,encoding='utf-8')
        report['commands'].append(dict(name=name,returncode=proc.returncode,elapsed_s=time.perf_counter()-t))
        if proc.returncode:raise RuntimeError('Falló '+name)
    try:
        import mcoc_p2
        if Path(mcoc_p2.__file__).resolve().parent!=ROOT/'src/mcoc_p2':raise ValueError('Paquete de otra entrega')
        run('pip_check',['-m','pip','check'])
        run('pytest',['-m','pytest','tests','-q','-p','no:cacheprovider',f'--junitxml={out/"pytest.xml"}'])
        junit_path=out/'pytest.xml'
        junit=ET.parse(junit_path)
        suites=list(junit.getroot().iter('testsuite'))
        for suite in suites:
            suite.attrib.pop('hostname',None)
        junit.write(junit_path,encoding='utf-8',xml_declaration=True)
        report['tests']={k:sum(int(s.get(k,0)) for s in suites) for k in ('tests','failures','errors','skipped')}
        if any(report['tests'][k] for k in ('failures','errors','skipped')):raise ValueError('Regresión incompleta')
        run('ifc',['scripts/check_ifc.py','geometry/foundation.ifc','--json',out/'ifc.json'])
        report['data']=validate_saved_result(a.result,ROOT)
        report['dossier']=inspect_dossier(ROOT/'docs/E09_DOSSIER.md')
        (out/'dossier.json').write_text(json.dumps(report['dossier'],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        base=json.loads((ROOT/'docs/E09_BASE_SELECCIONADA.json').read_text(encoding='utf-8'))
        archive=ROOT.parent/'P2_E08.zip'
        if archive.exists():
            report['e08_original_intact']=hashlib.sha256(archive.read_bytes()).hexdigest()==base['source_sha256']
            if not report['e08_original_intact']:raise ValueError('Cambió E08 original')
        else:report['e08_original_intact']='No se requiere E08 para ejecutar; original no presente'
        report['autonomous_import']=True
        report['status']='PASS'
    except BaseException:report['status']='FAIL';raise
    finally:(out/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':configure_runtime(ROOT);main()
