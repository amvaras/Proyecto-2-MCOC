"""Contar palabras y comprobar enlaces locales del dossier oficial."""
import json,re
from urllib.parse import unquote
from mcoc_p2.e11.pipeline import ROOT,write_json
def main():
    file=ROOT/'docs/E14_OPERACION.md';text=file.read_text(encoding='utf8');words=len(re.findall(r'\S+',text));broken=[]
    for raw in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text):
        if not raw.startswith(('https://','http://')) and not (file.parent/unquote(raw.split('#')[0])).is_file():broken.append(raw)
    report=dict(status='PASS' if words<=1400 and not broken else 'FAIL',words=words,limit=1400,broken_links=broken,commit='PENDIENTE DE PUBLICACIÓN')
    write_json(ROOT/'results/verification/dossier.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
    if report['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()

