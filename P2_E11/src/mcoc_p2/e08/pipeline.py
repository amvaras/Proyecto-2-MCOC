"""Pipeline IFC→grid→transiente; archivos reutilizables por interfaz y consola."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import numpy as np
from ..e07.ifc import read_pours
from ..e07.voxel import voxelize
from ..e07.faces import exposed_faces
from .inputs import validate_config,events_from_config,boundaries
from .solver import simulate


def write_json(path,data):
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def view_geometry(voxels,solids):
    """Superficies por vertida: ocultar una revela interfaces sin modificar física."""
    grid=voxels.grid;center=(np.array(grid.origin)+np.array(grid.upper))/2
    lookup=np.full(grid.shape,-1,dtype=np.int32)
    lookup[voxels.occupation_mask]=np.arange(int(voxels.occupation_mask.sum()))
    groups=[]
    for solid in solids:
        faces=exposed_faces(voxels,voxels.vertida_id==solid.pour_id)
        positions=np.array(grid.origin)+(faces.indices+.5)*np.array(grid.spacing)
        positions[np.arange(len(positions)),faces.axis]+=faces.sign*np.array(grid.spacing)[faces.axis]/2
        data=np.column_stack((positions-center,faces.axis,faces.sign,lookup[tuple(faces.indices.T)]))
        groups.append(dict(vertida_id=solid.pour_id,name=solid.name,faces=data.tolist()))
    return dict(spacing_m=grid.spacing,center_world_m=center.tolist(),extent_m=(np.array(grid.upper)-np.array(grid.origin)).tolist(),
                occupied_cells=int(voxels.occupation_mask.sum()),groups=groups,
                visibility_note='Ocultar o mostrar afecta solo al dibujo; las celdas continúan participando en la simulación.')


def run_pipeline(ifc,configuration,output,*,plots=True):
    output=Path(output)
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError('Destino con contenido; no sobrescribir resultados')
    solids,metadata=read_pours(ifc);cfg=validate_config(configuration,solids)
    output.mkdir(parents=True,exist_ok=True)
    write_json(output/'inputs.json',cfg)
    shutil.copyfile(ifc,output/'model.ifc')
    voxels=voxelize(solids,cfg['spacing_m'],margin=cfg['margin_m'])
    nominal=voxels.report()
    study=[voxelize(solids,h,margin=cfg['margin_m']).report() for h in cfg['resolutions_m']]
    def progress(row):
        # La interfaz omite las lecturas incompletas y vuelve a consultar el progreso.
        try:
            write_json(output/'progress.json', dict(time_s=row['time_s'], t_end_s=cfg['t_end_s'],
                       max_C=row['max_C'], active_ids=row['active_ids']))
        except PermissionError:
            # Un bloqueo del indicador de progreso en Windows no interrumpe el cálculo.
            pass
    events=events_from_config(cfg)
    result=simulate(voxels,events,boundaries(cfg),t_end_s=cfg['t_end_s'],max_step_s=cfg['max_step_s'],
        save_interval_s=cfg['save_interval_s'],safety=cfg['safety'],energy_reference_C=cfg['energy_reference_C'],progress=progress)
    np.savez_compressed(output/'voxels.npz',vertida_id=voxels.vertida_id,occupation_mask=voxels.occupation_mask,
        origin_m=voxels.grid.origin,spacing_m=voxels.grid.spacing)
    np.savez_compressed(output/'solution.npz',times_s=result.times_s,temperature_C=result.temperature_C,
        occupied_flat_indices=np.flatnonzero(voxels.occupation_mask),grid_shape=voxels.grid.shape)
    write_json(output/'geometry.json',view_geometry(voxels,solids))
    finite=result.temperature_C[np.isfinite(result.temperature_C)]
    report=dict(status='PASS',delivery='E08',configuration=cfg,ifc=metadata,pours=[s.summary() for s in solids],
        nominal=nominal,volume_study=study,times_s=result.times_s.tolist(),frames=result.metrics,
        activation_events=result.events,steps=result.steps,energy=result.energy,checks=result.checks,
        temperature_range_C=[float(finite.min()),float(finite.max())] if finite.size else [0.,1.],
        maximum_step_s=max((r['dt_s'] for r in result.steps),default=0.),
        max_dt_over_limit=max((r['dt_over_limit'] for r in result.steps),default=0.),
        integration='Euler explícito conservativo sobre máscara activa; hidratación integrada exactamente por intervalo.',
        assumptions=['Parámetros y cronograma ilustrativos, sin calibración Freirina.',
            'Hidratación prescrita por edad real, sin dependencia de temperatura.',
            'Contacto perfecto; bordes constantes por orientación; área staircase sin corregir.',
            'La visibilidad es solo del dibujo y no cambia la física.'],
        finished_utc=datetime.now(timezone.utc).isoformat())
    if plots:
        from .plots import create_figures
        report['figures']=create_figures(voxels,result,study,output/'figures')
    write_json(output/'summary.json',report)
    return report
