"""E02: cambios IFC reales en fixtures Python, sin atribuir autoría Bonsai."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
import ifcopenshell
from ifcopenshell.api import pset, root

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'geometry/foundation.ifc'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, ROOT/path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cmp = load('scripts/compare_ifc_e02.py', 'cmp_e02')
demo = load('examples/run_e02_1d.py', 'demo_e02')


def modified(tmp_path):
    model = ifcopenshell.open(str(BASE))
    element = next(e for e in model.by_type('IfcFooting') if e.Name == 'Vertida_03')
    prop = next(r.RelatingPropertyDefinition for r in element.IsDefinedBy
                if r.is_a('IfcRelDefinesByProperties') and r.RelatingPropertyDefinition.Name == 'UANDES_HormigonMasivo')
    pset.edit_pset(model, pset=prop, properties={'Estado':'Fixture Python E02, NO Bonsai'})
    path = tmp_path/'fixture_python.ifc'
    model.write(str(path))
    return path


def test_read_and_identical(tmp_path):
    model = ifcopenshell.open(str(BASE))
    path = tmp_path/'resaved.ifc'
    model.write(str(path))
    report = cmp.compare(BASE,path)
    assert report['before_elements'] == 5
    assert not report['different']


def test_property_change_and_preserve_base(tmp_path):
    digest = hashlib.sha256(BASE.read_bytes()).hexdigest()
    path = modified(tmp_path)
    report = cmp.compare(BASE,path)
    assert len(report['changes']) == 1
    row = report['changes'][0]
    assert row['name'] == 'Vertida_03'
    assert row['field'] == 'UANDES_HormigonMasivo.Estado'
    assert row['before'] == 'Preliminar E01; sin plan constructivo optimizado'
    assert row['after'] == 'Fixture Python E02, NO Bonsai'
    assert hashlib.sha256(BASE.read_bytes()).hexdigest() == digest


def test_added_removed(tmp_path):
    model = ifcopenshell.open(str(BASE))
    element = model.by_type('IfcFooting')[0]
    guid = element.GlobalId
    root.remove_product(model, product=element)
    added = root.create_entity(model, ifc_class='IfcFooting', name='Nuevo fixture')
    path = tmp_path/'membership.ifc'
    model.write(str(path))
    report = cmp.compare(BASE,path)
    assert [x['guid'] for x in report['removed']] == [guid]
    assert [x['guid'] for x in report['added']] == [added.GlobalId]


@pytest.mark.parametrize('content', ['', 'no es IFC'])
def test_invalid(tmp_path,content):
    p = tmp_path/'invalid.ifc';p.write_text(content)
    with pytest.raises(ValueError,match='No se pudo leer'):
        cmp.compare(BASE,p)


def test_missing_file(tmp_path):
    with pytest.raises(ValueError,match='inexistente'):
        cmp.snapshot(tmp_path/'missing.ifc')


def test_duplicate_guid(tmp_path):
    model = ifcopenshell.open(str(BASE));els=model.by_type('IfcFooting')
    els[1].GlobalId=els[0].GlobalId
    p=tmp_path/'duplicate.ifc';model.write(str(p))
    with pytest.raises(ValueError,match='duplicado'):
        cmp.snapshot(p)


def test_cli_changed_and_unchanged(tmp_path):
    command=[sys.executable,str(ROOT/'scripts/compare_ifc_e02.py'),str(BASE)]
    assert subprocess.run(command+[str(BASE),'--require-change'],capture_output=True).returncode == 1
    path=modified(tmp_path)
    completed=subprocess.run(command+[str(path),'--require-change','--json',str(tmp_path/'report.json')],capture_output=True,text=True)
    assert completed.returncode == 0
    assert 'Fixture Python E02, NO Bonsai' in completed.stdout
    assert subprocess.run(command+[str(tmp_path/'missing')],capture_output=True).returncode == 2


def test_nx_dx_fo_and_base_benchmark():
    report, result, exact=demo.run_case()
    assert result.temperature.shape[1] == 81
    assert report['dx_m'] == .0125
    assert report['effective_dt_s'] == 67.5
    assert report['fourier'] == pytest.approx(.4)
    assert report['steps'] == 1280
    assert report['error_exact_C'] == pytest.approx(.0006451356521708362,abs=1e-12)
    assert np.max(np.abs(result.temperature[-1]-exact)) == report['error_exact_C']


def test_dt_changes_temporal_error():
    coarse, a, _=demo.run_case(dt=67.5)
    fine, b, _=demo.run_case(dt=33.75)
    assert fine['effective_dt_s'] == coarse['effective_dt_s']/2
    assert b.steps == 2*a.steps
    assert not np.array_equal(a.temperature[-1],b.temperature[-1])
    assert fine['error_temporal_semidiscrete_C'] < coarse['error_temporal_semidiscrete_C']


def test_spatial_comparison_same_dt():
    a,sol_a,_=demo.run_case(nx=41,dt=1.)
    b,sol_b,_=demo.run_case(nx=81,dt=1.)
    assert sol_a.temperature.shape[1] == 41
    assert sol_b.temperature.shape[1] == 81
    assert a['dx_m'] == 2*b['dx_m']
    assert a['t_end_s'] == b['t_end_s'] == 86400
    assert a['effective_dt_s'] == b['effective_dt_s']
    assert b['error_exact_C'] < a['error_exact_C']/3.5


def test_unstable_is_rejected():
    with pytest.raises(ValueError,match='cota'):
        demo.run_case(nx=81,dt=100.)


def test_arrival_and_invalid_nx():
    report,_,_=demo.run_case(dt=67.5,t_end=1000.)
    assert report['t_end_s'] == 1000.
    assert report['effective_dt_s'] <= 67.5
    with pytest.raises(ValueError):
        demo.run_case(nx=2)
