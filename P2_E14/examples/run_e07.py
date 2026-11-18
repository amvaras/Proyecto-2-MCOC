"""E07 reproducible: IFC, vóxeles, caras, calendario y fuente preliminar (SI)."""
import argparse
from datetime import datetime,timezone
import json
import math
from pathlib import Path
import time
import numpy as np
from mcoc_p2 import Material,Robin
from mcoc_p2.e07.ifc import read_pours
from mcoc_p2.e07.voxel import voxelize
from mcoc_p2.e07.faces import exposed_faces,contacts
from mcoc_p2.e07.hydration import AdiabaticCurve
from mcoc_p2.e07.construction import PourEvent,ConstructionState
from mcoc_p2.e07.coupling import MaskedAssembly

ROOT=Path(__file__).resolve().parents[1]


def save_json(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def configuration(path):
    data=json.loads(path.read_text(encoding='utf-8-sig'))
    allowed={'description','spacing_m','resolutions_m','margin_m','t_end_s','max_step_s','h_W_m2K','ambient_C','material','hydration','events'}
    if not isinstance(data,dict) or data.keys()-allowed:raise ValueError('Claves desconocidas en configuración')
    return data


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ifc',type=Path,default=ROOT/'geometry/foundation.ifc')
    p.add_argument('--config',type=Path,default=ROOT/'configs/e07/demo.json')
    p.add_argument('--output',type=Path)
    p.add_argument('--inspect-only',action='store_true');p.add_argument('--no-plots',action='store_true')
    p.add_argument('--spacing',type=float,nargs='+');p.add_argument('--resolutions',type=float,nargs='+')
    for flag in ('margin','h','ambient','interval-hours','heat-mj-m3','duration-hours','t-end-hours','max-step'):
        p.add_argument('--'+flag,type=float)
    a=p.parse_args(argv)
    try:
        cfg=configuration(a.config)
        overrides={'spacing':'spacing_m','resolutions':'resolutions_m','margin':'margin_m','h':'h_W_m2K','ambient':'ambient_C','max_step':'max_step_s'}
        for key,target in overrides.items():
            if getattr(a,key) is not None:cfg[target]=getattr(a,key)
        if a.t_end_hours is not None:cfg['t_end_s']=a.t_end_hours*3600
        if a.interval_hours is not None:
            if not math.isfinite(a.interval_hours) or a.interval_hours<0:raise ValueError('Intervalo finito no negativo')
            for i,e in enumerate(sorted(cfg['events'],key=lambda e:e['pour_id'])):e['activation_s']=i*a.interval_hours*3600
        if a.heat_mj_m3 is not None:cfg['hydration']['H_vol_J_m3']=a.heat_mj_m3*1e6
        if a.duration_hours is not None:cfg['hydration']['duration_s']=a.duration_hours*3600
        solids,meta=read_pours(a.ifc)
        # Validar antes de escribir y antes de reservar la grilla.
        material=Material(**cfg['material']);curve=AdiabaticCurve(**cfg['hydration'])
        events=[]
        for supplied in cfg['events']:
            e=dict(supplied)
            event_material=Material(**{**cfg['material'],**e.pop('material',{})})
            event_curve=AdiabaticCurve(**{**cfg['hydration'],**e.pop('hydration',{})})
            events.append(PourEvent(**e,material=event_material,hydration=event_curve))
        bc={name:Robin(cfg['h_W_m2K'],cfg['ambient_C']) for name in (a+b for a in 'xyz' for b in '-+')}
        out=a.output or ROOT/'results/e07'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        if out.exists() and (not out.is_dir() or any(out.iterdir())):raise ValueError('Destino con contenido; no sobrescribir resultados')
        out.mkdir(parents=True,exist_ok=True)
        geometries={}
        for s in solids:
            geometries[f'vertices_{s.pour_id}']=s.mesh.vertices;geometries[f'triangles_{s.pour_id}']=s.mesh.triangles
        np.savez_compressed(out/'geometry.npz',**geometries)
        save_json(out/'geometry.json',{**meta,'pours':[s.summary() for s in solids]})
        if a.inspect_only:print('PASS inspección IFC: '+str(len(solids))+' vertidas');return 0
        start=time.perf_counter();voxels=voxelize(solids,cfg['spacing_m'],margin=cfg['margin_m']);nominal=voxels.report();nominal['elapsed_s']=time.perf_counter()-start
        coords={axis+'_m':c for axis,c in zip('xyz',voxels.grid.coordinates)}
        np.savez_compressed(out/'voxels.npz',vertida_id=voxels.vertida_id,occupation_mask=voxels.occupation_mask,
                            origin_m=voxels.grid.origin,spacing_m=voxels.grid.spacing,**coords)
        study=[]
        if len(cfg['resolutions_m'])<3 or len(set(cfg['resolutions_m']))<3:raise ValueError('Al menos tres resoluciones distintas')
        for h in cfg['resolutions_m']:
            start=time.perf_counter();row=voxelize(solids,h,margin=cfg['margin_m']).report();row['elapsed_s']=time.perf_counter()-start;study.append(row)
        faces=exposed_faces(voxels);interface=contacts(voxels)
        np.savez_compressed(out/'faces.npz',indices=faces.indices,axis=faces.axis,sign=faces.sign,area_m2=faces.areas,
                            normals=faces.normals,vertida_id=faces.pour_id,classification=faces.classification,**{'interface_'+k:v for k,v in interface.items()})
        state=ConstructionState(voxels,events);timeline=[]
        for t in state.time_grid(cfg['t_end_s'],cfg['max_step_s']):
            added=state.advance_to(float(t))
            if t==0:added=[e.pour_id for e in events if e.activation_s==0]
            active=state.active_mask();exposed=exposed_faces(voxels,active);edges=contacts(voxels,active)
            timeline.append(dict(time_s=float(t),activated_now=added,active_ids=sorted(state.applied),active_cells=int(active.sum()),
                                 active_volume_m3=int(active.sum())*voxels.grid.cell_volume,exposed_faces=len(exposed.areas),
                                 exposed_area_m2=float(exposed.areas.sum()),future_exposed_faces=int(np.count_nonzero(exposed.classification=='future_pour')),
                                 active_interface_faces=len(edges['area_m2']),age_s={str(e.pour_id):state.pour_age(float(t),e.pour_id) for e in events}))
        source=state.hydration_source();assembly=MaskedAssembly(voxels,state.active_mask(),{e.pour_id:e.material for e in events},bc)
        power,outward=assembly.power(state.temperature_C,source)
        generated=float(source.sum()*voxels.grid.cell_volume);residual=float(power.sum()-generated+outward)
        hydration_rows=state.hydration_report()
        tolerance=1e-9*max(1.,abs(generated),abs(outward))
        if abs(residual)>tolerance:raise ValueError('No cierra balance de potencia enmascarada')
        # No integrar T: esto es un ensamblaje y una demostración de estados.
        np.savez_compressed(out/'construction.npz',active_mask=state.active_mask(),placement_temperature_C=state.temperature_C,
                            hydration_source_W_m3=source,capacity_J_K=assembly.capacity,power_snapshot_W=power)
        area_pairs={}
        for pair,area in zip(interface['pour_ids'],interface['area_m2']):
            key='-'.join(map(str,pair));area_pairs[key]=area_pairs.get(key,0.)+float(area)
        report=dict(status='PASS',started_from_ifc=meta,configuration=cfg,nominal=nominal,volume_study=study,
                    exterior=faces.report(),interfaces=dict(count=len(interface['area_m2']),area_m2=float(interface['area_m2'].sum()),area_by_pair_m2=area_pairs),
                    timeline=timeline,hydration=dict(model='Curva adiabática cosenoidal prescrita, sin calibrar',temperature_dependence=False,
                    H_vol_J_m3=curve.H_vol_J_m3,duration_s=curve.duration_s,potential_released_J_m3=float(curve.released(0,curve.duration_s))),
                    assembly=dict(capacity_active_J_K=float(assembly.capacity.sum()),conductive_contacts=len(assembly.g),stable_dt_s=None if not math.isfinite(assembly.stable_dt) else assembly.stable_dt,
                                  source_power_W=generated,outward_power_W=outward,balance_residual_W=residual,balance_tolerance_W=tolerance),
                    integration='Ensamblaje enmascarado de potencia y capacidad verificado; NO integrador transiente final de fundación',
                    scope='Cronograma y calor FICTICIOS de demostración; sin calibración Freirina',finished_utc=datetime.now(timezone.utc).isoformat())
        report['hydration'].update(by_pour=hydration_rows,
            total_prescribed_released_energy_J=sum(row['released_energy_J'] for row in hydration_rows),
            global_parameters_note='H_vol_J_m3 y duration_s superiores son valores globales por defecto; by_pour contiene los parámetros efectivos.',
            energy_note='Integral de generación prescrita desde la colocación; no energía sensible de una simulación térmica resuelta.')
        checks=dict(labels_match_ifc=set(map(int,np.unique(voxels.vertida_id)))-{0}==set(voxels.guid_by_id),
                    occupancy_consistent=bool(np.array_equal(voxels.occupation_mask,voxels.vertida_id>0)),
                    per_pour_volume_positive=all(row['volume_voxel_m3']>0 for row in nominal['by_pour']),
                    volume_equals_cell_count=math.isclose(nominal['volume_voxel_m3'],nominal['occupied_cells']*voxels.grid.cell_volume,rel_tol=1e-14),
                    inactive_capacity_zero=bool(np.all(assembly.capacity[~state.active_mask()]==0)),
                    source_nonnegative=bool(np.all(source>=0)),
                    released_potential_consistent=all(math.isclose(float(e.hydration.released(0,e.hydration.duration_s)),e.hydration.H_vol_J_m3,rel_tol=1e-14,abs_tol=1e-12) for e in events),
                    all_events_reached=all(e.activation_s in [row['time_s'] for row in timeline] for e in events if e.activation_s<=cfg['t_end_s']),
                    masked_power_balance=abs(residual)<=tolerance,
                    per_pour_source_matches_field=math.isclose(sum(row['source_power_W'] for row in hydration_rows),generated,rel_tol=1e-12,abs_tol=1e-9))
        report['checks']=checks
        report['volume_accuracy_note']='Errores cuantificados por pieza y total, sin imponer monotonía ni un umbral universal de precisión geométrica.'
        if not all(checks.values()):raise ValueError('Incumplimiento de invariantes E07: '+str(checks))
        if not a.no_plots:
            from mcoc_p2.e07.plots import create_figures
            report['figures']=create_figures(voxels,study,timeline,events,out/'figures')
        save_json(out/'summary.json',report)
        print(json.dumps({k:report[k] for k in ('status','nominal','exterior','interfaces','hydration','assembly','integration')},ensure_ascii=False,indent=2))
        return 0
    except (ValueError,TypeError,KeyError,OSError,RuntimeError,OverflowError) as exc:
        print('ERROR: '+str(exc));return 2


if __name__=='__main__':raise SystemExit(main())
