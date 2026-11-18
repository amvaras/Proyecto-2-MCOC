"""Referencias independientes del transiente: fuente, masa entrante y convección."""
import numpy as np
import pytest
from numpy.testing import assert_allclose
from mcoc_p2 import Material, Robin
from mcoc_p2.e07.construction import PourEvent
from mcoc_p2.e07.hydration import AdiabaticCurve
from mcoc_p2.e08.solver import simulate
from e07_helpers import labelled


@pytest.mark.parametrize('step',[3.,47.,1000.])
def test_delayed_disconnected_pours_follow_adiabatic_curve_for_any_time_step(step):
    vox=labelled([[[1,0,2]]]);mat=Material(1.,2.,5.)
    events=[PourEvent(1,0,20,mat,AdiabaticCurve(20.,100.)),PourEvent(2,37.5,30,mat,AdiabaticCurve(40.,100.))]
    result=simulate(vox,events,t_end_s=240,max_step_s=step,save_interval_s=20)
    assert 37.5 in result.times_s and all(result.checks.values())
    first=20+(1-np.cos(np.pi*np.clip(result.times_s/100,0,1)))
    assert_allclose(result.temperature_C[:,0],first,atol=2e-13,rtol=0)
    active=result.times_s>=37.5
    second=30+2*(1-np.cos(np.pi*np.clip((result.times_s[active]-37.5)/100,0,1)))
    assert np.isnan(result.temperature_C[~active,1]).all()
    assert_allclose(result.temperature_C[active,1],second,atol=2e-13,rtol=0)
    assert result.energy['hydration_J']==pytest.approx(60)
    assert result.energy['placement_after_zero_J']==pytest.approx(300)
    assert result.energy['final_J']==pytest.approx(560)
    at=np.where(result.times_s==37.5)[0][0]
    assert result.temperature_C[at,1]==30


def test_two_cell_diffusion_matches_discrete_exact_mode_after_activation():
    vox=labelled([[[1,2]]]);mat=Material(1.,1.,1.);curve=AdiabaticCurve(0.,1.)
    events=[PourEvent(1,0,20,mat,curve),PourEvent(2,10,10,mat,curve)]
    result=simulate(vox,events,t_end_s=12,max_step_s=.25,save_interval_s=2)
    at=np.where(result.times_s==10)[0][0]
    assert_allclose(result.temperature_C[at],[20.,10.],rtol=0,atol=0)
    # C=1, G=1: the difference multiplies by 1-2*dt in each of 8 steps.
    assert_allclose(result.temperature_C[-1],[15+5*.5**8,15-5*.5**8],atol=1e-13)
    assert result.energy['hydration_J']==result.energy['outward_J']==0
    assert result.energy['placement_after_zero_J']==10
    assert result.energy['residual_J']==pytest.approx(0,abs=1e-12)


def test_robin_single_voxel_has_first_order_temporal_convergence_and_balance():
    vox=labelled([[[1]]]);mat=Material(2.,2400.,900.)
    event=PourEvent(1,0,50.,mat,AdiabaticCurve(0.,1.))
    bc={a+s:Robin(12.,20.) for a in 'xyz' for s in '-+'}
    # 6 faces: each G=1/(0.5/k+1/h), capacity=rho*cp.
    rate=6/(.5/2+1/12)/(2400*900)
    exact=20+30*np.exp(-rate*10000)
    errors=[]
    for step in (400.,200.,100.):
        r=simulate(vox,[event],bc,t_end_s=10000,max_step_s=step,save_interval_s=10000)
        errors.append(abs(r.temperature_C[-1,0]-exact))
        assert r.energy['outward_J']>0 and all(r.checks.values())
        assert abs(r.energy['residual_J'])<1e-6
    assert all(1.95<a/b<2.05 for a,b in zip(errors,errors[1:]))


def test_future_activation_changes_stability_without_reinitializing_old_pour():
    vox=labelled([[[1,2]]]);a=Material(1.,1.,1.);b=Material(100.,1.,1.)
    events=[PourEvent(1,0,20,a,AdiabaticCurve(0.,1.)),PourEvent(2,10,80,b,AdiabaticCurve(0.,1.))]
    r=simulate(vox,events,t_end_s=13,max_step_s=100,save_interval_s=10,safety=.7)
    assert r.steps[0]['stable_dt_s'] is None
    later=[s for s in r.steps if s['start_s']>=10]
    assert later and all(s['stable_dt_s'] is not None and s['dt_over_limit']<=.7+1e-13 for s in later)
    assert_allclose(r.temperature_C[1],[20.,80.])
    assert r.temperature_C[-1].min()>=20 and r.temperature_C[-1].max()<=80


def test_simultaneous_start_and_zero_horizon_are_valid():
    vox=labelled([[[7,11]]]);mat=Material(2.,2400.,900.)
    events=[PourEvent(7,0,18,mat,AdiabaticCurve()),PourEvent(11,0,23,mat,AdiabaticCurve())]
    r=simulate(vox,events,t_end_s=0)
    assert_allclose(r.temperature_C,[[18,23]])
    assert r.events[0]['vertida_ids']==[7,11] and not r.steps
    assert all(r.checks.values())


@pytest.mark.parametrize('kwargs',[{'max_step_s':0},{'safety':1.1},{'save_interval_s':0},{'t_end_s':-1}])
def test_invalid_time_controls_rejected(kwargs):
    arguments=dict(t_end_s=1);arguments.update(kwargs)
    with pytest.raises(ValueError):
        simulate(labelled([[[1]]]),[PourEvent(1,0,20,Material(1,1,1),AdiabaticCurve())],**arguments)
