"""Physical invariants and traceable comparison against the experimental run."""
import hashlib
import math

import numpy as np
import pytest

from mcoc_p2.diffusion_1d import Material
from mcoc_p2.e07.coupling import MaskedAssembly
from mcoc_p2.e08.solver import simulate
from mcoc_p2.e14.model import Model, catalog
from mcoc_p2.e14.io import ROOT, read
from mcoc_p2.e14.statistics import limit_states
from mcoc_p2.f02.pipes import Design, Network
from mcoc_p2.f02.study import InternalExchange, configuration

@pytest.fixture(scope='module')
def assembly_and_grid():
    model=Model()
    vox=model.engine.grid((.45,.45,.11))
    assembly=MaskedAssembly(vox,vox.occupation_mask,{i:Material(k=2.,rho=2400.,cp=900.) for i in range(1,6)})
    return assembly,vox,model.engine.solids

def test_heat_exchange_analytic_balance_capacity_and_bypass(assembly_and_grid):
    assembly,vox,solids=assembly_and_grid
    cfg=configuration()['pipe']
    network=Network(vox,solids,Design(**cfg))
    t=36*3600
    assert network.limit(assembly,t)<=assembly.stable_dt
    assert len(network.circuits)==29
    assert network.mass_flow==pytest.approx(.2495)
    assert network.r_per_m==pytest.approx(.25212,abs=1e-5)
    fields=np.where(vox.occupation_mask,40.,np.nan)
    net=np.zeros(fields.shape)
    q=network.apply(net,fields,t)
    expected=math.fsum(network.mass_cp*20*(-math.expm1(-c['length_m']/network.r_per_m/network.mass_cp))
                       for c in network.circuits)
    assert q==pytest.approx(expected,abs=1e-8)
    assert net.sum()==pytest.approx(-q,abs=1e-8)
    assert network.max_flow_ls==pytest.approx(7.25)
    for hours in (17,552,744):
        assert network.limit(assembly,3600*hours)==assembly.stable_dt
        assert network.apply(net,fields,3600*hours)==0
    network.limit(assembly,t)
    cold=np.where(vox.occupation_mask,17.,np.nan)
    before=net.copy()
    assert network.apply(net,cold,t)==0 and np.array_equal(before,net)
    capped=Network(vox,solids,Design(**{**cfg,'cap_kW':1}))
    capped.limit(assembly,t)
    net.fill(0)
    assert capped.apply(net,fields,t)==pytest.approx(1000.,abs=1e-8)
    assert net.sum()==pytest.approx(-1000.,abs=1e-8)

def test_off_window_reproduces_original_solver():
    from mcoc_p2.e08.inputs import events_from_config
    from mcoc_p2.e11.pipeline import make_environment
    from mcoc_p2.e11.weather import window
    model=Model()
    cfg,_=model.configuration(
        read(ROOT/'configs/e14/study.json')['plans'][0],catalog()[0],spacing=(1.2,1.2,.275))
    p=cfg['physics']
    vox=model.engine.grid(tuple(p['spacing_m']))
    events=events_from_config(p)
    weather=window(ROOT/cfg['snapshot'],cfg['simulation_start_utc'],p['t_end_s'])
    def solve(use_exchange):
        env=make_environment(vox,weather,cfg['environment'])
        boundary=InternalExchange(env,Network(vox,model.engine.solids,
            Design(**{**configuration()['pipe'],'layers':((3,1.42),),'radius':2.}))) if use_exchange else env
        result=simulate(vox,events,t_end_s=3600,max_step_s=900,boundary_update=boundary,
                        boundary_change_times_s=boundary.change_times_s)
        if use_exchange:assert boundary.close_ledger(result)==0
        return result
    a,b=solve(False),solve(True)
    np.testing.assert_array_equal(a.temperature_C,b.temperature_C)
    assert a.steps==b.steps and a.energy==b.energy

def test_saved_scenarios_metrics_or_and_reference():
    folder=ROOT/'results/f02'
    data=read(folder/'enumeration.json')
    controls=read(folder/'controls.json')
    weights={s['id']:s['weight'] for s in catalog()}
    assert len(data['rows'])==24 and {r['scenario']:r['weight'] for r in data['rows']}==weights
    assert data['kernel_sha256']==controls['kernel_sha256']
    assert hashlib.sha256((folder/'fields.npz').read_bytes()).hexdigest()==data['fields_sha256']
    expected=read(ROOT/'configs/f02/experimental_reference.json')
    for r in data['rows']:
        assert all(r['checks'].values()) and r['coverage']['covered_hours']==744
        assert r['energy']['cooling_J']>0
        assert r['Tmax_C']==r['peak']['temperature_C'] and r['delta_C']==r['delta_peak']['value_C']
        assert r['fail_joint']==(r['Tmax_C']>70 or r['delta_C']>20)
        assert [r['Tmax_C'],r['delta_C']]==pytest.approx(expected['nominal'][r['scenario']],abs=1e-8)
    for r in controls['rows']:
        key=str(r['configuration']['physics']['max_step_s'])+'-'+str(r['configuration']['physics']['spacing_m'][0])
        assert [r['Tmax_C'],r['delta_C']]==pytest.approx(expected['controls'][key][r['scenario']],abs=1e-8)
        assert not r['fail_joint']
    assert data['summary']['P_joint']==math.fsum(r['weight'] for r in data['rows'] if r['fail_joint'])==0
    assert limit_states([71,70],[21,20])['fail_joint'].tolist()==[True,False]
