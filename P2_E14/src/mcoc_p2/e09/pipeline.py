"""Baseline independiente, sin duplicar el integrador térmico de E08."""
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from ..e07.ifc import read_pours
from ..e07.voxel import voxelize
from ..e07.faces import exposed_faces,contacts
from ..e08.inputs import validate_config,events_from_config,boundaries
from ..e08.solver import simulate
from .analysis import FieldRecorder

ROOT=Path(__file__).resolve().parents[3]


def write_json(path,data):
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def stage_balances(solution):
    groups=[];start=0.;heat=loss=placed=residual=0.
    for row in solution.steps:
        heat+=row['hydration_energy_J'];loss+=row['outward_energy_J'];placed+=row['placement_energy_J'];residual+=row['balance_residual_J']
        if row['placement_energy_J']!=0 or any(e['time_s']==row['end_s'] for e in solution.events):
            groups.append(dict(start_h=start/3600,end_h=row['end_s']/3600,hydration_J=heat,outward_J=loss,placement_J=placed,balance_residual_J=residual))
            start=row['end_s'];heat=loss=placed=residual=0.
    groups.append(dict(start_h=start/3600,end_h=float(solution.times_s[-1]/3600),hydration_J=heat,outward_J=loss,placement_J=placed,balance_residual_J=residual))
    return groups


def run_baseline(ifc,configuration,output,*,plots=True,control=True,figure_dir=None):
    started=time.perf_counter();ifc=Path(ifc).resolve();out=Path(output).resolve()
    if not ifc.is_relative_to(ROOT) or not out.is_relative_to(ROOT):raise ValueError('IFC y resultados deben estar dentro de la entrega')
    if out.exists() and (not out.is_dir() or any(out.iterdir())):raise ValueError('Destino con contenido; usar uno nuevo')
    if not isinstance(configuration,dict) or set(configuration)!={'physics','analysis'}:raise ValueError('Config: physics y analysis')
    solids,metadata=read_pours(ifc);cfg=validate_config(configuration['physics'],solids)
    analysis=deepcopy(configuration['analysis'])
    if set(analysis)-{'core_target_m','horizontal_z_m','panel_hours','animation'}:raise ValueError('Opciones gráficas desconocidas')
    for h in analysis.get('panel_hours',[]):
        if isinstance(h,bool) or not isinstance(h,(float,int)) or not np.isfinite(h) or h<0:raise ValueError('Horas gráficas finitas no negativas')
    voxels=voxelize(solids,cfg['spacing_m'],margin=cfg['margin_m']);events=events_from_config(cfg);bc=boundaries(cfg)
    recorder=FieldRecorder(voxels,events,bc,analysis.get('core_target_m',(0,0,1.65)))
    options=dict(t_end_s=cfg['t_end_s'],max_step_s=cfg['max_step_s'],save_interval_s=cfg['save_interval_s'],
                 safety=cfg['safety'],energy_reference_C=cfg['energy_reference_C'])
    print(f"E09: {int(voxels.occupation_mask.sum())} vóxeles, {cfg['t_end_s']/3600:g} h",flush=True)
    solution=simulate(voxels,events,bc,observer=recorder,**options)
    control_result=None;control_statistics=None
    if control:
        cold=deepcopy(cfg);cold['hydration']['H_vol_J_m3']=0.
        for event in cold['events']:
            if 'hydration' in event:event['hydration']['H_vol_J_m3']=0.
        cold_events=events_from_config(cold);cold_recorder=FieldRecorder(voxels,cold_events,bc,analysis.get('core_target_m',(0,0,1.65)))
        print('E09: control sin hidratación',flush=True)
        control_result=simulate(voxels,cold_events,bc,observer=cold_recorder,**options)
        control_statistics=cold_recorder.arrays()
    out.mkdir(parents=True,exist_ok=False)
    occupied=voxels.occupation_mask;labels=voxels.vertida_id[occupied]
    activation={e.pour_id:e.activation_s for e in events}
    active=np.array([[t>=activation[int(pid)] for pid in labels] for t in solution.times_s],dtype=bool)
    field=np.where(active,solution.temperature_C,0.)
    if not np.isfinite(field).all() or np.any(~np.isfinite(solution.temperature_C[active])):raise ValueError('Temperaturas guardadas no finitas')
    np.savez_compressed(out/'grid.npz',vertida_id=voxels.vertida_id,occupation_mask=occupied,
        occupied_flat_indices=np.flatnonzero(occupied),origin_m=voxels.grid.origin,spacing_m=voxels.grid.spacing,
        x_m=voxels.grid.coordinates[0],y_m=voxels.grid.coordinates[1],z_m=voxels.grid.coordinates[2])
    np.savez_compressed(out/'temperature.npz',times_s=solution.times_s,temperature_C=field,active_mask=active)
    stats=recorder.arrays();np.savez_compressed(out/'statistics.npz',**stats)
    step_names=['start_s','end_s','dt_s','dt_over_limit','hydration_energy_J','outward_energy_J','placement_energy_J','balance_residual_J']
    steps={k:np.array([r[k] for r in solution.steps]) for k in step_names}
    steps['stable_dt_s']=np.array([r['stable_dt_s'] or 0. for r in solution.steps])
    steps['stable_dt_finite']=np.array([r['stable_dt_s'] is not None for r in solution.steps])
    np.savez_compressed(out/'steps.npz',**steps)
    if control_statistics is not None:np.savez_compressed(out/'control.npz',**control_statistics)
    study=[]
    for h in cfg['resolutions_m']:
        t=time.perf_counter();row=voxelize(solids,h,margin=cfg['margin_m']).report();row['elapsed_s']=time.perf_counter()-t;study.append(row)
    faces=exposed_faces(voxels);interfaces=contacts(voxels)
    # Estado de áreas realmente activas solo en los eventos y el final.
    surface_states=[]
    for t in sorted({0.,cfg['t_end_s'],*[e.activation_s for e in events if e.activation_s<=cfg['t_end_s']]}):
        mask=np.isin(voxels.vertida_id,[e.pour_id for e in events if e.activation_s<=t]);f=exposed_faces(voxels,mask)
        surface_states.append(dict(time_h=t/3600,active_cells=int(mask.sum()),exposed_area_m2=float(f.areas.sum()),
                                   faces_toward_future=int(np.count_nonzero(f.classification=='future_pour'))))
    summary=dict(status='PASS',delivery='E09',duration_h=cfg['t_end_s']/3600,configuration=dict(physics=cfg,analysis=analysis),
        ifc={**metadata,'relative_path':ifc.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(ifc.read_bytes()).hexdigest()},
        pours=[s.summary() for s in solids],grid=voxels.report(),volume_study=study,
        exterior=faces.report(),interfaces=dict(count=len(interfaces['area_m2']),area_m2=float(interfaces['area_m2'].sum())),
        active_surfaces=surface_states,thermal=recorder.summary(),energy=solution.energy,checks=solution.checks,
        stages=stage_balances(solution),events=solution.events,
        temporal=dict(integration_steps=len(solution.steps),saved_frames=len(solution.times_s),
                      min_step_s=float(steps['dt_s'].min()) if len(solution.steps) else 0.,
                      max_step_s=float(steps['dt_s'].max()) if len(solution.steps) else 0.,
                      max_dt_over_limit=float(steps['dt_over_limit'].max()) if len(solution.steps) else 0.,
                      smallest_stable_step_s=float(steps['stable_dt_s'][steps['stable_dt_finite']].min()) if steps['stable_dt_finite'].any() else None),
        snapshot_balance=[{k:r[k] for k in ('time_s','energy_J','hydration_energy_J','outward_energy_J','placement_energy_J','balance_residual_J')} for r in solution.metrics],
        storage='temperature_C: [frame, occupied index C-order]; 0 fuera de active_mask es relleno. grid.npz reconstruye [i,j,k]=XYZ. statistics registra cada paso. No interpretar rellenos como temperatura.',
        units=dict(temperature='degC',time='s',length='m',energy='J',q_dot_h='W/m3'),
        assumptions=['Parámetros ilustrativos sin calibración Freirina; clima constante, sin datos meteorológicos.',
                     'Base z- adiabática; caras expuestas superiores y laterales Robin, también frente a vertidas futuras.',
                     'Propiedades constantes, contacto perfecto, área staircase, sin suelo explícito ni Arrhenius.',
                     'Superficies de sondas Robin reconstruidas desde centro a cara; aproximación local de media celda.'],
        provenance=dict(source_archive='P2_E08.zip (sin modificar)',
                        source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'src').rglob('*.py'))}),
        finished_utc=datetime.now(timezone.utc).isoformat(),elapsed_s=time.perf_counter()-started)
    if control_result is not None:
        summary['control_no_hydration']=dict(peak_C=float(control_statistics['Tmax_C'].max()),energy=control_result.energy,checks=control_result.checks)
    summary['checks']={**summary['checks'],'stored_field_finite':bool(np.isfinite(field).all()),'active_frames_match_events':bool(np.array_equal(np.isfinite(solution.temperature_C),active)),
                       'statistics_every_step':len(stats['time_s'])==len(solution.steps)+1}
    if not all(summary['checks'].values()):raise ValueError('Verificación E09 fallida')
    write_json(out/'inputs.json',summary['configuration']);write_json(out/'summary.json',summary)
    if plots:
        from .plots import generate_figures
        summary['figures']=generate_figures(out,figure_dir or ROOT/'figures',animation=bool(analysis.get('animation',True)))
        write_json(out/'summary.json',summary)
    return summary
