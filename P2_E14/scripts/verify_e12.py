"""Verificación oficial E12 y reproducción determinista opcional sin red."""
import argparse,json,time,uuid,hashlib
from pathlib import Path
from mcoc_p2.e11.pipeline import ROOT,write_json
from mcoc_p2.e12.verification import verify
from mcoc_p2.e12.pipeline import run,arrays
from mcoc_p2.housekeeping import configure_runtime
import numpy as np
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reproduce',action='store_true');a=p.parse_args();start=time.perf_counter()
    result=ROOT/'results/e13/representative';report=verify(result,ROOT/'vtk/e13')
    if a.reproduce:
        target=ROOT/'.runtime'/('reproduce-'+uuid.uuid4().hex)
        cfg=json.loads((result/'inputs.json').read_text(encoding='utf8'));run(cfg,target,plots=False,export=False)
        equal=[]
        for name in ['grid.npz','fields.npz','all_steps.npz','statistics.npz','weather_steps.npz','constant_steps.npz']:
            original=arrays(result/name);copy=arrays(target/name);assert original.keys()==copy.keys()
            for k in original:np.testing.assert_array_equal(original[k],copy[k]);equal.append(name+':'+k)
        inventory=[dict(path=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in target.iterdir()]
        report['offline_reproduction']=dict(status='PASS',exact_arrays=equal,network='urlopen prohibido dentro de pipeline E12; snapshot local',duplicate_cleanup_inventory=inventory)
        assert json.loads((target/'geometry.json').read_text(encoding='utf8'))==json.loads((result/'geometry.json').read_text(encoding='utf8'))
        allowed={'grid.npz','fields.npz','all_steps.npz','statistics.npz','weather_steps.npz','constant_steps.npz','summary.json','inputs.json','geometry.json'}
        assert target.parent==ROOT/'.runtime' and not target.is_symlink() and not target.is_junction()
        assert set(p.name for p in target.iterdir())==allowed
        for row in inventory:
            p=target/row['path'];assert p.is_file() and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
        for row in inventory:(target/row['path']).unlink()
        try:target.rmdir()
        except PermissionError:
            import os,stat
            os.chmod(target,stat.S_IWRITE);target.rmdir()
    report['elapsed_s']=time.perf_counter()-start;write_json(ROOT/'results/verification/e12.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':configure_runtime(ROOT);main()

