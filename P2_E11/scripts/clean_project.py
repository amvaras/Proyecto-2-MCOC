"""Limpieza conservadora: simulación por defecto; solo caches reconocidos."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys

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


def development_plan(root=ROOT,include_environments=True):
    """Finalización E11 explícita; no se invoca desde hooks ni --apply normal.

    Solo entornos/temporales que esta sesión creó y documentó. La aplicación
    exige el mismo inventario completo y nunca borra directorios recursivamente.
    """
    root=Path(root).resolve()
    proof=root/'results/verification/environment.json'
    if root.name!='P2_E11' or not proof.is_file():raise ValueError('Falta evidencia de propiedad E11')
    if not json.loads(proof.read_text(encoding='utf-8'))['fresh_environment']:raise ValueError('Entornos no acreditados')
    files=[];dirs=[]
    targets=(('.venv','.venv-repro','src/mcoc_p2.egg-info') if include_environments else ())+('.runtime','.tmp','install.log')
    for name in targets:
        target=checked_path(root,root/name)
        if not target.exists():continue
        if Path(sys.prefix).resolve().is_relative_to(target):raise ValueError('No retirar el entorno que ejecuta la limpieza; usar py -3.12')
        if target.is_file():payload=[target]
        else:
            payload=[]
            for current,children,names in os.walk(target,followlinks=False):
                checked_path(root,Path(current));dirs.append(Path(current).relative_to(root).as_posix())
                for child in children:checked_path(root,Path(current)/child)
                payload.extend(Path(current)/n for n in names)
        for p in payload:
            checked_path(root,p)
            files.append(dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    return dict(root=str(root),files=sorted(files,key=lambda r:r['path']),directories=sorted(dirs,key=lambda p:(len(Path(p).parts),p),reverse=True),
                mode='dry-run',purpose='Solo desarrollo propio E11; no resultados oficiales',targets=list(targets),include_environments=include_environments)


def apply_development(plan,root=ROOT):
    root=Path(root).resolve()
    # Revalidar archivos, hashes, directorios, límites y entorno ANTES de borrar.
    current=development_plan(root,plan.get('include_environments',True))
    if current!=plan:raise ValueError('El inventario cambió; rehacer dry-run')
    for row in plan['files']:checked_path(root,root/row['path']).unlink()
    for name in plan['directories']:checked_path(root,root/name).rmdir()  # Solo si vacío.
    report=dict(mode='applied',method='SHA256 preflight; individual unlink; empty rmdir; no recursive delete',
                removed_files=len(plan['files']),removed_bytes=sum(r['bytes'] for r in plan['files']),
                roots=plan['targets'])
    (root/'results/verification/owned_cleanup.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true')
    parser.add_argument('--owned-development',action='store_true',help='Finalizar temporales propios E11 con inventario; usar Python fuera del entorno')
    parser.add_argument('--owned-runtime',action='store_true',help='Solo .runtime/.tmp propios; preserva entornos activos')
    args=parser.parse_args()
    if args.owned_development or args.owned_runtime:
        plan_path=ROOT/'.e11_cleanup_plan.json'
        if args.apply:
            plan=json.loads(plan_path.read_text(encoding='utf-8'))
            if plan.get('include_environments',True)==args.owned_runtime:raise ValueError('El plan no corresponde al alcance solicitado')
            report=apply_development(plan);plan_path.unlink()
        else:
            plan=development_plan(include_environments=not args.owned_runtime);plan_path.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
            report=dict(mode='dry-run',files=len(plan['files']),bytes=sum(r['bytes'] for r in plan['files']),plan=plan_path.name)
        print(json.dumps(report,ensure_ascii=False,indent=2));return
    plan=plan_cleanup()
    report=apply_cleanup(plan) if args.apply else plan
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
