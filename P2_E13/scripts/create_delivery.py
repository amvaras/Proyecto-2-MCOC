"""Base selectiva E13; dry-run primero. No copia resultados ni entornos."""
from pathlib import Path
import argparse, hashlib, json, os, shutil
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parent/'P2_E12'
EXCLUDE={'.git','__pycache__','.pytest_cache','.runtime','.tmp','.mplconfig'}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(folder):
    rows={}
    for current,dirs,names in os.walk(folder,followlinks=False):
        dirs[:]=[n for n in dirs if n not in EXCLUDE and not n.startswith('.venv') and not n.endswith('.egg-info')]
        for n in names:
            p=Path(current)/n
            if p.is_symlink() or p.is_junction():raise ValueError('No seguir enlaces')
            if p.suffix not in {'.pyc','.pyo'}:rows[p.relative_to(folder).as_posix()]=digest(p)
    return dict(sorted(rows.items()))
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    assert ROOT.name=='P2_E13' and 'OneDrive' in ROOT.parts
    files=[]
    for name in ('.gitattributes','.gitignore','pyproject.toml','requirements-lock.txt'):files.append(SOURCE/name)
    for name in ('src','tests','examples','scripts','configs','geometry','web','data'):
        for current,dirs,names in os.walk(SOURCE/name,followlinks=False):
            dirs[:]=[n for n in dirs if n not in EXCLUDE and not n.endswith('.egg-info')]
            for n in names:
                p=Path(current)/n
                if p.suffix in {'.pyc','.pyo','.log'} or p.relative_to(SOURCE).as_posix()=='scripts/create_delivery.py':continue
                if p.is_symlink() or p.is_junction():raise ValueError('No seguir enlaces')
                files.append(p)
    rows=[dict(path=p.relative_to(SOURCE).as_posix(),sha256=digest(p),bytes=p.stat().st_size) for p in sorted(files)]
    report=dict(source='P2_E12',destination='P2_E13',mode='dry-run',files=rows,bytes=sum(r['bytes'] for r in rows))
    if args.apply:
        before=inventory(SOURCE)
        for row in rows:
            target=ROOT/row['path'];source=SOURCE/row['path']
            if target.exists():
                if digest(target)!=row['sha256']:raise ValueError('Preservar archivo existente: '+row['path'])
                continue
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
            assert not os.path.samefile(source,target) and digest(target)==row['sha256']
        proof=ROOT/'results/verification';proof.mkdir(parents=True,exist_ok=True)
        report['mode']='created';(proof/'base.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        (proof/'E12_integrity.json').write_text(json.dumps(dict(before=before,after=None),indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2));print('Archivos:',len(rows))
if __name__=='__main__':main()
