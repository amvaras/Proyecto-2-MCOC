"""Lista exacta para una publicación futura; no cambia Git ni copia archivos.

Dry-run por defecto; --write guarda lista y SHA dentro de E14.
"""
from pathlib import Path
import argparse,hashlib,json,os
from mcoc_p2.e14.io import ROOT,read,write

LIST=ROOT/'docs/E14_ARCHIVOS_A_VERSIONAR.txt'
REPORT=ROOT/'results/verification/publication_e14.json'
SKIP={'.git','.runtime','.tmp','.pytest_cache','.mplconfig','__pycache__','build','dist'}
TOP={'src','tests','examples','scripts','configs','geometry','data','web','docs','figures','vtk','results'}
ROOTFILES={'.gitignore','.gitattributes','AGENTS.md','README.md','pyproject.toml','requirements-lock.txt','Iniciar E14.bat'}

def candidates():
    files=[]
    for current,dirs,names in os.walk(ROOT,followlinks=False):
        current=Path(current)
        for name in list(dirs):
            p=current/name
            if p.is_symlink() or p.is_junction():raise ValueError('Preservar enlace sin publicarlo')
            if name in SKIP or name.startswith('.venv') or name.endswith('.egg-info'):dirs.remove(name)
            elif current==ROOT and name not in TOP:dirs.remove(name)
            elif p==ROOT/'results/web_runs':dirs.remove(name)
            elif p==ROOT/'results/e14/hpc':dirs.remove(name)  # futuros jobs, no conjunto oficial
        for name in names:
            p=current/name;rel=p.relative_to(ROOT)
            if p.is_symlink() or p.is_junction():raise ValueError('Preservar enlace sin publicarlo')
            if current==ROOT and name not in ROOTFILES:continue
            if name.startswith('.env') or p.suffix in {'.log','.lock','.pyc','.pyo','.zip','.whl'} or '.tmp-' in name:continue
            if rel.parts[0]=='results' and rel.parts[1] not in {'e13','e14','verification'}:continue
            files.append(p)
    return sorted(set(files)|{LIST,REPORT},key=lambda p:p.relative_to(ROOT).as_posix())

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--write',action='store_true');a=p.parse_args();paths=candidates()
    if not (ROOT/'results/e14/official.json').is_file():raise ValueError('Sellar y verificar primero el conjunto científico')
    text=''.join('P2_E14/'+p.relative_to(ROOT).as_posix()+'\n' for p in paths)
    if a.write:LIST.write_text(text,encoding='utf8')
    rows=[]
    for path in paths:
        if path==REPORT:continue  # no hash autorreferente
        if not path.exists():
            if path==LIST and not a.write:continue
            raise ValueError('Archivo pendiente o ausente: '+str(path))
        rows.append(dict(source=path.relative_to(ROOT).as_posix(),target='P2_E14/'+path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    largest=max(rows,key=lambda r:r['bytes'])
    data=dict(mode='prepared' if a.write else 'dry-run',files_to_publish=len(paths),bytes_without_this_report=sum(r['bytes'] for r in rows),
       destination_prefix='P2_E14/',branch_proposal='codex/e14',current_git_state='results/verification/git_e14.json',
       official_fingerprint=read(ROOT/'results/e14/official.json')['fingerprint'],files=rows,self_report='Añadir también P2_E14/results/verification/publication_e14.json; su SHA no se incluye dentro de sí mismo',
       exclusions='Entornos, bytecode, caches recreables, logs, ZIP, credenciales, pruebas web y futuros jobs HPC',largest_file=largest,
       actions_performed='Solo lectura y, con --write, estos dos índices; sin git add, commits, ramas, fetch, push ni copias al checkout')
    if a.write:write(REPORT,data,replace=True)
    print(json.dumps({k:v for k,v in data.items() if k!='files'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
