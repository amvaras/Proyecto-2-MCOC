"""Sintaxis Bash y contrato Slurm; sin inventar disponibilidad ni ejecución remota."""
from pathlib import Path
import argparse,shutil,subprocess,json
from mcoc_p2.e11.pipeline import ROOT
from mcoc_p2.e14.io import write
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--emulate-manifest',type=Path);a=p.parse_args()
    bash=Path('C:/Program Files/Git/bin/bash.exe') if __import__('os').name=='nt' else Path(shutil.which('bash') or '/nonexistent')
    if not bash.is_file():raise RuntimeError('Bash no disponible para validar sintaxis')
    checks=[]
    for name in ('array.sbatch','submit.sh','collect.sh'):
        file=ROOT/'scripts/hpc'/name;raw=file.read_bytes()
        if b'\r' in raw:raise ValueError('Slurm requiere archivos LF, sin CRLF')
        r=subprocess.run([str(bash),'--noprofile','--norc','-n',file.as_posix()],cwd=ROOT,capture_output=True,text=True)
        if r.returncode:raise ValueError(r.stderr)
        checks.append(dict(file=file.relative_to(ROOT).as_posix(),bash_n='PASS'))
    text=(ROOT/'scripts/hpc/array.sbatch').read_text()
    assert '%A_%a' in text and 'SLURM_ARRAY_TASK_ID' in text and '--ntasks=1' in text and 'mpirun' not in text
    report=dict(status='PASS',syntax=checks,local_sbatch=shutil.which('sbatch'),local_squeue=shutil.which('squeue'),
        real_cluster_execution='NO VERIFICADO: no acceso/host/job real identificado',source='https://slurm.schedmd.com/job_array.html')
    if a.emulate_manifest:
        import os
        env={**os.environ,'E14_MANIFEST':a.emulate_manifest.as_posix(),'SLURM_ARRAY_TASK_ID':'0','E14_LOCAL_EMULATION':'1','E14_PYTHON':(ROOT/'.venv/Scripts/python.exe').as_posix() if os.name=='nt' else str(Path(__import__('sys').executable))}
        run=subprocess.run([str(bash),'--noprofile','--norc',(ROOT/'scripts/hpc/array.sbatch').as_posix()],cwd=ROOT,env=env,capture_output=True,text=True,timeout=180)
        report['emulation']=dict(exit_code=run.returncode,output=run.stdout[-1000:],error=run.stderr[-1000:])
        if run.returncode:raise RuntimeError('Emulación local falló: '+run.stderr)
    write(ROOT/'results/verification/hpc.json',report,replace=True);print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
