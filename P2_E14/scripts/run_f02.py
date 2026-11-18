"""Reproduce all 24 F02 scenarios or the independent numerical controls."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import hashlib
import math
import os
from pathlib import Path
import subprocess
import numpy as np

from mcoc_p2.e13.evaluator import Evaluator
from mcoc_p2.e14.io import ROOT, fingerprint, read, source_hashes, write
from mcoc_p2.e14.model import catalog
from mcoc_p2.f02.study import configuration, run_case

def init():
    global evaluator
    evaluator = Evaluator()

def solve(task):
    return run_case(task[0],spacing=task[1],step=task[2],visual=task[3],evaluator=evaluator)

def code_version():
    names = [*source_hashes(), 'scripts/run_f02.py', 'configs/f02/moderate_20.json',
             'src/mcoc_p2/f02/pipes.py','src/mcoc_p2/f02/study.py']
    return fingerprint({n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})

def summarize(rows):
    return dict(plan=rows[0]['plan'], N=len(rows), D_h=rows[0]['D_h'],
                Tmax_C=max(r['Tmax_C'] for r in rows), delta_C=max(r['delta_C'] for r in rows),
                **{name:math.fsum(r['weight'] for r in rows if r[flag]) for name,flag in
                   [('P_T','fail_T'),('P_delta','fail_delta'),('P_joint','fail_joint')]})

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workers',type=int,default=2)
    parser.add_argument('--output',type=Path,default=ROOT/'results/f02')
    parser.add_argument('--controls',action='store_true')
    args=parser.parse_args()
    os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
    out=args.output.resolve()
    if not out.is_relative_to(ROOT) or not 1<=args.workers<=4:
        parser.error('Salida dentro de P2_E14, entre 1 y 4 procesos')
    kernel=code_version()
    cfg=configuration()
    suite=cfg['controls']
    tag='controls' if args.controls else 'enumeration'
    tasks=([(id,suite['grid'],None,False) for id in suite['scenarios']] +
           [(id,None,suite['step_s'],False) for id in suite['scenarios']]) if args.controls else [
               (s['id'],None,None,s['id']==cfg['scenario_3d']) for s in catalog()]
    out.mkdir(parents=True,exist_ok=True)
    if (out/f'{tag}.json').exists() or (not args.controls and (out/'fields.npz').exists()):
        parser.error('Elige un destino nuevo para conservar resultados existentes')
    rows=[]
    with ProcessPoolExecutor(args.workers,initializer=init) as pool:
        for row,frames in pool.map(solve,tasks):
            rows.append(row)
            print(tag,row['scenario'],row['Tmax_C'],row['delta_C'],flush=True)
            if frames is not None:
                with (out/'fields.npz').open('xb') as stream:
                    np.savez_compressed(stream,**frames)
    if kernel!=code_version():
        raise RuntimeError('El kernel cambió durante la ejecución. Usa una salida nueva para repetir.')
    payload=dict(generated_at_utc=datetime.now(timezone.utc).isoformat(),kernel_sha256=kernel,
                 e14_base=subprocess.check_output(['git','rev-parse','entrega-e14^{commit}'],cwd=ROOT,text=True).strip(),
                 configuration=cfg, rows=rows)
    if not args.controls:
        payload.update(summary=summarize(rows), fields_sha256=hashlib.sha256((out/'fields.npz').read_bytes()).hexdigest())
    write(out/f'{tag}.json',payload)

if __name__=='__main__':
    main()
