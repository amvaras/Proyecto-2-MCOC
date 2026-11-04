"""Cuenta palabras y comprueba estructura y enlaces locales del dossier E06."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def inspect_dossier(path):
    path=Path(path).resolve()
    text=path.read_text(encoding='utf-8-sig')
    if any(ord(c)<32 and c not in '\n\r\t' for c in text):
        raise ValueError('Caracteres de control inválidos en Markdown')
    if '\\alpha' not in text or '\\rho' not in text:
        raise ValueError('Fórmula LaTeX incompleta o con escapes incorrectos')
    if '| Test | Qué verifica | Error/métrica | Resultado |' not in text:
        raise ValueError('Falta la cabecera exacta de la matriz')
    links=[]
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text):
        if target.startswith(('https://','http://','#')):continue
        resolved=(path.parent/target.strip('<>').split('#')[0]).resolve()
        if not resolved.is_relative_to(ROOT) or not resolved.is_file():
            raise ValueError('Enlace local inválido: '+target)
        links.append(dict(target=target,sha256=hashlib.sha256(resolved.read_bytes()).hexdigest()))
    # Prosa incluye títulos, listas y pies; tablas, bloques de código,
    # ecuaciones desplegadas e imágenes se contabilizan aparte.
    no_code=re.sub(r'```[\s\S]*?```',' ',text)
    no_equations=re.sub(r'\$\$[\s\S]*?\$\$',' ',no_code)
    no_images=re.sub(r'!\[[^\]]*\]\([^)]+\)',' ',no_equations)
    def words(s):
        s=re.sub(r'\[([^\]]*)\]\([^)]+\)',r'\1',s)
        s=re.sub(r'https?://\S+',' ',s)
        return re.findall(r"[^\W_]+(?:[.,’'−-][^\W_]+)*",s,re.UNICODE)
    prose='\n'.join(line for line in no_images.splitlines() if not line.lstrip().startswith('|'))
    report=dict(status='PASS',prose_words=len(words(prose)),all_visible_words=len(words(text)),
                limit_prose_words=1200,local_links_checked=len(links),links=links,
                counting_method='Palabras Unicode; títulos/listas/pies incluidos; tablas, imágenes, ecuaciones desplegadas y código excluidos solo de prosa; enlaces cuentan por etiqueta.')
    if report['prose_words']>1200:raise ValueError('Dossier excede 1200 palabras de prosa')
    for required in ('Convergencia espacial','Convergencia temporal','Conservación','Fuente','Robin','BIM','Simplificaciones','Repositorio','COMMIT E06 PENDIENTE DE PUBLICACIÓN'):
        if required not in text:raise ValueError('Contenido obligatorio ausente: '+required)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('path',type=Path,nargs='?',default=ROOT/'docs/E06_DOSSIER.md')
    p.add_argument('--json',type=Path)
    a=p.parse_args();r=inspect_dossier(a.path)
    if a.json:
        a.json.parent.mkdir(parents=True,exist_ok=True)
        a.json.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in r.items() if k!='links'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
