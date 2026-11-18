"""Base selectiva E14 y reutilización de evidencia científica vigente autorizada."""
from pathlib import Path
import os,hashlib,json,shutil,argparse
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT.parent/'P2_E13'
SKIP={'.git','.runtime','.tmp','__pycache__','.pytest_cache','.mplconfig'}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inventory(folder):
    out={}
    for current,dirs,names in os.walk(folder,followlinks=False):
        dirs[:]=[n for n in dirs if n not in SKIP and not n.startswith('.venv') and not n.endswith('.egg-info')]
        for n in names:
            p=Path(current)/n
            if p.is_symlink() or p.is_junction():raise ValueError('No seguir enlaces')
            if p.suffix not in {'.pyc','.pyo'}:out[p.relative_to(folder).as_posix()]=digest(p)
    return dict(sorted(out.items()))
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--apply',action='store_true');a=ap.parse_args()
    assert ROOT.name=='P2_E14' and 'OneDrive' in ROOT.parts
    selected=[SOURCE/n for n in ('.gitignore','.gitattributes','pyproject.toml','requirements-lock.txt')]
    for name in ('src','tests','examples','scripts','configs','geometry','data','web'):
        for current,dirs,names in os.walk(SOURCE/name,followlinks=False):
            dirs[:]=[n for n in dirs if n not in SKIP and not n.endswith('.egg-info')]
            for n in names:
                p=Path(current)/n;rel=p.relative_to(SOURCE).as_posix()
                if p.suffix not in {'.pyc','.pyo','.log'} and rel not in {'scripts/create_delivery.py','scripts/document_e13.py'}:selected.append(p)
    # Únicamente resultados actuales que evitan repetir E13: 120 métricas,
    # controles y un caso de campos usado como baseline/regresión. No inventarios,
    # JUnit, documentación, figuras ni resultados de desarrollo históricos.
    for name in ('results/e13','vtk/e13'):
        selected.extend(p for p in (SOURCE/name).rglob('*') if p.is_file())
    for name in ('controls.json','benchmark.json'):selected.append(SOURCE/'results/verification'/name)
    rows=[dict(path=p.relative_to(SOURCE).as_posix(),bytes=p.stat().st_size,sha256=digest(p)) for p in sorted(set(selected))]
    report=dict(source='P2_E13',destination='P2_E14',mode='dry-run',files=rows,bytes=sum(r['bytes'] for r in rows),
        reuse_authorization='Encargo cierre: inventariar/reutilizar cálculos vigentes, no repetirlos; copias físicas selectivas para autonomía')
    if a.apply:
        before=inventory(SOURCE)
        for row in rows:
            p=SOURCE/row['path'];q=ROOT/row['path']
            if q.exists():
                if digest(q)!=row['sha256']:raise ValueError('Preservar trabajo existente: '+row['path'])
                continue
            q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);assert digest(q)==row['sha256'] and not os.path.samefile(p,q)
        proof=ROOT/'results/verification';proof.mkdir(parents=True,exist_ok=True);report['mode']='created'
        (proof/'base.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        (proof/'E13_integrity.json').write_text(json.dumps(dict(before=before,after=None),indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='files'},ensure_ascii=False,indent=2));print('Archivos:',len(rows))
if __name__=='__main__':main()
