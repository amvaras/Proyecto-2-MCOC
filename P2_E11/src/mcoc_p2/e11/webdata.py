"""Adaptación de resultados E11 a la web; la física permanece en pipeline.run."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import numpy as np
from ..e07.ifc import read_pours
from ..e08.inputs import validate_config
from ..e10.weather import iso_utc,utc_time
from .pipeline import ROOT, make_environment
from .weather import validate, window


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def arrays(path):
    with np.load(path,allow_pickle=False) as z:return {k:z[k] for k in z.files}
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_web(config,model,snapshots):
    c=deepcopy(config)
    required={'ifc','snapshot','simulation_start_utc','constant_reference_C','physics','core_target_m','export_hours','environment'}
    if not isinstance(c,dict) or set(c)!=required:raise ValueError('Configuración E11 incompleta o con claves desconocidas')
    if c['snapshot'] not in snapshots:raise ValueError('Selecciona un snapshot local reconocido')
    if c['ifc']!='geometry/foundation.ifc':raise ValueError('El IFC se selecciona mediante el identificador del modelo')
    solids,_=read_pours(model);p=validate_config(c['physics'],solids)
    if not 0<p['t_end_s']<=72*3600:raise ValueError('Duración web: mayor que cero y hasta 72 h')
    p['save_interval_s']=min(p['save_interval_s'],p['t_end_s']/2)
    low=np.min([s.mesh.low for s in solids],axis=0);high=np.max([s.mesh.high for s in solids],axis=0)
    n=int(np.prod(np.ceil((high-low+2*p['margin_m'])/p['spacing_m'])))
    if n>150000:raise ValueError('La interfaz admite hasta 150000 celdas de grilla; aumenta el tamaño de celda')
    if n*(int(np.ceil(p['t_end_s']/p['save_interval_s']))+len(p['events'])+1)>3000000:raise ValueError('Demasiados campos guardados; aumenta el intervalo de guardado')
    if p['t_end_s']/p['max_step_s']>18000:raise ValueError('El paso solicitado supera el presupuesto web de pasos')
    if min(e['activation_s'] for e in p['events'])!=0:raise ValueError('Para esta demo debe existir una vertida inicial en t=0')
    if len(c['core_target_m'])!=3 or not np.isfinite(c['core_target_m']).all():raise ValueError('Sonda núcleo requiere tres coordenadas finitas')
    if not np.isfinite(c['constant_reference_C']) or c['constant_reference_C']<=-273.15:raise ValueError('Temperatura constante no física')
    if not isinstance(c['export_hours'],list) or any(not isinstance(h,(int,float)) or not np.isfinite(h) or h<0 for h in c['export_hours']):raise ValueError('Instantes VTK finitos y no negativos')
    # Valida todas las dataclasses de aire/suelo/moldaje antes de crear tareas.
    from .pipeline import ConstantWeather
    weather=window(ROOT/c['snapshot'],c['simulation_start_utc'],p['t_end_s'])
    ConstantWeather(weather,c['constant_reference_C'])
    class Geometry:
        occupation_mask=np.ones((1,1,1),dtype=bool)
    make_environment(Geometry(),weather,c['environment'])
    c['physics']=p
    return c


def weather_data(config):
    snap=validate(ROOT/config['snapshot'])
    selected=window(ROOT/config['snapshot'],config['simulation_start_utc'],config['physics']['t_end_s'])
    return dict(status='PASS',metadata=snap.metadata,snapshot=config['snapshot'],samples=len(snap.air),
                seconds=list(snap.seconds),temperature_C=list(snap.air),coverage=selected.coverage(),
                checks=dict(raw_hash=True,normalized_hash=True,units=True,coverage=True,finite=True,ordered_hourly=True),
                minimum_C=float(min(snap.air)),maximum_C=float(max(snap.air)))


def geometry(folder):
    g=arrays(Path(folder)/'grid.npz');s=read(Path(folder)/'summary.json')
    shape=g['vertida_id'].shape;flat=g['occupied_flat_indices'];indices=np.array(np.unravel_index(flat,shape)).T
    centers=g['origin_m']+(indices+.5)*g['spacing_m']
    return dict(origin_m=g['origin_m'].tolist(),spacing_m=g['spacing_m'].tolist(),shape=list(shape),
                centers_m=centers.tolist(),indices=indices.tolist(),labels=g['vertida_id'].ravel()[flat].tolist(),
                bounds_m=[g['origin_m'].tolist(),(g['origin_m']+np.array(shape)*g['spacing_m']).tolist()],
                groups=s['grid']['by_pour'],probes=s['probes'],source='grid.npz + fields.npz; misma indexación validada contra VTI')


def presentation(folder):
    folder=Path(folder);s=read(folder/'summary.json');f=arrays(folder/'fields.npz');a=arrays(folder/'statistics.npz');g=arrays(folder/'grid.npz')
    active=f['active'];labels=g['vertida_id'].ravel()[g['occupied_flat_indices']]
    geo=geometry(folder);centers=np.asarray(geo['centers_m']);centroids=[]
    for pid in sorted(set(labels)):
        rows=np.flatnonzero(labels==pid);target=centers[rows].mean(axis=0);cell=int(rows[np.argmin(np.linalg.norm(centers[rows]-target,axis=1))])
        centroids.append(dict(name=f'Centro V{pid}',vertida_id=int(pid),occupied_index=cell,coordinate_m=centers[cell].tolist(),
                              weather_C=[float(v) if ok else None for v,ok in zip(f['weather_C'][:,cell],active[:,cell])],
                              constant_C=[float(v) if ok else None for v,ok in zip(f['constant_C'][:,cell],active[:,cell])]))
    stats={k:v.tolist() for k,v in a.items()}
    for name in ('weather','constant'):
        values=a[name+'_probe_temperature_C'];valid=a[name+'_probe_valid']
        stats[name+'_probe_temperature_C']=[[float(t) if ok else None for t,ok in zip(row,mask)] for row,mask in zip(values,valid)]
    times=f['times_s'];frames=[]
    for i,t in enumerate(times):
        stat=int(np.flatnonzero(a['weather_time_s']==t)[0]);by_pour=[]
        for pid in sorted(set(labels)):
            mask=(labels==pid)&active[i];values=f['weather_C'][i,mask]
            event=next(e for e in s['configuration']['physics']['events'] if e['pour_id']==pid)
            by_pour.append(dict(vertida_id=int(pid),active=bool(mask.any()),age_s=float(t-event['activation_s']) if mask.any() else None,
                                mean_C=float(values.mean()) if len(values) else None,max_C=float(values.max()) if len(values) else None))
        frames.append(dict(time_s=float(t),utc=iso_utc(utc_time(s['simulation_start_utc']).timestamp()+t),
                           active_cells=int(active[i].sum()),active_ids=[r['vertida_id'] for r in by_pour if r['active']],by_pour=by_pour,
                           probes={name:stats[name+'_probe_temperature_C'][stat] for name in ('weather','constant')}))
    low=min(float(f[name][active].min()) for name in ('weather_C','constant_C'));high=max(float(f[name][active].max()) for name in ('weather_C','constant_C'))
    diff=float(abs(f['weather_C'][active]-f['constant_C'][active]).max())
    return dict(summary=s,statistics=stats,frames=frames,centers=centroids,temperature_range_C=[low,high],difference_range_C=[-max(diff,1e-6),max(diff,1e-6)],
                limits=dict(Tmax_reference_C=70,deltaT_reference_C=20,meaning='Referencias docentes; no certifican seguridad de obra'),fields_sha256=digest(folder/'fields.npz'))


def verify_result(folder,vtk_folder):
    import pyvista as pv
    from .vtkio import check_vtk
    folder=Path(folder);s=read(folder/'summary.json');g=arrays(folder/'grid.npz');f=arrays(folder/'fields.npz');rows=read(Path(vtk_folder)/'manifest.json')['states']
    assert len(rows)>=3
    for row in rows:
        i=row['frame'];T=np.zeros(g['vertida_id'].size);active=np.zeros(T.size,dtype=bool)
        T[g['occupied_flat_indices']]=f['weather_C'][i];active[g['occupied_flat_indices']]=f['active'][i]
        grid=pv.read(Path(vtk_folder)/row['file']);check_vtk(grid,g['vertida_id'],g['origin_m'],g['spacing_m'],T.reshape(g['vertida_id'].shape),active.reshape(g['vertida_id'].shape))
    p=s['configuration']['physics'];labels=g['vertida_id'].ravel()[g['occupied_flat_indices']];capacity=np.zeros(len(labels))
    for e in p['events']:
        mat={**p['material'],**e.get('material',{})};capacity[labels==e['pour_id']]=np.prod(g['spacing_m'])*mat['rho']*mat['cp']
    balances={}
    for name in ('weather','constant'):
        steps=arrays(folder/(name+'_steps.npz'));T=f[name+'_C'];active=f['active']
        energy=[float(np.sum(capacity[active[i]]*(T[i,active[i]]-p['energy_reference_C']))) for i in (0,-1)]
        residual=energy[1]-energy[0]-steps['hydration_energy_J'].sum()+steps['outward_energy_J'].sum()-steps['placement_energy_J'].sum()
        balances[name]=dict(residual_reconstructed_J=float(residual),tolerance_J=s['energy'][name]['tolerance_J'])
        if abs(residual)>s['energy'][name]['tolerance_J']:raise ValueError('Balance energético de campos guardados no cierra')
        if np.max(abs(steps['balance_residual_J']))>s['energy'][name]['tolerance_J']:raise ValueError('Balance por paso no cierra')
    checks=dict(finite_fields=bool(np.isfinite(f['weather_C']).all() and np.isfinite(f['constant_C']).all()),vtk_exact=True,
                balances_reconstructed=True,solver_checks=all(all(v.values()) for v in s['checks'].values()),same_steps=s['same_time_steps'],
                snapshot=weather_data(s['configuration'])['status']=='PASS')
    if not all(checks.values()):raise ValueError('Falló una verificación del resultado')
    return dict(status='PASS',checks=checks,vtk_states=len(rows),balances=balances,fields_sha256=digest(folder/'fields.npz'))
