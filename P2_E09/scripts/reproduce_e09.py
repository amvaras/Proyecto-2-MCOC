"""Repite el cálculo desde IFC/inputs y compara todos los arrays sin conservar otra corrida."""
import argparse,hashlib,importlib.metadata,json,shutil,time,uuid
from pathlib import Path
import numpy as np
from mcoc_p2.e09.pipeline import run_baseline,write_json
from mcoc_p2.housekeeping import configure_runtime

ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--result',type=Path,default=ROOT/'results/e09_baseline')
    p.add_argument('--output',type=Path,default=ROOT/'results/verification/reproduction.json')
    a=p.parse_args();source=a.result.resolve();start=time.perf_counter()
    if not source.is_relative_to(ROOT) or not a.output.resolve().is_relative_to(ROOT):raise ValueError('Rutas dentro de E09')
    summary=json.loads((source/'summary.json').read_text(encoding='utf-8'))
    inputs=json.loads((source/'inputs.json').read_text(encoding='utf-8'))
    work=ROOT/'.runtime'/('reproduce-'+uuid.uuid4().hex[:8]);work.mkdir(parents=True)
    marker=work/'.owned';marker.write_text('reproduce_e09',encoding='utf-8')
    report=dict(status='running',comparisons=[])
    try:
        import mcoc_p2
        origin=Path(mcoc_p2.__file__).resolve()
        if origin.parent!=ROOT/'src/mcoc_p2':raise ValueError('Paquete importado de otra entrega')
        has_control=(source/'control.npz').is_file()
        result=run_baseline(ROOT/summary['ifc']['relative_path'],inputs,work/'run',plots=False,control=has_control)
        total=0
        artifacts=['grid.npz','temperature.npz','statistics.npz','steps.npz']
        if has_control:artifacts.append('control.npz')
        for name in artifacts:
            with np.load(source/name) as expected,np.load(work/'run'/name) as repeated:
                if set(expected.files)!=set(repeated.files):raise ValueError('Arrays distintos: '+name)
                for key in expected.files:
                    if not np.array_equal(expected[key],repeated[key]):raise ValueError('Cambió '+name+':'+key)
                report['comparisons'].append(dict(file=name,arrays=len(expected.files),bitwise_equal=True));total+=len(expected.files)
        report.update(status='PASS',arrays_equal=total,physical_steps=result['temporal']['integration_steps'],
            own_import='src/mcoc_p2/__init__.py',packages={n:importlib.metadata.version(n) for n in ('mcoc-p2','numpy','ifcopenshell','matplotlib','pytest')},
            source_sha256={path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted((ROOT/'src').rglob('*.py'))},
            note='Nueva ejecución desde el IFC y los inputs de E09. Se comparan todos los arrays guardados, incluido el control cuando está presente.',
            elapsed_s=time.perf_counter()-start)
    except BaseException:report['status']='FAIL';raise
    finally:
        a.output.parent.mkdir(parents=True,exist_ok=True);write_json(a.output,report)
        if work.parent==ROOT/'.runtime' and marker.is_file() and marker.read_text()=='reproduce_e09':
            shutil.rmtree(work)
            try:work.parent.rmdir()
            except OSError:pass
    print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},ensure_ascii=False,indent=2))


if __name__=='__main__':configure_runtime(ROOT);main()
