"""Contrato Slurm ejecutado localmente: no acredita un clúster real."""
from pathlib import Path
import os,subprocess,sys
import pytest
from mcoc_p2.e14.workflow import prepare
from mcoc_p2.e14.model import baseline_plans
from mcoc_p2.e14.io import ROOT,read

def test_slurm_bash_syntax_and_actual_wrapper_emulation(tmp_path):
    bash=Path('C:/Program Files/Git/bin/bash.exe') if os.name=='nt' else Path('/bin/bash')
    assert bash.is_file(),'Instalar Bash para ejecutar la verificación Slurm, no para usar la aplicación'
    for name in ('array.sbatch','submit.sh','collect.sh'):
        path=ROOT/'scripts/hpc'/name;assert b'\r' not in path.read_bytes()
        r=subprocess.run([str(bash),'-n',path.as_posix()],capture_output=True,text=True);assert r.returncode==0,r.stderr
    cfg=dict(plans=baseline_plans()[:1],spacing_m=[.45,.45,.11],step_s=900,N=1,master_seed=777)
    out=tmp_path/'slurm';m=prepare(cfg,out,chunk_size=1);assert m['estimate']['new']==0
    env={**os.environ,'E14_MANIFEST':(out/'manifest.json').as_posix(),'SLURM_ARRAY_TASK_ID':'0','E14_LOCAL_EMULATION':'1','E14_PYTHON':Path(sys.executable).as_posix()}
    r=subprocess.run([str(bash),'--noprofile','--norc',(ROOT/'scripts/hpc/array.sbatch').as_posix()],cwd=ROOT,env=env,capture_output=True,text=True,timeout=60)
    assert r.returncode==0,r.stderr+r.stdout
    proof=read(out/'hpc_runtime/task-0000.json');assert proof['status']=='passed' and proof['mode']=='local_slurm_emulation' and proof['real_cluster_verified'] is False
    # Emular el script copiado al spool, conservando el directorio de envío.
    spool=tmp_path/'spool';spool.mkdir();script=spool/'slurm_script';script.write_bytes((ROOT/'scripts/hpc/array.sbatch').read_bytes())
    env['SLURM_SUBMIT_DIR']=ROOT.as_posix()
    r=subprocess.run([str(bash),'--noprofile','--norc',script.as_posix()],cwd=spool,env=env,capture_output=True,text=True,timeout=60)
    assert r.returncode==0,r.stderr+r.stdout

def test_accounting_rejects_empty_failed_pending_or_missing_array_tasks():
    from mcoc_p2.e14.hpc import validate_accounting
    text='123_0|COMPLETED|0:0|00:01:00|node01\n123_1|COMPLETED|0:0|00:01:01|node02\n'
    assert len(validate_accounting(text,'123',2))==2
    for bad in ('',text.splitlines()[0],text.replace('COMPLETED','RUNNING'),text.replace('0:0','1:0'),text.replace('123_1','123_0'),text.replace('123_0','124_0')):
        with pytest.raises(ValueError):validate_accounting(bad,'123',2)
