"""F02 embeds a heat exchange extension in E08's boundary/power interface."""
from dataclasses import replace
from bisect import bisect_right
from copy import deepcopy
from pathlib import Path
import numpy as np

from ..e08.solver import simulate
from ..e08.inputs import events_from_config, validate_config
from ..e11.pipeline import ROOT, make_environment
from ..e11.weather import window, iso_utc
from ..e12.metrics import GlobalRecorder
from ..e12.source import load_curve
from ..e13.evaluator import Evaluator
from ..e13.plans import thermal_config, validate_plan
from ..e14.io import read
from ..e14.model import catalog
from ..e14.statistics import limit_states
from .pipes import Design, Network

CONFIG = ROOT / 'configs/f02/moderate_20.json'

class StagedProtection:
    def __init__(self, environment, stages):
        self.environment = environment
        self.formwork = environment.formwork
        self.times = tuple(hours * 3600 for hours, _ in stages)
        board, insulation = self.formwork.layers
        self.forms = [self.formwork] + [
            replace(self.formwork, layers=(board, replace(insulation, thickness_m=thickness)))
            for _, thickness in stages
        ]
        self.change_times_s = tuple(sorted(set(environment.change_times_s) | set(self.times)))

    def __getattr__(self, name):
        return getattr(self.environment, name)

    def __call__(self, assembly, time_s):
        self.environment.formwork = self.forms[bisect_right(self.times, time_s)]
        self.environment(assembly, time_s)

class InternalExchange:
    """Extend the energy flux callback only on this run's integrator assemblies."""
    def __init__(self, environment, network):
        self.environment = environment
        self.network = network
        self.trace = []
        d = network.design
        self.change_times_s = tuple(sorted(set(environment.change_times_s) |
                                           {d.start_h*3600, d.stop_h*3600}))

    def __call__(self, assembly, time_s):
        self.environment(assembly, time_s)
        assembly.stable_dt = self.network.limit(assembly, time_s)
        # E08 accounts the cooling as outgoing power. Retain the separate ledger.
        original_power = type(assembly).power
        def power(temperature, source):
            net, boundary = original_power(assembly, temperature, source)
            cooled = self.network.apply(net, temperature, time_s)
            self.trace.append((time_s, cooled, boundary))
            return net, boundary + cooled
        assembly.power = power

    def close_ledger(self, solution):
        if len(self.trace) != len(solution.steps):
            raise ArithmeticError('Cada paso debe tener un balance de agua')
        terms = []
        for step, (time_s, watts, boundary_watts) in zip(solution.steps, self.trace, strict=True):
            dt_s = step['dt_s']
            if time_s != step['start_s'] or not np.isclose(
                (watts + boundary_watts)*dt_s, step['outward_energy_J'], atol=1e-5, rtol=1e-12
            ):
                raise ArithmeticError('Flujos térmicos inconsistentes')
            terms.append(watts*dt_s)
        return float(sum(terms))

def configuration():
    return read(CONFIG)

def run_case(scenario_id, *, spacing=None, step=None, evaluator=None, visual=False):
    study = configuration()
    engine = evaluator if evaluator is not None else Evaluator()
    scenario = next(s for s in catalog() if s['id'] == scenario_id)
    plan = validate_plan(study['construction'], engine.volumes)
    base = deepcopy(engine.base)
    board, insulation = base['environment']['formwork']['layers']
    base['environment']['formwork']['layers'] = [board, {**insulation, 'thickness_m': study['insulation_initial_m']}]
    cfg = thermal_config(base, plan, scenario, spacing=spacing or study['spacing_m'],
                         horizon_h=study['horizon_h'], max_step_s=step or study['max_step_s'])
    p = cfg['physics']
    spec = cfg['experimental_source']
    curve, _ = load_curve(ROOT/spec['file'], spec['curve'], spec['tail'], spec['tau_s'])
    p['hydration'] = dict(H_vol_J_m3=curve.H_vol_J_m3, duration_s=curve.duration_s)
    cfg['physics'] = p = validate_config(p, engine.solids)
    grid = engine.grid(tuple(p['spacing_m']))
    events = [replace(event, hydration=curve) for event in events_from_config(p)]
    weather = window(ROOT/cfg['snapshot'], cfg['simulation_start_utc'], p['t_end_s'])
    protection = StagedProtection(make_environment(grid, weather, cfg['environment']),
                                  study['insulation_stages_h_m'])
    network = Network(grid, engine.solids, Design(**study['pipe']))
    exchange = InternalExchange(protection, network)
    recorder = GlobalRecorder(grid, events, protection, cfg['core_target_m'])
    recorder.left_times.update(protection.times)
    solution = simulate(grid, events, t_end_s=p['t_end_s'], max_step_s=p['max_step_s'],
                        save_interval_s=p['save_interval_s'], safety=.8, energy_reference_C=20,
                        observer=recorder, boundary_update=exchange,
                        boundary_change_times_s=exchange.change_times_s)
    extracted = exchange.close_ledger(solution)
    data = recorder.arrays()
    states = limit_states(recorder.peak['temperature_C'], recorder.delta_peak['value_C'])
    cold = recorder.delta_peak['cold']
    solid = next(s.mesh for s in engine.solids if s.pour_id == cold['vertida_id'])
    depth = float(np.min(solid.offsets - solid.normals @ np.asarray(cold['coordinate_m'])))
    row = dict(plan=plan['id'], scenario=scenario_id, weight=scenario['weight'],
               D_h=plan['D_h'], Tmax_C=recorder.peak['temperature_C'],
               delta_C=recorder.delta_peak['value_C'], **{k:v.item() for k,v in states.items()},
               peak={**recorder.peak,'time_s':recorder.peak_time_s,
                     'utc':iso_utc(weather.start+recorder.peak_time_s)},
               delta_peak={**recorder.delta_peak,'time_s':recorder.delta_time_s,
                           'utc':iso_utc(weather.start+recorder.delta_time_s)},
               coverage=weather.coverage(), configuration=cfg, checks=solution.checks,
               steps=len(solution.steps), S25_depth_IFC_m=depth,
               energy={**solution.energy, 'cooling_J':extracted,
                       'surface_outward_J':solution.energy['outward_J']-extracted},
               water=dict(max_kW=network.peak_kW, flow_peak_ls=network.max_flow_ls,
                          max_return_C=network.max_return, resistance_K_m_W=network.r_per_m,
                          active_length_m=sum(c['length_m'] for c in network.circuits),
                          circuits=network.circuits))
    if not visual:
        return row, None
    # Same case, with the exact observer fields at both maxima added to the timeline.
    frames = dict(zip(solution.times_s, np.nan_to_num(solution.temperature_C,nan=0.)))
    frames.update({recorder.peak_time_s:recorder.peak_field, recorder.delta_time_s:recorder.delta_field})
    times = np.asarray(sorted(frames))
    indices = np.argwhere(grid.occupation_mask)
    centers = np.array(grid.grid.origin) + (indices + .5) * grid.grid.spacing
    return row, dict(times_s=times, temperature_C=np.stack([frames[t] for t in times]).astype(np.float32),
                     indices=indices, centers_m=centers, labels=grid.vertida_id[grid.occupation_mask],
                     origins_m=grid.grid.origin, spacing_m=grid.grid.spacing, shape=grid.grid.shape,
                     births_s=[next(e.activation_s for e in events if e.pour_id==int(pid))
                               for pid in grid.vertida_id[grid.occupation_mask]],
                     stats_time_s=data['time_s'], stats_Tmax_C=data['Tmax_C'],
                     stats_S25_C=data['S25min_C'], stats_delta_C=data['delta25_C'])
