"""Migración auditada de metadata: corregir agregación, sin repetir ni alterar física."""
from pathlib import Path
from mcoc_p2.e11.pipeline import ROOT
from mcoc_p2.e14.io import read,write,fingerprint
from mcoc_p2.e14.workflow import runtime_signature,validate_chunk
from mcoc_p2.e14.model import Model
def main():
    path=ROOT/'results/e14/enumeration/manifest.json';m=read(path);oldfp=m['fingerprint'];assert oldfp==fingerprint({k:v for k,v in m.items() if k not in ('fingerprint','created_at_utc')})
    current=runtime_signature();assert m['versions']['kernel']==current['kernel']
    changed=[n for n in current['workflow'] if current['workflow'][n]!=m['versions']['workflow'][n]]
    assert changed==['src/mcoc_p2/e14/workflow.py'],changed
    model=Model();chunks=[];hashes=[]
    for i,indices in enumerate(m['chunks']):
        p=path.parent/'chunks'/f'chunk-{i:04d}.json';chunk=validate_chunk(read(p),m,i);assert chunk['status']=='passed'
        for e,j in zip(chunk['entries'],indices):
            t=m['tasks'][j];cfg,_=model.configuration(t['item'],t['scenario'],t['spacing_m'],t['step_s'])
            assert model.key(cfg)==t['physics_key']==e['physics_key'];hashes.append(fingerprint(e['row']))
        chunks.append((p,chunk))
    progress=read(path.parent/'progress.json');old_workflow=m['versions']['workflow'];m['versions']=current
    m['aggregation_migration']=dict(from_fingerprint=oldfp,reason='Correcciones de agregación/reanudación y evitar construir N veces los mismos inputs; sin cambiar muestras, kernel, inputs físicos o filas')
    m['fingerprint']=fingerprint({k:v for k,v in m.items() if k not in ('fingerprint','created_at_utc')})
    after=[]
    for p,chunk in chunks:
        chunk['manifest_fingerprint']=m['fingerprint'];chunk['content_sha256']=fingerprint({k:v for k,v in chunk.items() if k!='content_sha256'})
        after.extend(fingerprint(e['row']) for e in chunk['entries']);write(p,chunk,replace=True)
    assert after==hashes;write(path,m,replace=True)
    proof=ROOT/'results/verification/aggregation_fix.json';previous=read(proof) if proof.exists() else None
    history=previous.get('migrations',[previous]) if previous else []
    history.append(dict(changed_files=changed,old_workflow=old_workflow,new_workflow=current['workflow'],physical_rows_unchanged=len(hashes),row_hashes=hashes,old_manifest_fingerprint=oldfp,new_manifest_fingerprint=m['fingerprint'],thermal_reruns=0))
    write(proof,dict(status='PASS',original_physical_stage_elapsed_s=previous['original_physical_stage_elapsed_s'] if previous else progress['elapsed_s'],migrations=history),replace=proof.exists())
    print('PASS: 192 filas físicas preservadas; únicamente metadata de agregación actualizada')
if __name__=='__main__':main()
