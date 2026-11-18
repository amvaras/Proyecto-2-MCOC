"""Euler explícito conservativo: eventos exactos, fuente integrada y balance global."""
from bisect import bisect_right
from dataclasses import dataclass
import math
import numpy as np
from ..e07.construction import ConstructionState
from ..e07.coupling import MaskedAssembly


@dataclass
class StageSolution:
    times_s: np.ndarray
    temperature_C: np.ndarray  # fotogramas × celdas ocupadas; NaN antes de activar
    metrics: list
    steps: list
    events: list
    checks: dict
    energy: dict


def simulate(voxels, events, boundaries=None, *, t_end_s, max_step_s=3600.,
             save_interval_s=3600., safety=.8, energy_reference_C=0., progress=None, observer=None,
             boundary_update=None, boundary_change_times_s=()):
    for name,value in [('t_end_s',t_end_s),('max_step_s',max_step_s),('save_interval_s',save_interval_s),('safety',safety),('reference',energy_reference_C)]:
        if isinstance(value,bool) or not math.isfinite(value):raise ValueError(name+' debe ser real finito')
    if t_end_s<0 or min(max_step_s,save_interval_s,safety)<=0 or safety>1:raise ValueError('Tiempo/pasos/safety fuera de rango')
    events=list(events);state=ConstructionState(voxels,events)
    materials={e.pour_id:e.material for e in events};occupied=voxels.occupation_mask
    count=int(occupied.sum());volume=voxels.grid.cell_volume
    snapshots=sorted({0.,float(t_end_s),*[float(e.activation_s) for e in events if e.activation_s<=t_end_s],
                      *[float(i*save_interval_s) for i in range(1,math.ceil(t_end_s/save_interval_s))]})
    if len(snapshots)>401 or len(snapshots)*count>30_000_000:raise ValueError('Historial demasiado grande')
    changes = sorted(set(boundary_change_times_s))
    if any(not math.isfinite(t) or t < 0 for t in changes):
        raise ValueError('Los cambios de borde deben tener tiempos finitos y no negativos')
    system=MaskedAssembly(voxels,state.active_mask(),materials,boundaries)
    initial_energy=system.energy(state.temperature_C,energy_reference_C)
    generated=outward_total=placed=0.;max_residual=0.;work=0
    history=[];metrics=[];steps=[];activations=[]
    def record_event(added,entry):
        if added:activations.append(dict(time_s=state.time_s,vertida_ids=added,placement_energy_J=entry))
    record_event(sorted(state.applied),initial_energy)
    def save():
        values=state.temperature_C[occupied].copy();history.append(values)
        finite=values[np.isfinite(values)]
        per_pour=[]
        for e in sorted(events,key=lambda e:e.pour_id):
            data=state.temperature_C[voxels.vertida_id==e.pour_id]
            active=e.pour_id in state.applied
            per_pour.append(dict(vertida_id=e.pour_id,active=active,age_s=state.pour_age(state.time_s,e.pour_id),
                min_C=float(data.min()) if active else None,max_C=float(data.max()) if active else None,
                mean_C=float(data.mean()) if active else None))
        energy=system.energy(state.temperature_C,energy_reference_C)
        row=dict(time_s=state.time_s,active_ids=sorted(state.applied),active_cells=int(system.active.sum()),
            min_C=float(finite.min()) if finite.size else None,max_C=float(finite.max()) if finite.size else None,
            mean_C=float(finite.mean()) if finite.size else None,by_pour=per_pour,energy_J=energy,
            hydration_energy_J=generated,outward_energy_J=outward_total,placement_energy_J=placed,
            balance_residual_J=energy-initial_energy-generated+outward_total-placed)
        metrics.append(row)
        if progress:progress(row)
    def observe():
        # Solo lectura: instrumentación E09 sin cambiar el avance físico E08.
        if observer is not None:
            temperature=state.temperature_C.view();temperature.flags.writeable=False
            active=system.active.view();active.flags.writeable=False
            observer(state.time_s,temperature,active)
    save();observe()
    for target in snapshots[1:]:
        while state.time_s<target:
            if len(steps)>=20000:raise ValueError('Más de 20000 pasos: revisar malla y duración')
            start = state.time_s
            step_target = target
            if boundary_update is not None:
                boundary_update(system, start)
                next_change = bisect_right(changes, start)
                if next_change < len(changes):
                    step_target = min(target, changes[next_change])
            remaining = step_target-start
            limit=system.stable_dt
            dt=min(max_step_s,safety*limit,remaining)
            if not math.isfinite(dt) or dt<=0 or start+dt==start:raise ValueError('Paso temporal fuera de rango')
            stop=step_target if dt==remaining else start+dt
            dt=stop-start
            source=np.zeros(voxels.grid.shape)
            for e in events:
                if e.pour_id in state.applied:
                    source[voxels.vertida_id==e.pour_id]=e.hydration.released(start-e.activation_s,stop-e.activation_s)/dt
            before=system.energy(state.temperature_C,energy_reference_C)
            net,outward=system.power(state.temperature_C,source)
            state.temperature_C[system.active]+=dt*net[system.active]/system.capacity[system.active]
            if not np.isfinite(state.temperature_C[system.active]).all() or np.any(state.temperature_C[system.active]<=-273.15):
                raise FloatingPointError('Temperatura activa no física o no finita')
            added=state.advance_to(stop)
            entry=0.
            if added:
                for e in events:
                    if e.pour_id in added:
                        entry+=np.count_nonzero(voxels.vertida_id==e.pour_id)*volume*e.material.rho*e.material.cp*(e.initial_C-energy_reference_C)
                system=MaskedAssembly(voxels,state.active_mask(),materials,boundaries)
                record_event(added,float(entry))
            heat=float(source.sum()*volume*dt);loss=float(outward*dt)
            generated+=heat;outward_total+=loss;placed+=float(entry)
            after=system.energy(state.temperature_C,energy_reference_C)
            residual=after-before-heat+loss-entry;max_residual=max(max_residual,abs(residual))
            steps.append(dict(start_s=start,end_s=stop,dt_s=dt,stable_dt_s=limit if math.isfinite(limit) else None,
                dt_over_limit=dt/limit if math.isfinite(limit) else 0.,hydration_energy_J=heat,
                outward_energy_J=loss,placement_energy_J=float(entry),balance_residual_J=float(residual)))
            work+=int(system.active.sum())
            observe()
            if work>1_000_000_000:raise ValueError('Presupuesto de cómputo excedido; usar malla más gruesa o menor duración')
        save()
    final_energy=system.energy(state.temperature_C,energy_reference_C)
    expected_heat=sum(r['released_energy_J'] for r in state.hydration_report())
    residual=final_energy-initial_energy-generated+outward_total-placed
    tolerance=1e-6+5e-12*(abs(initial_energy)+abs(final_energy)+abs(generated)+abs(outward_total)+abs(placed))
    checks=dict(global_energy_balance=abs(residual)<=tolerance,
        step_energy_balance=max_residual<=tolerance,
        hydration_potential=math.isclose(generated,expected_heat,rel_tol=1e-11,abs_tol=1e-6),
        stable_steps=all(row['dt_over_limit']<=safety*(1+1e-12) for row in steps),
        events_reached=all(e.pour_id in state.applied for e in events if e.activation_s<=t_end_s),
        inactive_is_nan=bool(np.isnan(state.temperature_C[occupied&~system.active]).all()),
        final_time_exact=state.time_s==t_end_s)
    if not all(checks.values()):raise ValueError('Falla en verificaciones E08: '+str(checks))
    return StageSolution(np.array(snapshots),np.stack(history),metrics,steps,activations,checks,
        dict(reference_C=energy_reference_C,initial_J=initial_energy,final_J=final_energy,
             hydration_J=generated,outward_J=outward_total,placement_after_zero_J=placed,
             residual_J=float(residual),max_step_residual_J=float(max_residual),tolerance_J=tolerance))
