"""E12 reutiliza el integrador existente; una fuente experimental y 336 h."""
from copy import deepcopy
from datetime import datetime,timezone
from pathlib import Path
import hashlib,time,zipfile
from unittest.mock import patch
import numpy as np
from ..e11.pipeline import run as run_pair,write_json,ROOT
from ..e11.vtkio import export_result
from ..e10.weather import iso_utc,utc_time
from .source import load_curve
from .metrics import GlobalRecorder

def arrays(path):
    with np.load(path) as z:return {k:z[k] for k in z.files}

def save_step_fields(path,**values):
    """NPZ estándar con LZMA: float64 exacto, sin cuantización ni dependencias."""
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_LZMA,allowZip64=True) as z:
        for name,value in values.items():
            with z.open(name+'.npy','w',force_zip64=True) as stream:
                np.lib.format.write_array(stream,np.asanyarray(value),allow_pickle=False)


def geometry_report(vox,cfg):
    from ..e07.ifc import read_pours
    from ..e07.faces import exposed_faces,contacts
    solids,meta=read_pours(ROOT/cfg['ifc']);faces=exposed_faces(vox);interfaces=contacts(vox,different_only=True);rows=[]
    for t in sorted({*[e['activation_s'] for e in cfg['physics']['events']],cfg['environment']['formwork']['remove_at_s']}):
        active=np.isin(vox.vertida_id,[e['pour_id'] for e in cfg['physics']['events'] if e['activation_s']<=t])
        f=exposed_faces(vox,active);ic=contacts(vox,active,different_only=True)
        rows.append(dict(time_h=t/3600,active_cells=int(active.sum()),exposed_faces=len(f.areas),exposed_area_m2=float(f.areas.sum()),future_faces=int((f.classification=='future_pour').sum()),closed_interface_faces=len(ic['area_m2'])))
    return dict(status='PASS',ifc=meta,solids=[dict(id=p.pour_id,guid=p.guid,name=p.name,mesh_volume_m3=p.mesh.volume,low_m=p.mesh.low.tolist(),high_m=p.mesh.high.tolist(),placement_m=p.placement_si.tolist(),closed_oriented=True) for p in solids],
                final_exterior=dict(faces=len(faces.areas),area_m2=float(faces.areas.sum())),interfaces=dict(faces=len(interfaces['area_m2']),area_m2=float(interfaces['area_m2'].sum())),construction=rows,
                note='Caras finales y temporalmente expuestas son distintas; calendario geométrico sin temperaturas inferidas. ClosedMesh valida cierre/orientación al extraer el IFC real.')


def run(config,output,*,plots=True,export=True,keep_all_steps=True,voxelization=None,vtk_dir=None,figure_dir=None):
    start=time.perf_counter();cfg=deepcopy(config);out=Path(output).resolve()
    for enabled,path in ((plots,figure_dir or ROOT/'figures'),(export,vtk_dir or ROOT/'vtk/e12')):
        path=Path(path).resolve()
        if enabled and (not path.is_relative_to(ROOT) or (path.exists() and any(path.iterdir()))):raise ValueError('Elegir carpeta nueva de artefactos; no reemplazar figuras o VTK existentes')
    if cfg['evaluation']['depth_m']!=.025:raise ValueError('Criterio E12: profundidad de 0.025 m')
    source=(ROOT/cfg['experimental_source']['file']).resolve()
    if not source.is_relative_to(ROOT/'data/hydration'):raise ValueError('Fuente dentro de data/hydration')
    spec=cfg['experimental_source'];curve,source_report=load_curve(source,spec['curve'],spec['tail'],spec.get('tau_s',86400.))
    if any(e.get('hydration') for e in cfg['physics']['events']):raise ValueError('E12 utiliza una sola curva común, sin mezclas por vertida')
    cfg['physics']['hydration']=dict(H_vol_J_m3=curve.H_vol_J_m3,duration_s=curve.duration_s)
    if min(cfg['physics']['spacing_m'])/2<cfg['evaluation']['depth_m']:raise ValueError('Resolución/profundidad fuera de la aproximación S25')
    records=[]
    def recorder(vox,events,env,target):
        capture=keep_all_steps and not records
        times=() if not records else [records[0].peak['time_h']*3600,records[0].delta_peak['time_h']*3600]
        # Los tiempos se guardan a partir del reloj del observador para evitar redondeo h→s.
        if records:times=[records[0].peak_time_s,records[0].delta_time_s]
        item=GlobalRecorder(vox,events,env,target,capture_all=capture,capture_times=times,depth_m=cfg['evaluation']['depth_m'])
        records.append(item);return item
    def offline(*args,**kwargs):raise RuntimeError('La simulación E12 no permite red; adquirir datos es una acción separada')
    with patch('urllib.request.urlopen',offline),patch('mcoc_p2.e10.weather.urlopen',offline):
        summary=run_pair(cfg,out,plots=False,export=False,hydration_curve=curve,recorder_factory=recorder,voxelization=voxelization)
    main,control=records;g=arrays(out/'grid.npz');f=arrays(out/'fields.npz')
    write_json(out/'geometry.json',geometry_report(main.voxels,cfg))
    # Incorporar los dos máximos exactos al historial visual, sin interpolar el campo.
    additions={main.peak_time_s:main.peak_field,main.delta_time_s:main.delta_field}
    merged=sorted(set(f['times_s'])|set(additions));lookup={float(t):i for i,t in enumerate(f['times_s'])}
    weather=[];constant=[]
    for t in merged:
        if t in lookup:
            weather.append(f['weather_C'][lookup[t]]);constant.append(f['constant_C'][lookup[t]])
        else:
            weather.append(additions[t]);constant.append(control.captured[t])
    labels=g['vertida_id'][g['occupation_mask']]
    births=np.array([next(e['activation_s'] for e in cfg['physics']['events'] if e['pour_id']==int(pid)) for pid in labels])
    merged=np.asarray(merged);active=merged[:,None]>=births
    np.savez_compressed(out/'fields.npz',times_s=merged,active=active,weather_C=np.stack(weather),constant_C=np.stack(constant))
    if keep_all_steps:
        all_times=main.arrays()['time_s'];field=np.stack(main.fields);main.fields.clear()
        save_step_fields(out/'all_steps.npz',times_s=all_times,weather_C=field,active=all_times[:,None]>=births)
        del field
    absolute=utc_time(cfg['simulation_start_utc']).timestamp()
    peak={**main.peak,'time_s':main.peak_time_s,'utc':iso_utc(absolute+main.peak_time_s),'active':True}
    delta={**main.delta_peak,'time_s':main.delta_time_s,'utc':iso_utc(absolute+main.delta_time_s)}
    x=main.arrays()
    grid=main.voxels
    main.assembly.set_face_conditions(main.assembly.face_g,main.assembly.reservoir,main.assembly.prescribed)
    # Las potencias aquí son estados instantáneos; la energía oficial es la suma de pasos.
    is_e13='e13_ensemble_member' in summary['weather_metadata']
    is_e14=cfg['physics'].get('description','').startswith('E14:')
    summary.update(delivery='E14' if is_e14 else 'E13' if is_e13 else 'E12',source=source_report,global_maximum=peak,global_delta25_maximum=delta,
                   evaluation=cfg['evaluation'],temperature_pass=peak['temperature_C']<=70,delta_pass=delta['value_C']<=20,
                   complete_336h=cfg['physics']['t_end_s']>=336*3600 if is_e13 else cfg['physics']['t_end_s']==336*3600,
                   deterministic_status=('CUMPLE' if peak['temperature_C']<=70 and delta['value_C']<=20 else 'NO CUMPLE') if (cfg['physics']['t_end_s']>=336*3600 if is_e13 else cfg['physics']['t_end_s']==336*3600) else 'NO VERIFICADO: horizonte parcial',
                   criterion_status='Aplicación del criterio del curso con aproximación lineal subcelda; sensibilidad espacial requerida',
                   saved_frames=len(merged),all_integration_fields=keep_all_steps,
                   end_trend=dict(Tmax_change_last_24h_C=float(x['Tmax_C'][-1]-x['Tmax_C'][np.argmin(abs(x['time_s']-(x['time_s'][-1]-86400)))]),
                                  maximum_at_final=peak['time_s']==cfg['physics']['t_end_s']),
                   dataset_policy='Forecast nuevo de 16 días; no mezcla con E11, sin extrapolación ni cola climática',
                   storage='fields: [tiempo,celdas ocupadas C-order]; all_steps conserva cada paso weather; active excluye ceros de relleno; campos float64',
                   elapsed_s=time.perf_counter()-start)
    write_json(out/'summary.json',summary)
    if export:
        hours=sorted(set([*cfg['export_hours'],peak['time_h'],delta['time_h']]))
        summary['vtk']=export_result(out,vtk_dir or ROOT/'vtk/e12',hours,collection_name='e14.pvd' if is_e14 else 'e13.pvd' if is_e13 else 'e12.pvd')
    if plots:
        from .plots import make_plots
        summary['figures']=make_plots(out,figure_dir or ROOT/'figures',vtk_dir or ROOT/'vtk/e12')
    summary['elapsed_s']=time.perf_counter()-start;write_json(out/'summary.json',summary)
    return summary

