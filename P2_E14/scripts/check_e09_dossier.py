"""Cuenta todo el texto visible y comprueba enlaces locales del dossier E09."""
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PENDING='COMMIT E09 PENDIENTE DE PUBLICACIÓN'
PUBLICATION_REF='entrega-e09'
PUBLICATION_URL=f'https://github.com/amvaras/Proyecto-2-MCOC/commit/{PUBLICATION_REF}'


def word_count(text):
    # No se excluyen tablas, ecuaciones ni bloques de código.
    text=re.sub(r'!\[[^\]]*\]\([^)]+\)',' ',text)
    text=re.sub(r'\[([^\]]*)\]\([^)]+\)',r'\1',text)
    text=re.sub(r'https?://\S+',' ',text)
    return len(re.findall(r"[^\W_]+(?:[.,’'−-][^\W_]+)*",text,re.UNICODE))


def inspect_dossier(path,*,root=ROOT,require_published=False):
    path=Path(path).resolve();root=Path(root).resolve();text=path.read_text(encoding='utf-8-sig')
    count=word_count(text)
    if count>1200:raise ValueError(f'Dossier: {count} palabras; máximo 1200')
    if 'https://github.com/amvaras/Proyecto-2-MCOC' not in text:raise ValueError('Repositorio ausente')
    match=re.search(r'^Commit evaluado:[ \t]*\*\*(.*?)\*\*[ \t]*$',text,re.MULTILINE)
    commit=match[1] if match else ''
    if f'Commit evaluado: [{PUBLICATION_REF}]({PUBLICATION_URL})' in text.splitlines():
        commit=f'refs/tags/{PUBLICATION_REF}'
    has_reference=commit==f'refs/tags/{PUBLICATION_REF}' or bool(re.fullmatch('[0-9a-f]{40}',commit))
    if commit!=PENDING and not has_reference:raise ValueError('Commit E09 ausente o inválido')
    if require_published and not has_reference:raise ValueError('Commit E09 pendiente de publicación')
    if '7029671' not in text or 'Qué reproduce' not in text or 'Qué no reproduce' not in text:raise ValueError('Comparación con Ju y Lei incompleta')
    images=[];links=[]
    for image,target in re.findall(r'(!?)\[[^\]]*\]\(([^)]+)\)',text):
        if target.startswith(('http://','https://','#')):continue
        file=(path.parent/target.strip('<>').split('#')[0]).resolve()
        if not file.is_relative_to(root) or not file.is_file():raise ValueError('Enlace local inválido: '+target)
        links.append(target)
        if image:
            if file.suffix!='.png' or not file.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Figura PNG inválida')
            images.append(target)
    if len(images)<8:raise ValueError('Dossier requiere las ocho categorías de figuras')
    return dict(status='PASS',words=count,limit=1200,includes_tables_code_equations=True,
                local_links=len(links),images=len(images),formal_status=commit,
                publication_verified=False,sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('path',type=Path,nargs='?',default=ROOT/'docs/E09_DOSSIER.md')
    p.add_argument('--require-published',action='store_true');p.add_argument('--json',type=Path)
    a=p.parse_args();r=inspect_dossier(a.path,require_published=a.require_published)
    if a.json:a.json.parent.mkdir(parents=True,exist_ok=True);a.json.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(r,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
