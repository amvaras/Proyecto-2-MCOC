"""Límite estricto, trazabilidad formal y enlaces del dossier E09."""
import importlib.util
from pathlib import Path
import pytest
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('e09_checker',ROOT/'scripts/check_e09_dossier.py')
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)


@pytest.fixture
def document(tmp_path):
    # Imagen artificial solo para probar validación documental, no evidencia física.
    Image.new('RGB',(2,2),'white').save(tmp_path/'test.png')
    text='# E09\nRepositorio https://github.com/amvaras/Proyecto-2-MCOC\nCommit evaluado: **COMMIT E09 PENDIENTE DE PUBLICACIÓN**\nQué reproduce y Qué no reproduce; DOI 7029671.\n'
    text+='\n'.join(f'![Figura {i}](test.png)' for i in range(8))
    p=tmp_path/'dossier.md';p.write_text(text,encoding='utf-8');return p


def test_word_counter_includes_code_tables_and_equations():
    assert checker.word_count('uno dos\n~~~text\ntres cuatro\n~~~\n| cinco | seis |\n$$ siete ocho $$')>=9
    assert checker.word_count('![No contar imagen](figura.png) [Etiqueta](https://example.com)')==1


def test_pending_commit_is_allowed_but_not_claimed_published(document):
    r=checker.inspect_dossier(document,root=document.parent)
    assert r['status']=='PASS' and not r['publication_verified'] and r['images']==8
    with pytest.raises(ValueError,match='pendiente'):checker.inspect_dossier(document,root=document.parent,require_published=True)


def test_publication_tag_identifies_e09_commit(document):
    text=document.read_text(encoding='utf-8')
    document.write_text(text.replace(f'**{checker.PENDING}**',
                                     f'[{checker.PUBLICATION_REF}]({checker.PUBLICATION_URL})'),encoding='utf-8')
    result=checker.inspect_dossier(document,root=document.parent,require_published=True)
    assert result['formal_status']=='refs/tags/entrega-e09'


def test_long_text_cannot_be_hidden_in_code_or_tables(document):
    with document.open('a',encoding='utf-8') as stream:stream.write('\n~~~\n'+'palabra '*1201+'\n~~~')
    with pytest.raises(ValueError,match='1200'):checker.inspect_dossier(document,root=document.parent)


@pytest.mark.parametrize('target',['ausente.png','../outside.png'])
def test_dossier_rejects_missing_or_external_images(document,target):
    Image.new('RGB',(2,2)).save(document.parent.parent/'outside.png')
    s=document.read_text(encoding='utf-8').replace('test.png',target);document.write_text(s,encoding='utf-8')
    with pytest.raises(ValueError,match='Enlace'):checker.inspect_dossier(document,root=document.parent)
