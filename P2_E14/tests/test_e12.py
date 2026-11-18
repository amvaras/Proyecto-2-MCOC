"""Fuente auténtica, física E12, máximos globales y evidencia reproducible."""
from copy import deepcopy
import hashlib,json,re
from urllib.parse import unquote
from pathlib import Path
import numpy as np
import pytest
import pyvista as pv
from mcoc_p2 import Material
from mcoc_p2.e07.construction import PourEvent
from mcoc_p2.e07.coupling import MaskedAssembly
from mcoc_p2.e08.solver import simulate
from mcoc_p2.e11.pipeline import make_environment
from mcoc_p2.e11.weather import window
from mcoc_p2.e12.source import read_sources,load_curve,select_representative,ExperimentalCurve,NAMES,NOMINAL_MJ
from mcoc_p2.e12.metrics import surface_values,GlobalRecorder
from mcoc_p2.e12.pipeline import run,arrays
from e07_helpers import labelled

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/hydration/source_terms.txt'
def config():return json.loads((ROOT/'configs/e12/baseline.json').read_text(encoding='utf8'))

def test_original_eight_curves_hash_energy_nan_and_representative_selection():
    curves,report=read_sources(SOURCE)
    assert tuple(curves)==NAMES
    assert report['sha256']=='182b4a500dd02060b89dc452f007a379c7ab6cdc569e67de59a04c00d3497956'
    selected,scores=select_representative(curves);assert selected=='M2_SS' and scores[selected]==min(scores.values())
    for i,name in enumerate(NAMES):
        t,q=curves[name];assert abs(np.trapezoid(q,t)/1e6-NOMINAL_MJ[i])<=.06
        if name.endswith('22A'):assert t[-1]==163*3600 and report['curves'][name]['missing_tail']>0
        else:assert t[-1]==240.333*3600

@pytest.mark.parametrize('bad',['interior_nan','negative','energy','time'])
def test_source_corruption_rejected(tmp_path,bad):
    a=np.loadtxt(SOURCE)
    if bad=='interior_nan':a[20,5]=np.nan
    elif bad=='negative':a[20,1]=-1
    elif bad=='energy':a[:,2]*=2
    elif bad=='time':a[2,0]=a[1,0]
    p=tmp_path/'source_terms.txt'
    header='\n'.join(x for x in SOURCE.read_text(encoding='utf8').splitlines() if x.startswith('#'))
    np.savetxt(p,a,header=header,comments='')
    with pytest.raises(ValueError):read_sources(p)

def test_exact_piecewise_linear_integral_and_units_independent_triangle():
    curve=ExperimentalCurve([0,600,1200,86400],[0,2,0,0])
    assert curve.released(0,86400)==pytest.approx(1200)  # J/m³, no kg cemento ni rho cp.
    assert curve.released(0,300)==pytest.approx(150)
    assert curve.released(300,900)==pytest.approx(900)
    assert curve.source(300)==pytest.approx(1)
    assert curve.released(-100,0)==0 and curve.source(-1)==0
    assert curve.released(86400,336*3600)==0
    with pytest.raises(ValueError):curve.released(2,1)

def test_zero_tail_is_continuous_and_does_not_silently_replace_nan():
    curve,report=load_curve(SOURCE)
    assert curve.source(curve.duration_s)==curve.source(curve.duration_s+1)==0
    assert curve.released(curve.duration_s,336*3600)==0 and report['tail_additional_MJ_m3']==0
    with pytest.raises(ValueError):load_curve(SOURCE,'M1_SS',tail='zero')
    exp,_=load_curve(SOURCE,'M1_SS',tail='exponential',tau_s=86400)
    assert exp.source(exp.duration_s+1)==pytest.approx(exp.source_W_m3[-1]*np.exp(-1/86400))
    assert exp.released(exp.duration_s,exp.duration_s+86400)==pytest.approx(exp.source_W_m3[-1]*86400*(1-np.exp(-1)))

def test_336h_adiabatic_energy_matches_independent_rho_cp_relation():
    curve,_=load_curve(SOURCE);vox=labelled([[[1]]]);mat=Material(2,2400,900)
    result=simulate(vox,[PourEvent(1,0,18,mat,curve)],t_end_s=336*3600,max_step_s=7200,save_interval_s=24*3600)
    expected=18+95.715221706e6/(2400*900)
    assert result.temperature_C[-1,0]==pytest.approx(expected,abs=1e-11)
    assert result.times_s[-1]==336*3600 and all(result.checks.values())

def test_foundation_parameters_are_not_specimen_beta_or_capacity():
    c=config()
    assert c['environment']['air']['h_still_W_m2K']==8
    assert c['physics']['material']['rho']==2400 and c['physics']['material']['cp']==900
    assert c['experimental_source']['curve']=='M2_SS'

def test_weather_has_full_336h_coverage_and_rejects_beyond_dataset():
    c=config();w=window(ROOT/c['snapshot'],c['simulation_start_utc'],336*3600)
    assert w.coverage()['covered_hours']==336 and w.coverage()['tail_hours']==0
    assert w.snapshot.metadata['retrieved_at_utc'].startswith('2026-11-17')
    assert len(w.snapshot.seconds)==384 and w.at(336*3600).source_kind=='forecast'
    with pytest.raises(ValueError):window(ROOT/c['snapshot'],c['simulation_start_utc'],400*3600)

def test_S25_uses_all_exposed_faces_and_correct_half_cell_resistance():
    # Una celda a 30°C, ambiente20, h8, k2, Δ=1: q''=10/(.25+.125).
    vox=labelled([[[1]]]);mat=Material(2,2400,900)
    from mcoc_p2 import Robin
    assembly=MaskedAssembly(vox,vox.occupation_mask,{1:mat},{a+s:Robin(8,20) for a in 'xyz' for s in '-+'})
    face,near,cell,xyz,face_xyz,q=surface_values(assembly,np.full((1,1,1),30.),.025)
    np.testing.assert_allclose(q,10/.375,rtol=0,atol=1e-12)
    np.testing.assert_allclose(face,30-(10/.375)*.25,rtol=0,atol=1e-12)
    np.testing.assert_allclose(near,30-(10/.375)*(.5-.025)/2,rtol=0,atol=1e-12)
    np.testing.assert_allclose(np.linalg.norm(xyz-face_xyz,axis=1),.025,rtol=0,atol=1e-14)
    assert np.all(near>face) and np.all(near<cell)

def test_activation_restarts_age_and_records_both_sides_of_surface_change():
    vox=labelled([[[1,2]]]);mat=Material(2,2400,900);curve,_=load_curve(SOURCE)
    events=[PourEvent(1,0,20,mat,curve),PourEvent(2,600,25,mat,curve)]
    class Weather:
        change_times_s=()
        def at(self,t):
            from mcoc_p2.e10.weather import WeatherSample
            return WeatherSample(15,0,0,'synthetic')
    cfg=deepcopy(config()['environment']);cfg['formwork']['remove_at_s']=900
    env=make_environment(vox,Weather(),cfg);record=GlobalRecorder(vox,events,env,[.5,.5,.5],capture_all=True)
    result=simulate(vox,events,t_end_s=1200,max_step_s=300,save_interval_s=600,observer=record,boundary_update=env,boundary_change_times_s=env.change_times_s)
    t=record.arrays()['time_s'];assert np.nextafter(600.,-np.inf) in t and 600 in t
    before=record.fields[np.flatnonzero(t==np.nextafter(600.,-np.inf))[0]];after=record.fields[np.flatnonzero(t==600)[0]]
    assert before[1]==0 and after[1]==25
    assert np.nextafter(900.,-np.inf) in t and all(result.checks.values())

@pytest.fixture(scope='module')
def quick_run(tmp_path_factory):
    c=config();c['physics'].update(spacing_m=[.9,.9,.275],t_end_s=10800,max_step_s=600,save_interval_s=3600)
    for i,e in enumerate(c['physics']['events']):e['activation_s']=i*1800
    c['export_hours']=[0,1.5,3];out=tmp_path_factory.mktemp('e12')/'result'
    summary=run(c,out,plots=False,vtk_dir=out/'vtk')
    return c,out,summary

def test_real_IFC_experimental_heat_activation_mask_global_metrics_and_VTK(quick_run):
    c,out,s=quick_run;a=arrays(out/'all_steps.npz');g=arrays(out/'grid.npz')
    assert s['delivery']=='E12' and s['source']['selected']=='M2_SS'
    assert not s['complete_336h'] and s['deterministic_status'].startswith('NO VERIFICADO')
    assert np.isfinite(a['weather_C']).all() and np.all(a['weather_C'][~a['active']]==0)
    assert a['weather_C'][a['active']].max()==s['global_maximum']['temperature_C']
    assert s['global_delta25_maximum']['hot']['active'] and s['global_delta25_maximum']['cold']['classification'] in {'lateral','top','bottom','future_pour'}
    assert len(s['activation_events'])==5 and all(all(x.values()) for x in s['checks'].values())
    assert (out/'vtk/e12.pvd').is_file()
    for row in s['vtk']['states']:
        mesh=pv.read(out/'vtk'/row['file']);assert mesh.n_cells==g['vertida_id'].size

def test_E12_reproduction_exact_with_all_HTTP_prohibited(quick_run,tmp_path,monkeypatch):
    c,out,s=quick_run
    def forbid(*args,**kwargs):raise AssertionError('Red prohibida en simulación')
    monkeypatch.setattr('urllib.request.urlopen',forbid);monkeypatch.setattr('mcoc_p2.e10.weather.urlopen',forbid)
    target=tmp_path/'repeat';run(c,target,plots=False,export=False)
    for name in ['fields.npz','statistics.npz','all_steps.npz','weather_steps.npz','constant_steps.npz']:
        a,b=arrays(out/name),arrays(target/name);assert a.keys()==b.keys()
        for key in a:np.testing.assert_array_equal(a[key],b[key])

def test_E12_figure_generation_uses_actual_result(quick_run,tmp_path):
    from mcoc_p2.e12.plots import make_plots
    from PIL import Image
    _,out,_=quick_run;paths=make_plots(out,tmp_path/'figures',out/'vtk')
    assert len(paths)>=8
    for name in paths:
        with Image.open(ROOT/name) as im:im.verify()


def test_owned_cleanup_handles_OneDrive_readonly_and_protects_official_results():
    import importlib.util,os,stat,uuid
    spec=importlib.util.spec_from_file_location('cleanup_e12_test',ROOT/'scripts/clean_project.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    own=ROOT/'.runtime'/('pytest-cleanup-'+uuid.uuid4().hex);own.mkdir()
    (own/'.owned').write_text('pytest',encoding='utf8');(own/'nested').mkdir();(own/'nested/a.txt').write_text('propio',encoding='utf8')
    os.chmod(own/'nested',stat.S_IREAD)
    report=module.remove_owned_pytest_tree(ROOT,own)
    assert report['files']==2 and not own.exists()
    with pytest.raises(ValueError):module.remove_owned_pytest_tree(ROOT,ROOT/'results/e12')


def test_new_run_refuses_existing_artifact_folder_before_writing(tmp_path):
    folder=tmp_path/'artifacts';folder.mkdir();note=folder/'user_note.txt';note.write_text('conservar',encoding='utf8')
    destination=tmp_path/'new_result'
    with pytest.raises(ValueError,match='carpeta nueva'):run(config(),destination,plots=True,export=False,figure_dir=folder)
    assert note.read_text(encoding='utf8')=='conservar' and not destination.exists()

def test_official_dossier_word_budget_and_relative_figures():
    path=ROOT/'docs/E14_OPERACION.md'  # Cobertura documental vigente; física E12 intacta.
    text=path.read_text(encoding='utf8')
    assert len(re.findall(r'\S+',text))<=1400
    assert 'PENDIENTE DE PUBLICACIÓN' in text and '70' in text and '20' in text
    for raw in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text):
        if not raw.startswith(('https://','http://')):assert (path.parent/unquote(raw.split('#')[0])).is_file(),raw

