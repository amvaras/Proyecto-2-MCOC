import numpy as np
import pytest
from mcoc_p2 import Material,CartesianGrid,CartesianSystem,Robin,Neumann
from mcoc_p2.e07.faces import exposed_faces,contacts
from mcoc_p2.e07.hydration import AdiabaticCurve,HydrationContext,q_dot_h
from mcoc_p2.e07.construction import PourEvent,ConstructionState
from mcoc_p2.e07.coupling import MaskedAssembly
from e07_helpers import labelled

MAT=Material(2.,2400.,900.)


def example(events_at=(0.,10.)):
    vox=labelled([[[1,2]]]);events=[PourEvent(i,t,18.+i,MAT,AdiabaticCurve()) for i,t in zip((1,2),events_at)]
    return vox,ConstructionState(vox,events)


def test_single_cell_exterior_area_normals_and_anisotropy():
    vox=labelled([[[1]]],(2.,3.,4.));faces=exposed_faces(vox)
    assert len(faces.areas)==6 and faces.areas.sum()==pytest.approx(52)
    np.testing.assert_allclose((faces.normals*faces.areas[:,None]).sum(axis=0),0)
    assert faces.report()['area_by_orientation_m2']['x+']==12


def test_internal_same_pour_face_is_neither_exterior_nor_interface():
    vox=labelled([[[1,1]]]);assert len(exposed_faces(vox).areas)==10
    assert len(contacts(vox)['area_m2'])==0 and len(contacts(vox,different_only=False)['area_m2'])==1


def test_two_active_pours_have_one_internal_interface_no_robin():
    vox=labelled([[[1,2]]]);assert len(exposed_faces(vox).areas)==10
    edges=contacts(vox);assert len(edges['area_m2'])==1
    np.testing.assert_array_equal(edges['pour_ids'],[[1,2]])


def test_future_pour_becomes_exposed_then_internal():
    vox,state=example();before=exposed_faces(vox,state.active_mask())
    assert len(before.areas)==6 and before.report()['count_by_class']['future_pour']==1
    assert len(contacts(vox,state.active_mask())['area_m2'])==0
    state.advance_to(10.)
    assert 'future_pour' not in exposed_faces(vox,state.active_mask()).report()['count_by_class']
    assert len(contacts(vox,state.active_mask())['area_m2'])==1


def test_zero_later_events_initialization_age_and_no_double_application():
    vox,state=example();assert state.applied=={1};assert np.isnan(state.temperature_C[0,0,1])
    assert state.pour_age(9,2) is None and state.pour_age(10,2)==0
    state.temperature_C[0,0,0]=35.;state.advance_to(10.)
    np.testing.assert_allclose(state.temperature_C,[[[35.,20.]]])
    state.temperature_C[0,0,1]=42.;assert state.advance_to(10.)==[]
    assert state.temperature_C[0,0,1]==42 and state.pour_age(15,2)==5


def test_timeline_hits_events_exactly_without_large_steps():
    _,state=example((0.,10.3));times=state.time_grid(30.,7.)
    assert 10.3 in times and times[0]==0 and times[-1]==30
    assert np.diff(times).max()<=7+1e-12
    for t in times:state.advance_to(t)
    assert state.applied=={1,2}


def test_jumping_an_event_is_rejected():
    _,state=example()
    with pytest.raises(ValueError,match='saltar'):state.advance_to(11)


def test_simultaneous_events_activate_together_and_remain_distinct():
    _,state=example((0.,0.));assert state.applied=={1,2}
    np.testing.assert_allclose(state.temperature_C,[[[19.,20.]]])


@pytest.mark.parametrize('fault',['duplicate','missing','negative','temperature'])
def test_invalid_schedule(fault):
    vox,_=example()
    with pytest.raises(ValueError):
        if fault=='duplicate':ConstructionState(vox,[PourEvent(1,0,20,MAT,AdiabaticCurve())]*2)
        elif fault=='missing':ConstructionState(vox,[])
        elif fault=='negative':PourEvent(1,-1,20,MAT,AdiabaticCurve())
        else:PourEvent(1,0,-300,MAT,AdiabaticCurve())


def test_hydration_degree_bounds_source_units_and_exhaustion():
    curve=AdiabaticCurve(1000.,100.)
    np.testing.assert_allclose(curve.degree([-1,0,50,100,1000]),[0,0,.5,1,1],atol=1e-15)
    assert curve.source(50)==pytest.approx(1000*np.pi/200)
    np.testing.assert_array_equal(curve.source([-1,0,100,1000]),0)


def test_hydration_potential_conserved_for_arbitrary_steps():
    curve=AdiabaticCurve();times=np.array([-3,0,1,10000,20000,172799,172800,2e6])
    releases=curve.released(times[:-1],times[1:])
    assert releases.min()>=0 and releases.sum()==pytest.approx(curve.H_vol_J_m3,rel=1e-15)
    t=np.linspace(0,curve.duration_s,10001)
    assert np.trapezoid(curve.source(t),t)==pytest.approx(curve.H_vol_J_m3,rel=1e-7)


def test_adiabatic_curve_derivative_matches_volumetric_source():
    curve=AdiabaticCurve();age=40000.;epsilon=1.
    derivative=(curve.adiabatic_temperature(age+epsilon,MAT)-curve.adiabatic_temperature(age-epsilon,MAT))/(2*epsilon)
    assert MAT.rho*MAT.cp*derivative==pytest.approx(curve.source(age),rel=1e-8)
    assert curve.adiabatic_temperature(curve.duration_s,MAT)==pytest.approx(50.)


def test_prescribed_curve_is_explicitly_temperature_independent():
    context=HydrationContext(AdiabaticCurve(),10.)
    assert q_dot_h(20000,10.,MAT,context)==q_dot_h(20000,70.,MAT,context)
    assert q_dot_h(9,20.,MAT,context)==0
    with pytest.raises(ValueError):q_dot_h(100,-273.15,MAT,context)


def test_new_pour_age_and_source_reset_independently():
    _,state=example();state.advance_to(10)
    source=state.hydration_source();assert source[0,0,0]>0 and source[0,0,1]==0


def test_masked_assembly_excludes_inactive_capacity_and_exchange():
    vox,state=example();system=MaskedAssembly(vox,state.active_mask(),{1:MAT,2:MAT})
    assert system.capacity[0,0,1]==0 and system.capacity.sum()==MAT.rho*MAT.cp
    power,out=system.power(state.temperature_C);np.testing.assert_array_equal(power,0);assert out==0
    assert len(system.g)==0


def test_perfect_contact_opposite_exchange_heterogeneous_conductivity():
    vox=labelled([[[1,2]]],(.2,.3,.4));a=Material(2,2400,900);b=Material(4,2200,800)
    system=MaskedAssembly(vox,vox.occupation_mask,{1:a,2:b});power,out=system.power(np.array([[[10.,30.]]]))
    g=.2*.3/(.4/(2*a.k)+.4/(2*b.k))
    assert system.g[0]==pytest.approx(g);assert power[0,0,0]==pytest.approx(g*20)
    assert power.sum()==pytest.approx(0,abs=1e-14) and out==0


@pytest.mark.parametrize('boundary',[Neumann(),Robin(12.,20.)])
def test_full_mask_power_and_stability_match_verified_box_solver(boundary):
    vox=labelled(np.ones((3,4,5)),(.2,.3,.4));grid=CartesianGrid((.6,1.2,2.),(3,4,5))
    bc={a+s:boundary for a in 'xyz' for s in '-+'}
    masked=MaskedAssembly(vox,vox.occupation_mask,{1:MAT},bc);box=CartesianSystem(grid,MAT,bc)
    t=np.random.default_rng(29).uniform(10,50,grid.shape);source=1250.
    power,out=masked.power(t,source)
    np.testing.assert_allclose(power,box.power(t,source),rtol=1e-13,atol=1e-10)
    assert masked.stable_dt==pytest.approx(box.stable_dt,rel=1e-14)
    assert masked.energy(t)==pytest.approx(box.energy(t),rel=1e-14)


def test_future_face_robin_heat_loss_without_fictitious_future_material():
    vox,state=example();system=MaskedAssembly(vox,state.active_mask(),{1:MAT,2:MAT},{'z+':Robin(10,0)})
    power,out=system.power(state.temperature_C)
    expected=19/(.5/2+1/10)
    assert out==pytest.approx(expected) and power.sum()==pytest.approx(-expected)
    assert system.capacity[0,0,1]==0
