"""Duraciones, riesgo conjunto, fuentes auténticas, clima coherente y mismo integrador."""
from copy import deepcopy
from pathlib import Path
from dataclasses import replace
import json
import numpy as np
import pytest
from mcoc_p2 import Material
from mcoc_p2.e07.construction import PourEvent
from mcoc_p2.e07.coupling import MaskedAssembly
from mcoc_p2.e07.hydration import AdiabaticCurve
from mcoc_p2.e08.solver import simulate
from mcoc_p2.e13.plans import make_plan,validate_plan,thermal_config
from mcoc_p2.e13.risk import probability,weights,scenarios,select
from mcoc_p2.e13.weather import read,validate_snapshot,reduce_members
from mcoc_p2.e13.evaluator import Evaluator,validate_study
from e07_helpers import labelled
ROOT=Path(__file__).resolve().parents[1]
def test_joint_probability_is_OR_not_sum_or_product_and_exact_counts():
    rows=[dict(Tmax_C=50.,delta_C=10.,weight=1/24) for _ in range(24)]
    rows[0].update(Tmax_C=71,delta_C=21)
    a=probability(rows);assert a['P_joint']==pytest.approx(1/24) and a['P_T']==a['P_delta']==a['P_joint'] and a['feasible']
    rows[1]['delta_C']=21;b=probability(rows)
    assert b['P_joint']==pytest.approx(2/24) and b['P_T']==pytest.approx(1/24) and not b['feasible']
    rows[1]['delta_C']=20;rows[0].update(Tmax_C=70,delta_C=20);assert probability(rows)['P_joint']==0
@pytest.mark.parametrize('bad',[[.4,.4],[-.1,1.1],[np.nan,1],[],[np.inf]])
def test_invalid_weights_rejected(bad):
    with pytest.raises(ValueError):weights(bad)
def test_duration_includes_physical_placing_delays_and_resource_non_overlap():
    volumes=[100.,100.,100.,100.,100.];p=make_plan('p',volumes,50,wait_h=.5)
    assert p['D_h']==12 and sum(p['duration_h'])==10
    delayed=deepcopy(p);delayed['start_h']=[v+4 for v in p['start_h']];assert validate_plan(delayed,volumes)['D_h']==16
    bad=deepcopy(p);bad['start_h'][1]=.1
    with pytest.raises(ValueError):validate_plan(bad,volumes)
    bad=deepcopy(p);bad['duration_h'][0]=0
    with pytest.raises(ValueError):validate_plan(bad,volumes)
    one=make_plan('one',volumes,50,single=True);assert one['D_h']==10 and one['duration_h']==[10]
    one['initial_C'][1]+=1
    with pytest.raises(ValueError):validate_plan(one,volumes)
def test_single_pour_regions_equal_one_union_without_spurious_internal_Robin():
    vox=labelled([[[1,2],[1,2]],[[1,2],[1,2]]]);union=labelled(np.where(vox.vertida_id>0,1,0).tolist());mat=Material(2,2400,900);curve=AdiabaticCurve(1e6,3600)
    events=[PourEvent(i,0,20,mat,curve) for i in (1,2)]
    from mcoc_p2 import Robin
    b={a+s:Robin(8,15) for a in 'xyz' for s in '-+'}
    a=simulate(vox,events,b,t_end_s=7200,max_step_s=300,save_interval_s=900)
    c=simulate(union,[PourEvent(1,0,20,mat,curve)],b,t_end_s=7200,max_step_s=300,save_interval_s=900)
    np.testing.assert_array_equal(a.temperature_C,c.temperature_C)
    assembly=MaskedAssembly(vox,vox.occupation_mask,{i:mat for i in (1,2)},b)
    assert len(assembly.faces.areas)==24 and 'future_pour' not in assembly.faces.classification
def test_authentic_ensemble_medoid_weights_and_member_derivation():
    r=read(ROOT/'data/ensemble/reduction.json');sc=scenarios(r)
    assert len(sc)==24 and len({x['id'] for x in sc})==24 and sum(x['weight'] for x in sc)==pytest.approx(1)
    assert r['counts']==[15,12,4] and r['medoids']==[0,13,17]
    assert sum(x['weight'] for x in sc if x['campaign']=='SS')==pytest.approx(.8)
    for p in r['snapshots']:
        snap=validate_snapshot(ROOT/p);assert len(snap.seconds)==818 and np.isfinite(snap.air).all()
    bad=deepcopy(r);bad['medoids'][1]=bad['medoids'][0]
    with pytest.raises(ValueError):scenarios(bad)
    small=reduce_members([[0,1],[1,2],[2,3],[10,11]],3)
    assert sum(small['counts'])==4 and len(set(small['medoids']))==3
def test_selection_uses_duration_and_same_joint_risk_without_favoring_prior_candidate():
    plans=[dict(id='slow',D_h=20),dict(id='fast',D_h=10)]
    rows=[dict(plan=p['id'],Tmax_C=60,delta_C=19,weight=1) for p in plans]
    table,best=select(plans,rows);assert best['plan']=='fast'
    rows[1]['Tmax_C']=71;assert select(plans,rows)[1]['plan']=='slow'
    rows[0]['delta_C']=21;assert select(plans,rows)[1] is None
def test_eight_tail_models_preserve_real_records_and_add_only_declared_energy():
    from mcoc_p2.e12.source import load_curve,NAMES
    for name in NAMES:
        curve,report=load_curve(ROOT/'data/hydration/source_terms.txt',name,tail='exponential',tau_s=86400)
        assert curve.source(curve.duration_s+1)==pytest.approx(curve.source_W_m3[-1]*np.exp(-1/86400))
        assert curve.released(curve.duration_s,curve.duration_s+86400)==pytest.approx(curve.tail_potential_J_m3*(1-np.exp(-1)))
        assert curve.tail_potential_J_m3>=0 and report['curves'][name]['integrated_MJ_m3']>60
def test_real_E13_case_age_coverage_energy_horizon_and_no_network(monkeypatch):
    e=Evaluator();c=read(ROOT/'configs/e13/study.json');s=scenarios(read(ROOT/'data/ensemble/reduction.json'))[3]
    p=c['plans'][2];s=deepcopy(s)
    def forbid(*args,**kwargs):raise AssertionError('Red prohibida')
    monkeypatch.setattr('urllib.request.urlopen',forbid)
    a,x,record,solution=e.case(p,s,spacing=[.9,.9,.275],horizon_h=24,max_step_s=900)
    assert all(a['checks'].values()) and a['energy']['hydration_J']>0 and a['coverage']['tail_hours']==0
    assert a['first336_Tmax_C']==a['Tmax_C'] and a['D_h']==p['D_h']
    assert np.isfinite(x['Tmax_C']).all() and np.ptp(x['Tmax_C'])>1
    assert len(solution.events)==5 and all(r['time_s']>=0 for r in solution.events)
    assert all(row['active_ids']!=[] for row in solution.metrics)
    future=deepcopy(p);future['start_h']=[v+1 for v in p['start_h']]
    a,_,_,solution=e.case(future,s,spacing=[.9,.9,.275],horizon_h=4,max_step_s=900)
    assert solution.events[0]['time_s']==3600 and solution.metrics[0]['active_cells']==0
