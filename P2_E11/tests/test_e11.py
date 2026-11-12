"""E11: autenticidad trazable, interpolación, Robin, offline y VTK XYZ."""
from copy import deepcopy
import csv,hashlib,io,json,shutil
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
import pyvista as pv
import pytest
from mcoc_p2 import Material,Robin,Neumann
from mcoc_p2.e07.construction import PourEvent
from mcoc_p2.e07.coupling import MaskedAssembly
from mcoc_p2.e07.hydration import AdiabaticCurve
from mcoc_p2.e08.solver import simulate
from mcoc_p2.e10.weather import Snapshot,WeatherWindow,WeatherSample,utc_time
from mcoc_p2.e10 import weather as inherited_weather
from mcoc_p2.e11.weather import validate,normalized_bytes,window
from mcoc_p2.e11.pipeline import run,make_environment
from mcoc_p2.e11.vtkio import image_data,check_vtk
from mcoc_p2.e11.viewer import Viewer
from e07_helpers import labelled

ROOT=Path(__file__).resolve().parents[1]
def config():return json.loads((ROOT/'configs/e11/demo.json').read_text(encoding='utf-8'))


def test_real_snapshot_metadata_normalization_timezone_and_edges():
    c=config();s=validate(ROOT/c['snapshot'])
    rows=list(csv.DictReader(io.StringIO(normalized_bytes(s).decode())))
    assert len(rows)==len(s.seconds) and s.metadata['kind']=='forecast'
    assert s.metadata['provider_model_version'] is None  # proveedor no informó versión
    assert all(utc_time(row['time_utc'])==utc_time(row['time_America_Santiago']) for row in rows)
    assert all(float(row['temperature_C'])==value for row,value in zip(rows,s.air))
    start=utc_time(c['simulation_start_utc']).timestamp()
    w=window(ROOT/c['snapshot'],c['simulation_start_utc'],3600)
    assert w.at(0).air_C==s.sample(start).air_C and w.at(3600).air_C==s.sample(start+3600).air_C
    with pytest.raises(ValueError):w.at(-1)
    with pytest.raises(ValueError):w.at(3601)
    with pytest.raises(ValueError):window(ROOT/c['snapshot'],c['simulation_start_utc'],100*3600)


@pytest.mark.parametrize('mutation',['hash','csv','missing','duplicate','units','timezone'])
def test_corrupt_snapshot_is_rejected(tmp_path,mutation):
    source=ROOT/config()['snapshot'];folder=tmp_path/'snapshot';shutil.copytree(source,folder)
    if mutation=='hash':(folder/'weather.json').write_bytes((folder/'weather.json').read_bytes()+b' ')
    elif mutation=='csv':(folder/'temperature.csv').write_bytes(b'fake csv')
    else:
        data=json.loads((folder/'weather.json').read_bytes())
        if mutation=='missing':data['hourly']['temperature_2m'][1]=None
        if mutation=='duplicate':data['hourly']['time'][1]=data['hourly']['time'][0]
        if mutation=='units':data['hourly_units']['temperature_2m']='F'
        if mutation=='timezone':data['utc_offset_seconds']=-10800
        raw=json.dumps(data).encode();(folder/'weather.json').write_bytes(raw)
        meta=json.loads((folder/'metadata.json').read_bytes());meta['raw_sha256']=hashlib.sha256(raw).hexdigest();(folder/'metadata.json').write_text(json.dumps(meta),encoding='utf-8')
    with pytest.raises(ValueError):validate(folder)


def test_synthetic_linear_interpolation_is_analytic_and_not_extrapolated():
    # Diagnóstico unitario, nunca snapshot oficial.
    s=Snapshot({'kind':'synthetic'},(0,3600),(10.,30.),(0.,0.),(0.,0.))
    assert s.sample(900).air_C==15
    assert s.sample(1800).air_C==20
    assert s.sample(3600).air_C==30
    with pytest.raises(ValueError):s.sample(-.1)
    with pytest.raises(ValueError):s.sample(3600.1)


class Conditions:
    change_times_s=(1.3,)
    def __init__(self,temperature=20,variable=False):self.temperature=temperature;self.variable=variable;self.queries=[]
    def at(self,t):
        value=self.temperature+(t if self.variable else 0);self.queries.append((t,value))
        return WeatherSample(value,0.,0.,'synthetic')


def env(vox,conditions):
    c=config()['environment'];c=deepcopy(c);c['soil']['adiabatic']=True;c['formwork']['layers']=[];c['formwork']['remove_at_s']=0.
    return make_environment(vox,conditions,c)


def test_constant_boundary_matches_previous_robin_and_activation_changes_faces():
    vox=labelled([[[1,2]]]);mat=Material(2,2,5)
    events=[PourEvent(1,0,30,mat,AdiabaticCurve(0,1)),PourEvent(2,1.3,20,mat,AdiabaticCurve(0,1))]
    static={a+s:Robin(8,20) for a in 'xyz' for s in '-+'};static['z-']=Neumann()
    a=simulate(vox,events,static,t_end_s=3,max_step_s=.1,save_interval_s=.5)
    boundary=env(vox,Conditions())
    b=simulate(vox,events,t_end_s=3,max_step_s=.1,save_interval_s=.5,boundary_update=boundary,boundary_change_times_s=boundary.change_times_s)
    np.testing.assert_allclose(a.temperature_C,b.temperature_C,atol=2e-13,rtol=0,equal_nan=True)
    before=MaskedAssembly(vox,vox.vertida_id==1,{1:mat,2:mat});after=MaskedAssembly(vox,vox.occupation_mask,{1:mat,2:mat})
    assert np.any(before.faces.classification=='future_pour')
    assert not np.any(after.faces.classification=='future_pour')
    assert len(after.g)==1 and all(b.checks.values())


@pytest.mark.parametrize('ambient,sign',[(10,1),(50,-1)])
def test_boundary_flux_sign_and_energy_for_colder_or_hotter_air(ambient,sign):
    vox=labelled([[[1]]]);mat=Material(2,2,5);boundary=env(vox,Conditions(ambient))
    system=MaskedAssembly(vox,vox.occupation_mask,{1:mat});boundary(system,0)
    power,outward=system.power(np.full((1,1,1),30.))
    expected=5*8/(1+8*.5/2)*(30-ambient)  # base aislada; cinco caras
    assert outward==pytest.approx(expected) and sign*outward>0 and power.sum()==pytest.approx(-outward)
    r=simulate(vox,[PourEvent(1,0,30,mat,AdiabaticCurve(0,1))],t_end_s=1,max_step_s=.02,boundary_update=boundary)
    assert sign*r.energy['outward_J']>0 and all(r.checks.values())


def test_solver_queries_variable_weather_at_actual_step_starts():
    vox=labelled([[[1]]]);mat=Material(2,2400,900);conditions=Conditions(variable=True)
    boundary=env(vox,conditions)
    r=simulate(vox,[PourEvent(1,0,30,mat,AdiabaticCurve(0,1))],t_end_s=2,max_step_s=.4,save_interval_s=2,
               boundary_update=boundary,boundary_change_times_s=conditions.change_times_s)
    assert conditions.queries==[(step['start_s'],20+step['start_s']) for step in r.steps]
    assert 1.3 in [s['end_s'] for s in r.steps]
    assert len({v for _,v in conditions.queries})>1


def test_vtk_non_cubic_asymmetric_coordinates_fields_and_filters(tmp_path):
    idx=np.indices((2,3,4));ids=(idx[0]+2*idx[1]+idx[2])%6;active=(ids>0)&(idx[2]<3)
    T=20+idx[0]+10*idx[1]+100*idx[2];origin=np.array([10.,-2.,4.]);spacing=np.array([.7,1.2,.3])
    g=image_data(ids,origin,spacing,T,active);path=tmp_path/'test.vti';g.save(path)
    reread=pv.read(path);assert check_vtk(reread,ids,origin,spacing,T,active)['exact_temperature_equality']
    live=reread.threshold(.5,scalars='active');assert live.n_cells==active.sum()
    assert live.slice(normal='z',origin=(10.5,-1,4.4)).n_cells>0
    clipped=live.clip(normal='x',origin=(10.7,-1,4.4))
    assert clipped.n_cells>0 and clipped.bounds.x_max<=10.7+1e-12
    assert 0<clipped.volume<live.volume  # El filtro puede cambiar la topología y no el conteo.


@pytest.fixture(scope='module')
def real_run(tmp_path_factory):
    c=config();c['physics'].update(spacing_m=[.9,.9,.275],t_end_s=3*3600,max_step_s=600,save_interval_s=3600)
    for i,event in enumerate(c['physics']['events']):event['activation_s']=i*1800
    c['export_hours']=[0,1.5,3]
    out=tmp_path_factory.mktemp('e11')/'result'
    s=run(c,out,plots=False,vtk_dir=out/'vtk')
    return c,out,s


def test_real_ifc_weather_changes_thermal_field_balance_and_vtk(real_run):
    c,out,s=real_run
    assert all(all(v.values()) for v in s['checks'].values()) and s['same_time_steps']
    assert s['comparison']['final_field_Linf_C']>1e-6
    assert s['comparison']['outward_energy_difference_J']!=0
    assert len(s['activation_events'])==5 and all(s['energy'][n]['hydration_J']>0 for n in ('weather','constant'))
    with np.load(out/'fields.npz') as a:
        assert np.isfinite(a['weather_C']).all() and np.all(a['weather_C'][~a['active']]==0)
    assert s['vtk']['pvd_read_verified'] and len(s['vtk']['states'])>=3
    assert (ROOT/s['vtk']['collection']).resolve()==(out/'vtk/e11.pvd').resolve()


def test_offline_reproduction_is_exact(real_run,tmp_path,monkeypatch):
    import urllib.request
    def forbidden(*args,**kwargs):raise AssertionError('Intento de red en simulación offline')
    monkeypatch.setattr(urllib.request,'urlopen',forbidden);monkeypatch.setattr(inherited_weather,'urlopen',forbidden)
    c,out,s=real_run;again=tmp_path/'again';run(c,again,plots=False,export=False)
    with np.load(out/'fields.npz') as a,np.load(again/'fields.npz') as b:
        for key in a.files:np.testing.assert_array_equal(a[key],b[key])


def test_viewer_visibility_time_slice_clip_do_not_mutate_physics(real_run):
    _,out,_=real_run
    before=hashlib.sha256((out/'fields.npz').read_bytes()).hexdigest()
    v=Viewer(out/'vtk',out,off_screen=True)
    try:
        actors=len(v.plotter.actors);v.toggle(5);v.toggle(5);v.change(-1);v.change(1)
        assert len(v.plotter.actors)<=actors
        v.set_mode('slice');v.set_mode('clip')
        assert all(a['cells']>0 for a in v.actions if a['action'] in ('slice','clip'))
    finally:v.plotter.close()
    assert hashlib.sha256((out/'fields.npz').read_bytes()).hexdigest()==before
