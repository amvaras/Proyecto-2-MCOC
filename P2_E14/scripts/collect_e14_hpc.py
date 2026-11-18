"""Consultar sacct real y exigir todos los índices/outputs antes de acreditar el array."""
from pathlib import Path
import argparse,subprocess
from mcoc_p2.e14.io import ROOT,read,write
from mcoc_p2.e14.workflow import load_manifest,aggregate
from mcoc_p2.e14.hpc import validate_accounting

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--job',required=True);p.add_argument('--manifest',type=Path,required=True);a=p.parse_args()
    m=load_manifest(a.manifest)
    if not a.job.isdecimal():raise ValueError('JobID numérico')
    r=subprocess.run(['sacct','--array','-X','-j',a.job,'--format=JobID%50,State%30,ExitCode,Elapsed,NodeList%200','-P','-n'],capture_output=True,text=True,check=True,timeout=30)
    accounting=validate_accounting(r.stdout,a.job,len(m['chunks']))
    for i in range(len(m['chunks'])):
        proof=read(a.manifest.parent/'hpc_runtime'/f'task-{i:04d}.json')
        if proof['mode']!='slurm_environment' or proof['status']!='passed' or proof['array_job_id']!=a.job or proof['array_task_id']!=str(i) or proof['manifest_fingerprint']!=m['fingerprint']:raise ValueError('Falta prueba runtime del job real; no acreditar emulación/caso ajeno')
    results=aggregate(a.manifest);assert results['status']=='PASS'
    report=dict(status='PASS',job=a.job,manifest=m['fingerprint'],accounting=accounting,sacct_stdout=r.stdout,validated_outputs=True,
                real_cluster_verified=True,scope='Array y outputs; inputs térmicos ya presentes pueden proceder de cache. No prueba rendimiento de nuevos solves.',source='https://slurm.schedmd.com/sacct.html')
    write(ROOT/'results/e14/hpc'/('job-'+a.job+'.json'),report)
    print('PASS: accounting expandido y todos los outputs del array',a.job)
if __name__=='__main__':main()
