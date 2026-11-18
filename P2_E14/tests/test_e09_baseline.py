"""Verificación E09 adicional; referencias independientes y artefactos reales."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import numpy as np
import pytest
from PIL import Image
from numpy.testing import assert_allclose
from mcoc_p2 import Material,Robin
from mcoc_p2.e07.construction import PourEvent
from mcoc_p2.e07.hydration import AdiabaticCurve
from mcoc_p2.e08.solver import simulate
from mcoc_p2.e09.analysis import FieldRecorder,select_probes,probe_values
from mcoc_p2.e09.pipeline import run_baseline,stage_balances
from mcoc_p2.e09.plots import generate_figures,load_result,cut_payload
from e07_helpers import labelled

ROOT=Path(__file__).resolve().parents[1]


def event(pid=1,t=0,T=20,H=0,material=None):
    return PourEvent(pid,t,T,material or Material(1.,2.,5.),AdiabaticCurve(H,5.))


def test_observer_receives_readonly_fields_and_does_not_change_solution():
    vox=labelled([[[1,2,0]]]);events=[event(1,T=35),event(2,t=1.3,T=15)]
    seen=[]
    def observe(t,temperature,active):
        with pytest.raises(ValueError):temperature[0,0,0]=99
        with pytest.raises(ValueError):active[0,0,0]=False
        seen.append(t)
    a=simulate(vox,events,t_end_s=3,max_step_s=.1,save_interval_s=.5)
    b=simulate(vox,events,t_end_s=3,max_step_s=.1,save_interval_s=.5,observer=observe)
    assert_allclose(a.temperature_C,b.temperature_C,rtol=0,atol=0,equal_nan=True)
    assert a.steps==b.steps and len(seen)==len(b.steps)+1 and 1.3 in seen


def test_adiabatic_masked_recorder_uses_active_cells_only_and_preserves_energy():
    vox=labelled([[[1,0],[1,0]],[[1,0],[1,0]]])
    bc={a+s:Robin(0,20) for a in 'xyz' for s in '-+'}
    rec=FieldRecorder(vox,[event(T=35)],bc)
    r=simulate(vox,[event(T=35)],bc,t_end_s=3,max_step_s=.3,observer=rec)
    a=rec.arrays();assert_allclose(a['Tmax_C'],35);assert_allclose(a['Tmin_C'],35);assert_allclose(a['Tmean_C'],35)
    assert r.energy['residual_J']==pytest.approx(0,abs=1e-12) and all(a['active_count']==4)


class LinearBenchmark(AdiabaticCurve):
    """Fuente uniforme sintética para referencia, no modelo de hormigón."""
    def degree(self,age_s):return np.clip(np.asarray(age_s)/self.duration_s,0,1)
    def source(self,age_s):
        age=np.asarray(age_s);return np.where((age>=0)&(age<self.duration_s),self.H_vol_J_m3/self.duration_s,0.)


def test_uniform_source_in_masked_disconnected_pours_has_analytic_temperature():
    vox=labelled([[[1,0,2]]]);mat=Material(1,2,5);curve=LinearBenchmark(25.,5.)
    events=[PourEvent(1,0,20,mat,curve),PourEvent(2,1.5,27,mat,curve)]
    r=simulate(vox,events,t_end_s=4,max_step_s=.4,save_interval_s=.5)
    assert_allclose(r.temperature_C[:,0],20+.5*r.times_s,rtol=0,atol=2e-13)
    live=r.times_s>=1.5;assert np.isnan(r.temperature_C[~live,1]).all()
    assert_allclose(r.temperature_C[live,1],27+.5*(r.times_s[live]-1.5),rtol=0,atol=2e-13)
    assert r.energy['hydration_J']==pytest.approx(5*(4+2.5))


def test_robin_probe_is_face_temperature_not_cell_center():
    vox=labelled([[[1]]]);probes=select_probes(vox,(.5,.5,.5))
    t=np.array([[[40.]]]);active=np.ones((1,1,1),dtype=bool)
    bc={a+s:Robin(10.,20.) for a in 'xyz' for s in '-+'}
    values,valid=probe_values(t,active,probes,{1:Material(2,2,5)},bc)
    assert valid.all() and values[0]==40
    assert values[1]==pytest.approx(20+20/(1+10*.5/2))
    assert 20<values[1]<40
    assert_allclose(values[[1,2]],values[1])
    values,valid=probe_values(t,np.zeros_like(active),probes,{1:Material(2,2,5)},bc)
    assert not valid.any() and not values.any()


def test_stage_balance_keeps_zero_reference_placement_event():
    vox=labelled([[[1,2]]]);events=[event(1,T=30),event(2,t=1,T=20)]
    r=simulate(vox,events,t_end_s=3,max_step_s=.2,energy_reference_C=20)
    stages=stage_balances(r)
    assert len(stages)==2 and stages[0]['end_h']==1/3600
    assert sum(s['placement_J'] for s in stages)==0
    assert abs(sum(s['balance_residual_J'] for s in stages))<1e-10


def test_heating_and_cooling_respond_to_h_heat_and_placement_separately():
    vox=labelled([[[1]]]);mat=Material(1,2,5)
    def run(h=0,H=20,T=30):
        bc={a+s:Robin(h,20) for a in 'xyz' for s in '-+'}
        return simulate(vox,[event(T=T,H=H,material=mat)],bc,t_end_s=2,max_step_s=.05).temperature_C[-1,0]
    assert run(h=5)<run()
    assert run(H=40)>run()
    assert run(T=35)>run()
    assert run(H=0)==pytest.approx(30)


@pytest.fixture(scope='module')
def real_result(tmp_path_factory):
    out=tmp_path_factory.mktemp('e09')/'case'
    cfg=json.loads((ROOT/'configs/e09/baseline.json').read_text(encoding='utf-8'))
    p=cfg['physics'];p.update(spacing_m=[.9,.9,.275],resolutions_m=[.55,.4,.275],t_end_s=7200.,max_step_s=120.,save_interval_s=1800.)
    p['hydration']['duration_s']=3600.
    for i,e in enumerate(p['events']):e['activation_s']=i*720.
    cfg['analysis'].update(panel_hours=[0,.5,1,2],animation=True)
    report=run_baseline(ROOT/'geometry/foundation.ifc',cfg,out,plots=False)
    return out,report


def test_real_baseline_stores_finite_fields_masks_and_exact_events(real_result):
    out,s=real_result
    assert all(s['checks'].values()) and s['control_no_hydration']['peak_C']==pytest.approx(22)
    assert s['thermal']['peak']['temperature_C']>40
    with np.load(out/'temperature.npz') as z,np.load(out/'grid.npz') as g:
        assert np.isfinite(z['temperature_C']).all() and not z['temperature_C'][~z['active_mask']].any()
        ids=g['vertida_id'][g['occupation_mask']]
        for i,event in enumerate(s['configuration']['physics']['events']):
            frame=int(np.flatnonzero(z['times_s']==event['activation_s'])[0]);new=ids==event['pour_id']
            assert_allclose(z['temperature_C'][frame,new],event['initial_C'],atol=0,rtol=0)
            assert not z['active_mask'][:frame,new].any()
        assert not np.array_equal(z['temperature_C'][0],z['temperature_C'][-1])
        capacity=np.zeros_like(ids,dtype=float)
        for e in s['configuration']['physics']['events']:
            m=s['configuration']['physics']['material'];capacity[ids==e['pour_id']]=m['rho']*m['cp']*np.prod(g['spacing_m'])
        energy=np.sum(capacity[z['active_mask'][-1]]*(z['temperature_C'][-1,z['active_mask'][-1]]-20))
        assert energy==pytest.approx(s['energy']['final_J'],abs=1e-5)
    with np.load(out/'steps.npz') as z:
        assert all(np.isfinite(z[k]).all() for k in z.files)
        assert np.all(z['dt_over_limit']<=.8*(1+1e-12))
        assert abs(z['hydration_energy_J'].sum()-s['energy']['hydration_J'])<1e-5
    assert all(abs(r['balance_residual_J'])<=s['energy']['tolerance_J'] for r in s['stages'])


def test_peak_and_probes_are_recorded_each_integration_step(real_result):
    out,s=real_result
    with np.load(out/'statistics.npz') as z:
        assert len(z['time_s'])==s['temporal']['integration_steps']+1
        peak=np.argmax(z['Tmax_C'])
        assert z['Tmax_C'][peak]==s['thermal']['peak']['temperature_C']
        assert z['time_s'][peak]/3600==s['thermal']['peak']['time_h']
        assert np.all(np.diff(z['time_s'])>0)
        valid=z['probe_valid'][:,0]&z['probe_valid'][:,1]
        expected=np.max((z['probe_temperature_C'][:,0]-z['probe_temperature_C'][:,1])[valid])
        assert expected==s['thermal']['center_top_difference']['maximum_C']


def test_spatial_figures_and_gif_preserve_field_and_match_raw_arrays(real_result):
    out,s=real_result;before=hashlib.sha256((out/'temperature.npz').read_bytes()).hexdigest()
    figdir=out/'figures'
    report=generate_figures(out,figdir,animation=True,azim=-40)
    assert hashlib.sha256((out/'temperature.npz').read_bytes()).hexdigest()==before==report['field_sha256']
    _,g,d,_,_=load_result(out)
    frame=len(d['times_s'])-1;p=cut_payload(g,d,frame,'vertical')
    j=int(np.argmin(abs(g['y_m'])));shape=g['vertida_id'].shape
    independent=np.zeros(np.prod(shape));independent[g['occupied_flat_indices']]=d['temperature_C'][frame]
    assert_allclose(p['values'],independent.reshape(shape)[:,j,:].T,rtol=0,atol=0)
    manifest=json.loads((out/'figure_manifest.json').read_text(encoding='utf-8'))
    assert manifest['field_sha256']==before
    for name in report['files']:
        with Image.open(figdir/name) as image:
            assert image.width>100 and image.height>100
            if name.endswith('.png'):assert before in image.info['Description']
    with Image.open(figdir/'e09_evolucion.gif') as image:assert image.n_frames>1
    assert 'e09_evolucion_espacial.png' in report['files']
    assert (out/'temperature.npz').read_bytes() and hashlib.sha256((out/'temperature.npz').read_bytes()).hexdigest()==before
