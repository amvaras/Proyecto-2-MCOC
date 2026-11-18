"""Una tarea Slurm = un chunk único. También admite emulación local explícita."""
import argparse,os,sys,socket,hashlib
from pathlib import Path
import numpy as np
from mcoc_p2.e11.pipeline import ROOT
from mcoc_p2.e14.io import write
from mcoc_p2.e14.workflow import load_manifest,execute_chunk
from mcoc_p2.housekeeping import configure_runtime
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--index',type=int);p.add_argument('--local-emulation',action='store_true');a=p.parse_args()
    m=load_manifest(a.manifest);i=a.index
    if i is None:
        text=os.environ.get('SLURM_ARRAY_TASK_ID','')
        if not text.isdecimal():raise ValueError('SLURM_ARRAY_TASK_ID requerido')
        i=int(text)
    if not 0<=i<len(m['chunks']):raise ValueError('Índice Slurm no corresponde al manifest')
    if np.__version__!=m['versions']['numpy'] or sys.version.split()[0].split('.')[:2]!=m['versions']['python'].split('.')[:2]:raise ValueError('Instalar Python/NumPy declarados antes de ejecutar')
    r=execute_chunk(a.manifest,i,retry_failed=True)
    proof=dict(manifest_fingerprint=m['fingerprint'],index=i,mode='local_slurm_emulation' if a.local_emulation else 'slurm_environment',
       scheduler_job_id=os.environ.get('SLURM_JOB_ID'),array_job_id=os.environ.get('SLURM_ARRAY_JOB_ID'),array_task_id=os.environ.get('SLURM_ARRAY_TASK_ID'),
       python=sys.version,numpy=np.__version__,host=socket.gethostname(),pid=os.getpid(),status=r['status'],
       scripts_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'scripts/hpc').glob('*') if p.is_file()},
       real_cluster_verified=False,meaning='El entorno Slurm por sí solo no verifica ejecución real; adjuntar sbatch/sacct y outputs validados')
    write(a.manifest.parent/'hpc_runtime'/f'task-{i:04d}.json',proof,replace=True)
    print(r['status'],i)
    if r['status']!='passed':raise SystemExit(1)
if __name__=='__main__':configure_runtime(ROOT);main()
