"""E07: errores geométricos visibles y parámetros efectivos de construcción."""
import json
from pathlib import Path
import subprocess
import sys
import warnings

import numpy as np
import pytest
from numpy.testing import assert_allclose

from mcoc_p2 import Material
from mcoc_p2.e07.construction import ConstructionState, PourEvent
from mcoc_p2.e07.coupling import MaskedAssembly
from mcoc_p2.e07.faces import contacts, exposed_faces
from mcoc_p2.e07.geometry import ClosedMesh
from mcoc_p2.e07.hydration import AdiabaticCurve
from mcoc_p2.e07.voxel import voxelize
from e07_helpers import cube, labelled, solid

ROOT=Path(__file__).resolve().parents[1]
MAT=Material(2.,2400.,900.)


def test_total_volume_cannot_hide_compensating_pour_errors():
    vox=labelled([[[7,11]]])
    vox.reference_volumes={7:1.5,11:.5}
    report=vox.report()
    assert report['relative_error']==0 and report['signed_error_m3']==0
    assert report['sum_absolute_pour_errors_m3']==pytest.approx(1.)
    assert report['max_pour_relative_error']==pytest.approx(1.)
    assert [r['signed_error_m3'] for r in report['by_pour']]==[-.5,.5]


def test_staircase_area_bias_survives_volume_refinement(record_property):
    original=cube();angle=np.pi/4
    rotation=np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]])
    mesh=ClosedMesh(original.vertices@rotation.T+[1,1,0],original.triangles)
    rows=[]
    for n in (20,40,80):
        vox=voxelize([solid(mesh)],(np.sqrt(2)/n,np.sqrt(2)/n,.1))
        rows.append(dict(n=n,dx_m=np.sqrt(2)/n,volume_m3=vox.report()['volume_voxel_m3'],
                         staircase_area_m2=exposed_faces(vox).report()['area_m2']))
    assert abs(rows[-1]['volume_m3']-1)<.03
    assert abs(rows[-1]['volume_m3']-1)<abs(rows[0]['volume_m3']-1)
    # Rotar un cubo unitario no cambia su área física: 6 m². La suma de caras
    # cartesianas tiende a 2+4*sqrt(2), no a 6, para esta orientación.
    assert rows[-1]['staircase_area_m2']-6>1.5
    assert abs(rows[-1]['staircase_area_m2']-(2+4*np.sqrt(2)))<.06
    record_property('e07_audit_scientific',json.dumps(dict(case='staircase_rotated_cube',
        exact_volume_m3=1.,exact_area_m2=6.,cartesian_area_limit_m2=2+4*np.sqrt(2),rows=rows)))


def test_new_activation_adds_only_new_material_energy_and_changes_contact():
    vox=labelled([[[7,11]]],(2.,3.,4.))
    other=Material(4.,2200.,800.)
    events=[PourEvent(7,0,30.,MAT,AdiabaticCurve()),PourEvent(11,10,20.,other,AdiabaticCurve())]
    state=ConstructionState(vox,events);state.temperature_C[0,0,0]=47.
    before=MaskedAssembly(vox,state.active_mask(),{7:MAT,11:other})
    old_energy=before.energy(state.temperature_C)
    assert len(contacts(vox,state.active_mask())['area_m2'])==0
    assert np.isnan(state.temperature_C[0,0,1])
    state.advance_to(10.)
    after=MaskedAssembly(vox,state.active_mask(),{7:MAT,11:other})
    assert state.temperature_C[0,0,0]==47.
    assert after.energy(state.temperature_C)==pytest.approx(old_energy+2200*800*24*20)
    assert len(contacts(vox,state.active_mask())['area_m2'])==1
    assert after.faces.areas.sum()==pytest.approx(92.)
    power,outward=after.power(state.temperature_C)
    assert power.sum()==pytest.approx(0.,abs=1e-10) and outward==0


@pytest.mark.parametrize('time',[0.,5.,10.,15.,20.])
def test_effective_hydration_budget_units_age_and_exhaustion(time,record_property):
    vox=labelled([[[7,11]]],(2.,1.,1.))
    events=[PourEvent(7,0,20,MAT,AdiabaticCurve(1000.,10.)),
            PourEvent(11,10,22,Material(3.,2000.,1000.),AdiabaticCurve(2000.,10.))]
    state=ConstructionState(vox,events)
    for t in state.time_grid(time,7.):state.advance_to(float(t))
    rows=state.hydration_report();by_id={r['vertida_id']:r for r in rows}
    expected_energy=0.
    for pid,start,potential in [(7,0,1000.),(11,10,2000.)]:
        age=max(0.,time-start)
        fraction=(1-np.cos(np.pi*min(age/10,1)))/2
        assert by_id[pid]['released_energy_J']==pytest.approx(2*potential*fraction,abs=1e-10)
        assert by_id[pid]['active']==(time>=start)
        assert by_id[pid]['source_power_W']==pytest.approx(2*by_id[pid]['source_W_m3'])
        expected_energy+=2*potential*fraction
    assert sum(r['source_power_W'] for r in rows)==pytest.approx(state.hydration_source().sum()*2)
    if time==5:
        assert by_id[7]['released_J_m3']==pytest.approx(500.)
        assert by_id[7]['source_W_m3']==pytest.approx(50*np.pi)
        assert by_id[11]['age_s'] is None and by_id[11]['released_energy_J']==0
    if time==20:
        assert expected_energy==pytest.approx(6000.)
        assert state.hydration_source().sum()==0
    record_property('e07_audit_scientific',json.dumps(dict(case='hydration_budget',time_s=time,by_pour=rows)))


def test_figures_keep_world_coordinates_ids_all_curves_and_finite_horizon(tmp_path,monkeypatch):
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from mcoc_p2.e07.plots import create_figures
    solids=[solid(cube((30,-20,7),(32,-18,8)),7),solid(cube((30,-20,8),(32,-18,9)),11)]
    vox=voxelize(solids,.5)
    study=[voxelize(solids,h).report() for h in (.5,.25,.125)]
    events=[PourEvent(7,0,15,MAT,AdiabaticCurve(1000.,10.)),
            PourEvent(11,7200,25,MAT,AdiabaticCurve(2000.,20.))]
    timeline=[dict(time_s=0.,active_volume_m3=4.),dict(time_s=3600.,active_volume_m3=4.)]
    figures=[];close=plt.close
    def capture(fig=None):
        if isinstance(fig,Figure):figures.append(fig)
        close(fig)
    monkeypatch.setattr(plt,'close',capture)
    with warnings.catch_warnings():
        warnings.filterwarnings('error',message='Data has no positive values.*')
        paths=create_figures(vox,study,timeline,events,tmp_path)
    assert len(paths)==5 and all(Path(p).stat().st_size>1000 for p in paths)
    assert_allclose(figures[0].axes[0].get_xlim(),[30,32])
    assert_allclose(figures[0].axes[0].get_ylim(),[-20,-18])
    assert_allclose(figures[0].axes[0].get_zlim(),[7,9])
    image=figures[2].axes[0].images[0]
    rgba=image.cmap(image.norm(image.get_array()))
    assert len(np.unique(rgba.reshape(-1,4),axis=0))==2
    assert_allclose(figures[3].axes[0].get_xlim(),[0,1])
    assert len(figures[4].axes[0].lines)==len(figures[4].axes[1].lines)==2
    assert figures[4].axes[0].lines[0].get_ydata()[-1]==pytest.approx(15+1000/(2400*900))
    assert figures[4].axes[0].lines[1].get_ydata()[-1]==pytest.approx(25+2000/(2400*900))


def test_ifc_custom_ids_and_per_pour_parameters_reach_fields_and_summary(tmp_path):
    import ifcopenshell
    from ifcopenshell.api import pset
    ids=dict(zip(range(1,6),(7,11,23,41,59)))
    model=ifcopenshell.open(str(ROOT/'geometry/foundation.ifc'))
    for element in model.by_type('IfcFooting'):
        property_set=next(r.RelatingPropertyDefinition for r in element.IsDefinedBy
            if r.is_a('IfcRelDefinesByProperties') and r.RelatingPropertyDefinition.Name=='UANDES_HormigonMasivo')
        pset.edit_pset(model,pset=property_set,properties={'VertidaID':ids[int(element.Name[-2:])]})
    ifc=tmp_path/'ids.ifc';model.write(str(ifc))
    cfg=json.loads((ROOT/'configs/e07/demo.json').read_text(encoding='utf-8'))
    cfg.update(spacing_m=[.55,.55,.275],resolutions_m=[.55,.4,.275],t_end_s=3600.)
    for event in cfg['events']:event.update(pour_id=ids[event['pour_id']],activation_s=0.)
    cfg['events'][1].update(material={'cp':1000.},hydration={'H_vol_J_m3':20e6,'duration_s':7200.})
    cfg['events'][4]['hydration']={'H_vol_J_m3':0.}
    config=tmp_path/'config.json';config.write_text(json.dumps(cfg),encoding='utf-8')
    output=tmp_path/'resultado'
    proc=subprocess.run([sys.executable,'-X','utf8','-B',str(ROOT/'examples/run_e07.py'),
        '--ifc',str(ifc),'--config',str(config),'--output',str(output),'--no-plots'],
        capture_output=True,text=True,encoding='utf-8')
    assert proc.returncode==0,proc.stdout+proc.stderr
    report=json.loads((output/'summary.json').read_text(encoding='utf-8'))
    by_id={r['vertida_id']:r for r in report['hydration']['by_pour']}
    assert set(by_id)=={7,11,23,41,59} and all(report['checks'].values())
    assert by_id[11]['material']['cp']==1000 and by_id[11]['duration_s']==7200
    assert by_id[11]['released_J_m3']==pytest.approx(10e6)
    assert by_id[59]['released_energy_J']==by_id[59]['source_W_m3']==0
    assert sum(r['source_power_W'] for r in by_id.values())==pytest.approx(report['assembly']['source_power_W'])
    with np.load(output/'voxels.npz') as v,np.load(output/'construction.npz') as c:
        assert_allclose(c['hydration_source_W_m3'][v['vertida_id']==11],20e6*np.pi/14400)
        assert_allclose(c['capacity_J_K'][v['vertida_id']==11],2400*1000*np.prod(v['spacing_m']))
