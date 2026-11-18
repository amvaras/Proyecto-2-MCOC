"""Regresiones de fallos reales de reproducción, extensión y trazabilidad E06."""
import base64
import hashlib
import importlib
import json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def scripts(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT/'scripts'))
    return importlib.import_module('check_e06_dossier'), importlib.import_module('audit_integrity')


@pytest.fixture
def dossier(tmp_path):
    # PNG real de 1×1 para probar enlaces; las figuras científicas se generan
    # y revisan por separado en la ejecución de integración.
    png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a6S8AAAAASUVORK5CYII=')
    for name in ('espacial.png','temporal.png','bim.png'):(tmp_path/name).write_bytes(png)
    (tmp_path/'base.ifc').write_text('ISO-10303-21;',encoding='utf-8')
    labels=('Exacta 1D','Exacta 2D','Exacta 3D','Convergencia espacial',
            'Convergencia temporal','Conservación','Fuente','Neumann','Robin','Estabilidad')
    matrix='\n'.join(f'| {label} | Caso analítico | Error bajo tolerancia | PASS |' for label in labels)
    text='''# E06
## Repositorio
Repositorio: [proyecto](https://github.com/amvaras/Proyecto-2-MCOC).
Commit evaluado: **COMMIT E06 PENDIENTE DE PUBLICACIÓN**
| Test | Qué verifica | Error/métrica | Resultado |
|---|---|---|---|
'''+matrix+r'''
\alpha=k/(\rho c_p)
## BIM
![Espacial](espacial.png)
![Temporal](temporal.png)
![BIM](bim.png)
[IFC](base.ifc)
## Simplificaciones
Geometría docente.
'''
    path=tmp_path/'dossier.md';path.write_text(text,encoding='utf-8')
    return path


def test_pending_is_explicit_and_publication_can_be_required(scripts,dossier):
    checker,_=scripts
    original=dossier.read_text(encoding='utf-8')
    for ending in ('', '.'):
        dossier.write_text(original.replace('PUBLICACIÓN**','PUBLICACIÓN**'+ending),encoding='utf-8')
        report=checker.inspect_dossier(dossier,root=dossier.parent)
        assert report['status']=='PASS' and not report['published_commit_declared']
        assert report['figures_checked']==3 and report['ifc_links_checked']==1
    with pytest.raises(ValueError,match='pendiente'):
        checker.inspect_dossier(dossier,root=dossier.parent,require_published=True)


def test_checker_accepts_real_sha_format_without_demanding_pending_marker(scripts,dossier):
    checker,_=scripts
    text=dossier.read_text(encoding='utf-8').replace('COMMIT E06 PENDIENTE DE PUBLICACIÓN','a'*40)
    dossier.write_text(text,encoding='utf-8')
    report=checker.inspect_dossier(dossier,root=dossier.parent,require_published=True)
    assert report['published_commit_declared'] and report['evaluated_commit']=='a'*40
    # La comprobación es estructural, no una consulta remota ni prueba de publicación.


@pytest.mark.parametrize('wrapper',['{}','```text\n{}\n```','$$\n{}\n$$'])
def test_word_limit_counts_code_and_equations_too(scripts,dossier,wrapper):
    checker,_=scripts
    with dossier.open('a',encoding='utf-8') as stream:
        stream.write('\n'+wrapper.format('palabra '*1201))
    with pytest.raises(ValueError,match='1200'):
        checker.inspect_dossier(dossier,root=dossier.parent)


@pytest.mark.parametrize('old,new,reason',[
    ('bim.png','ausente.png','Enlace'),
    ('[IFC](base.ifc)','','IFC'),
    ('| Exacta 3D | Caso analítico | Error bajo tolerancia | PASS |','','matriz'),
    ('COMMIT E06 PENDIENTE DE PUBLICACIÓN','abcdef','Commit'),
])
def test_missing_evidence_and_incomplete_identification_are_rejected(scripts,dossier,old,new,reason):
    checker,_=scripts
    dossier.write_text(dossier.read_text(encoding='utf-8').replace(old,new),encoding='utf-8')
    with pytest.raises(ValueError,match=reason):checker.inspect_dossier(dossier,root=dossier.parent)


def test_fake_png_is_rejected(scripts,dossier):
    checker,_=scripts
    (dossier.parent/'bim.png').write_text('no es una figura',encoding='utf-8')
    with pytest.raises(ValueError,match='PNG'):checker.inspect_dossier(dossier,root=dossier.parent)


def test_link_outside_project_is_rejected(scripts,dossier,tmp_path):
    checker,_=scripts
    outside=tmp_path.parent/'outside_e06.ifc';outside.write_text('IFC',encoding='utf-8')
    dossier.write_text(dossier.read_text(encoding='utf-8').replace('base.ifc','../outside_e06.ifc'),encoding='utf-8')
    with pytest.raises(ValueError,match='Enlace'):checker.inspect_dossier(dossier,root=dossier.parent)


def test_recorded_revision_does_not_mask_new_tampering(scripts,tmp_path):
    _,integrity=scripts
    path=tmp_path/'solver.py';path.write_bytes(b'base')
    old=hashlib.sha256(path.read_bytes()).hexdigest()
    files={'solver.py':{'sha256':old}}
    assert integrity.inspect_inventory(tmp_path,files)['unchanged']==1
    path.write_bytes(b'revision verificada')
    current=hashlib.sha256(path.read_bytes()).hexdigest()
    record=tmp_path/'revisiones.json'
    record.write_text(json.dumps({'files':{'solver.py':{
        'original_sha256':[old],'current_sha256':current,'reason':'Corrección documentada'}}}),encoding='utf-8')
    report=integrity.inspect_inventory(tmp_path,files,revisions=record)
    assert report['checked']==1 and len(report['documented_revisions'])==1
    path.write_bytes(b'otro cambio no documentado')
    with pytest.raises(ValueError,match='solver.py'):integrity.inspect_inventory(tmp_path,files,revisions=record)


@pytest.mark.parametrize('mutation',['unregistered','missing','wrong_original'])
def test_integrity_rejects_unknown_or_missing_content(scripts,tmp_path,mutation):
    _,integrity=scripts
    path=tmp_path/'base.py';path.write_bytes(b'base')
    old=hashlib.sha256(path.read_bytes()).hexdigest()
    files={'base.py':{'sha256':old}}
    record=tmp_path/'revisiones.json'
    if mutation=='missing':
        files={'missing.py':{'sha256':old}}
    else:
        path.write_bytes(b'distinto')
    record.write_text(json.dumps({'files':{} if mutation!='wrong_original' else {'base.py':{
        'original_sha256':['0'*64],'current_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'reason':'No corresponde al inventario'}}}),encoding='utf-8')
    with pytest.raises(ValueError,match='Integridad'):integrity.inspect_inventory(tmp_path,files,revisions=record)
