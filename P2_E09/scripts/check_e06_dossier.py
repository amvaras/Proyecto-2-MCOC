"""Comprueba extensión, contenidos, commit y enlaces del dossier E06."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PENDING='COMMIT E06 PENDIENTE DE PUBLICACIÓN'


def inspect_dossier(path, *, root=ROOT, require_published=False):
    path=Path(path).resolve()
    root=Path(root).resolve()
    text=path.read_text(encoding='utf-8-sig')
    if any(ord(c)<32 and c not in '\n\r\t' for c in text):
        raise ValueError('Caracteres de control inválidos en Markdown')
    if '\\alpha' not in text or '\\rho' not in text:
        raise ValueError('Fórmula LaTeX incompleta o con escapes incorrectos')
    if '| Test | Qué verifica | Error/métrica | Resultado |' not in text:
        raise ValueError('Falta la cabecera exacta de la matriz')
    matrix=text.split('| Test | Qué verifica | Error/métrica | Resultado |',1)[1]
    matrix='\n'.join(line for line in matrix.splitlines() if line.lstrip().startswith('|'))
    for label in ('Exacta 1D','Exacta 2D','Exacta 3D','Convergencia espacial',
                  'Convergencia temporal','Conservación','Fuente','Neumann','Robin','Estabilidad'):
        if label not in matrix:raise ValueError('Falta caso en matriz: '+label)
    if 'https://github.com/amvaras/Proyecto-2-MCOC' not in text:
        raise ValueError('Falta el repositorio del proyecto')
    match=re.search(r'^Commit evaluado:\s*(.+)$',text,re.MULTILINE)
    value=re.sub(r'[*`]', '', match[1]).strip().rstrip('.') if match else ''
    published=bool(re.fullmatch(r'[0-9a-fA-F]{40}',value))
    if not published and value!=PENDING:
        raise ValueError('Commit evaluado debe ser SHA de 40 caracteres o pendiente explícito')
    if require_published and not published:
        raise ValueError('El commit evaluado sigue pendiente de publicación')
    links=[];images=[];ifc_links=[]
    for image,target in re.findall(r'(!?)\[[^\]]*\]\(([^)]+)\)',text):
        if target.startswith(('https://','http://','#')):continue
        resolved=(path.parent/target.strip('<>').split('#')[0]).resolve()
        if not resolved.is_relative_to(root) or not resolved.is_file():
            raise ValueError('Enlace local inválido: '+target)
        links.append(dict(target=target,sha256=hashlib.sha256(resolved.read_bytes()).hexdigest()))
        if image:
            if resolved.suffix.lower()!='.png' or not resolved.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):
                raise ValueError('Figura PNG inválida: '+target)
            images.append(target)
        if resolved.suffix.lower()=='.ifc':ifc_links.append(target)
    if len(images)<3 or not ifc_links:
        raise ValueError('Se requieren las figuras de convergencia/BIM y enlace al IFC')
    # Solo figuras/tablas se excluyen: las fórmulas y el contenido de código
    # sí cuentan. No se permite ocultar prosa en bloques de código.
    no_images=re.sub(r'!\[[^\]]*\]\([^)]+\)',' ',text)
    def words(s):
        s=re.sub(r'\[([^\]]*)\]\([^)]+\)',r'\1',s)
        s=re.sub(r'https?://\S+',' ',s)
        return re.findall(r"[^\W_]+(?:[.,’'−-][^\W_]+)*",s,re.UNICODE)
    prose='\n'.join(line for line in no_images.splitlines() if not line.lstrip().startswith('|'))
    report=dict(status='PASS',prose_words=len(words(prose)),all_visible_words=len(words(text)),
                limit_prose_words=1200,local_links_checked=len(links),links=links,
                figures_checked=len(images),ifc_links_checked=len(ifc_links),
                evaluated_commit=value,published_commit_declared=published,
                formal_status='SHA declarado; comprobar publicación al entregar' if published else PENDING,
                counting_method='Palabras Unicode, incluidos títulos, listas, pies, fórmulas y código; solo tablas e imágenes excluidas del límite. Enlaces cuentan por etiqueta.')
    if report['prose_words']>1200:raise ValueError('Dossier excede 1200 palabras de prosa')
    for required in ('Convergencia espacial','Convergencia temporal','Conservación','Fuente','Robin','BIM','Simplificaciones','Repositorio'):
        if required not in text:raise ValueError('Contenido obligatorio ausente: '+required)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('path',type=Path,nargs='?',default=ROOT/'docs/E06_DOSSIER.md')
    p.add_argument('--json',type=Path)
    p.add_argument('--require-published',action='store_true')
    a=p.parse_args();r=inspect_dossier(a.path,require_published=a.require_published)
    if a.json:
        a.json.parent.mkdir(parents=True,exist_ok=True)
        a.json.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in r.items() if k!='links'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
