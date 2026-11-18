"""Prueba real de solver secuencial/paralelo con mismas muestras, sin cache hits."""
from pathlib import Path
import argparse,uuid,hashlib,subprocess,sys
from mcoc_p2.e11.pipeline import ROOT
from mcoc_p2.e14.io import read,write
from mcoc_p2.e14.model import baseline_plans
from mcoc_p2.e14.workflow import prepare,run_local
from mcoc_p2.housekeeping import configure_runtime
def main():
    name='parallel-'+uuid.uuid4().hex[:10];base=ROOT/'.runtime'/name;base.mkdir(parents=True)
    c=dict(plans=baseline_plans()[:1],spacing_m=[.9,.9,.275],step_s=900,N=4,master_seed=20261119)
    a=base/'sequential';b=base/'parallel';ma=prepare(c,a,chunk_size=1,cache=base/'cache_seq');mb=prepare(c,b,chunk_size=1,cache=base/'cache_parallel')
    assert ma['bank']==mb['bank']
    ra=run_local(a/'manifest.json',1,force=True);rb=run_local(b/'manifest.json',2,force=True)
    def cases(folder):
        return {e['physics_key']:e['row'] for p in (folder/'chunks').glob('*.json') for e in read(p)['entries']}
    x=cases(a);y=cases(b);assert x.keys()==y.keys();fields=[]
    for key in x:
        for item in ('Tmax_C','delta_C','g_T','g_Delta','peak','delta_peak','energy','saved_fields_sha256'):assert x[key][item]==y[key][item],item
        fields.append(dict(physics_key=key,saved_fields_sha256=x[key]['saved_fields_sha256']))
    assert ra['plans']==rb['plans'] and ra['cache_hits']==rb['cache_hits']==0
    # El wrapper Bash ejecuta la misma entrada CLI y valida el índice de array.
    command=[sys.executable,'-X','utf8','-B','scripts/validate_e14_hpc.py','--emulate-manifest',str(a/'manifest.json')]
    check=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    if check.returncode:raise ValueError(check.stdout+check.stderr)
    runtime=read(a/'hpc_runtime/task-0000.json');write(ROOT/'results/verification/hpc_runtime_local.json',runtime,replace=True)
    write(ROOT/'results/verification/parallel.json',dict(status='PASS',samples=4,unique_physics=len(x),actual_solver_runs=2*len(x),cached=0,
        sequential_s=ra['execution']['elapsed_s'],parallel_s=rb['execution']['elapsed_s'],exact_metrics=True,exact_saved_field_hashes=fields,seed_bank_equal=True,
        local_slurm_emulation='PASS',real_cluster=False,temporary_root=base.relative_to(ROOT).as_posix()),replace=True)
    print('PASS: solver secuencial/paralelo, semillas, campos y wrapper Slurm local')
if __name__=='__main__':configure_runtime(ROOT);main()
