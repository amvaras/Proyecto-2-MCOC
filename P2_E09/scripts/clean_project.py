"""Limpieza conservadora: simulación por defecto; solo caches reconocidos."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
CACHES={'__pycache__','.pytest_cache','.mplconfig'}


def checked_path(root,path):
    root=Path(root).absolute();path=Path(path).absolute()
    if path==root or not path.is_relative_to(root):raise ValueError('Ruta fuera de la entrega o raíz completa')
    for part in [path,*path.parents]:
        if part==root:break
        if part.is_symlink() or part.is_junction():raise ValueError('No seguir enlaces ni junctions')
    if not path.resolve().is_relative_to(root.resolve()):raise ValueError('Destino resuelto fuera de la entrega')
    return path


def recognized(cache,relative):
    if cache=='__pycache__':return relative.suffix in ('.pyc','.pyo')
    if cache=='.mplconfig':return bool(re.fullmatch(r'fontlist-v\d+(?:\.\d+)*\.json',relative.name)) and len(relative.parts)==1
    return relative.as_posix() in {'.gitignore','CACHEDIR.TAG','README.md','v/cache/nodeids','v/cache/lastfailed','v/cache/stepwise'}


def plan_cleanup(root=ROOT):
    root=Path(root).absolute()
    if root.is_symlink() or root.is_junction() or not re.fullmatch(r'P2_E\d{2}',root.name):raise ValueError('Seleccionar una entrega P2_E## real')
    if not (root/'pyproject.toml').is_file() or not (root/'src').is_dir():raise ValueError('Faltan marcadores de proyecto')
    files=[];folders=[];skipped=[]
    for current,dirs,names in os.walk(root,followlinks=False):
        for d in list(dirs):
            path=Path(current)/d
            if path.is_symlink() or path.is_junction():dirs.remove(d);skipped.append(path.relative_to(root).as_posix());continue
            if d=='.git' or d.startswith('.venv') or re.fullmatch(r'P2_E\d{2}',d):dirs.remove(d);continue
            if d not in CACHES:continue
            dirs.remove(d);payload=[];cache_dirs=[];valid=True
            for parent,children,cache_names in os.walk(path,followlinks=False):
                for child in list(children):
                    p=Path(parent)/child
                    if p.is_symlink() or p.is_junction():valid=False;children.remove(child)
                cache_dirs.append(Path(parent))
                for name in cache_names:
                    p=Path(parent)/name
                    if p.is_symlink() or p.is_junction() or not recognized(d,p.relative_to(path)):valid=False
                    else:payload.append(p)
            if not valid:skipped.append(path.relative_to(root).as_posix());continue
            for p in payload:
                checked_path(root,p)
                files.append(dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),cache=d))
            folders.extend(p.relative_to(root).as_posix() for p in cache_dirs)
    return dict(root=str(root),mode='dry-run',files=sorted(files,key=lambda x:x['path']),
                empty_directories=sorted(set(folders),key=lambda x:len(Path(x).parts),reverse=True),
                skipped=skipped,total_bytes=sum(f['bytes'] for f in files))


def apply_cleanup(plan,root=ROOT,log=True):
    root=Path(root).absolute()
    if Path(plan['root'])!=root:raise ValueError('Plan corresponde a otra raíz')
    # Prevalidar todo; si apareció un archivo diferente, no eliminarlo.
    for row in plan['files']:
        p=checked_path(root,root/row['path'])
        if row['cache'] not in CACHES or row['cache'] not in p.relative_to(root).parts:raise ValueError('Archivo no reconocido')
        cache_parent=next(a for a in p.parents if a.name==row['cache'])
        if not recognized(row['cache'],p.relative_to(cache_parent)):raise ValueError('Contenido protegido')
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Archivo cambió desde el dry-run')
    for name in plan['empty_directories']:
        p=checked_path(root,root/name)
        if not any(part in CACHES for part in p.relative_to(root).parts):raise ValueError('Directorio protegido')
    deleted=[]
    for row in plan['files']:
        p=checked_path(root,root/row['path']);p.unlink();deleted.append(row['path'])
    for name in plan['empty_directories']:
        p=checked_path(root,root/name)
        if p.name not in CACHES and not any(a.name in CACHES for a in p.parents):raise ValueError('Directorio protegido')
        try:p.rmdir()
        except OSError:pass  # Archivo nuevo/desconocido: conservarlo.
    report=dict(mode='applied',utc=datetime.now(timezone.utc).isoformat(),deleted=deleted,
                deleted_files=len(deleted),deleted_bytes=plan['total_bytes'],skipped=plan['skipped'])
    if log and deleted:
        target=root/'results/verification/cleanup_last.json';target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report


def cleanup_caches(root=ROOT):
    """Hook de finalización para ejecutores; nunca borra resultados científicos."""
    return apply_cleanup(plan_cleanup(root),root)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true')
    args=parser.parse_args();plan=plan_cleanup()
    report=apply_cleanup(plan) if args.apply else plan
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
