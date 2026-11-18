"""Verificar máximos desde todos los campos y S25 con fórmula independiente."""
from pathlib import Path
from dataclasses import replace
import hashlib,json
import numpy as np
from ..e11.pipeline import ROOT,write_json
from ..e11 import webdata
from ..e11.weather import window
from ..e07.voxel import VoxelGrid,Voxelization
from ..e07.faces import exposed_faces
from ..e08.inputs import events_from_config
from .pipeline import arrays
from .source import load_curve

def verify(folder,vtk_folder):
    folder=Path(folder);s=json.loads((folder/'summary.json').read_text(encoding='utf8'));c=s['configuration'];p=c['physics']
    base=webdata.verify_result(folder,vtk_folder);g=arrays(folder/'grid.npz');all_fields=arrays(folder/'all_steps.npz');stats=arrays(folder/'statistics.npz')
    times=all_fields['times_s'];T=all_fields['weather_C'];active=all_fields['active'];labels=g['vertida_id'][g['occupation_mask']];idx=np.argwhere(g['occupation_mask'])
    assert np.isfinite(T).all() and np.all(T[~active]==0) and np.all(np.diff(times)>0)
    assert times[0]==0 and times[-1]==p['t_end_s']
    births=np.array([next(e['activation_s'] for e in p['events'] if e['pour_id']==int(pid)) for pid in labels])
    np.testing.assert_array_equal(active,times[:,None]>=births)
    np.testing.assert_array_equal(times,stats['weather_time_s'])
    grid=VoxelGrid(tuple(g['origin_m']),tuple(g['spacing_m']),g['vertida_id'].shape)
    vox=Voxelization(grid,g['vertida_id'],{x['vertida_id']:x['guid'] for x in s['grid']['by_pour']},{x['vertida_id']:x['volume_reference_m3'] for x in s['grid']['by_pour']})
    weather=window(ROOT/c['snapshot'],c['simulation_start_utc'],p['t_end_s'])
    faces=None;old_active=None;maxval=-np.inf;maxdelta=-np.inf;peak=None;delta_peak=None;max_d25_error=0.
    recovered=[];face_values=[];boundary_values=[]
    capacities=np.array([np.prod(g['spacing_m'])*{**p['material'],**next(e.get('material',{}) for e in p['events'] if e['pour_id']==int(pid))}['rho']*{**p['material'],**next(e.get('material',{}) for e in p['events'] if e['pour_id']==int(pid))}['cp'] for pid in labels])
    for i,t in enumerate(times):
        live=np.zeros(g['vertida_id'].shape,dtype=bool);live[g['occupation_mask']]=active[i]
        full=np.zeros(live.shape);full[g['occupation_mask']]=T[i]
        if old_active is None or not np.array_equal(live,old_active):faces=exposed_faces(vox,live);old_active=live
        axis=faces.axis;half=g['spacing_m'][axis]/2
        k=np.array([{**p['material'],**next(e.get('material',{}) for e in p['events'] if e['pour_id']==int(pid))}['k'] for pid in faces.pour_id])
        cell=full[tuple(faces.indices.T)];e=c['environment'];ground=(axis==2)&(faces.sign==-1)&(faces.indices[:,2]==0)
        R=half/k+1/e['air']['h_still_W_m2K']
        if t<e['formwork']['remove_at_s']:
            covered=np.zeros(len(axis),dtype=bool)
            for face in e['formwork']['orientations']:covered|=(axis=='xyz'.index(face[0]))&(faces.sign==(-1 if face[1]=='-' else 1))
            covered&=(faces.classification!='future_pour')&~ground
            R[covered]+=sum(layer['thickness_m']/layer['conductivity_W_mK'] for layer in e['formwork']['layers'])
        q=(cell-weather.at(t).air_C)/R
        soil=e['soil']
        q[ground]=0 if soil['adiabatic'] else (cell[ground]-soil['temperature_C'])/(half[ground]/k[ground]+soil['depth_m']/soil['conductivity_W_mK']+soil['contact_m2K_W'])
        near=cell-q*(half-c['evaluation']['depth_m'])/k
        hi=float(T[i,active[i]].max());lo=float(near.min());delta=hi-lo
        recovered.append(delta);face_values.append(float((cell-q*half/k).min()));boundary_values.append(float(cell.min()))
        max_d25_error=max(max_d25_error,abs(delta-stats['weather_delta25_C'][i]))
        if hi>maxval:
            maxval=hi;column=int(np.argmax(np.where(active[i],T[i],-np.inf)));peak=dict(time_s=float(t),occupied_index=column,index=idx[column].tolist())
        if delta>maxdelta:
            maxdelta=delta;j=int(np.argmin(near));cold=faces.indices[j];xyz=g['origin_m']+(cold+.5)*g['spacing_m'];xyz[axis[j]]+=faces.sign[j]*(half[j]-c['evaluation']['depth_m'])
            delta_peak=dict(time_s=float(t),cold_index=cold.tolist(),cold_coordinate_m=xyz.tolist(),cold_temperature_C=float(near[j]))
    assert maxval==s['global_maximum']['temperature_C'] and peak['time_s']==s['global_maximum']['time_s']
    assert maxdelta==s['global_delta25_maximum']['value_C'] and delta_peak['time_s']==s['global_delta25_maximum']['time_s']
    np.testing.assert_allclose(delta_peak['cold_coordinate_m'],s['global_delta25_maximum']['cold']['coordinate_m'],rtol=0,atol=1e-12)
    np.testing.assert_allclose(recovered,stats['weather_delta25_C'],rtol=0,atol=1e-10)
    for event in p['events']:
        i=int(np.flatnonzero(times==event['activation_s'])[0]);mask=labels==event['pour_id'];np.testing.assert_array_equal(T[i,mask],np.full(mask.sum(),event['initial_C']))
    curve,source=load_curve(ROOT/c['experimental_source']['file'],c['experimental_source']['curve'],c['experimental_source']['tail'],c['experimental_source'].get('tau_s',86400.))
    steps=arrays(folder/'weather_steps.npz');pred=np.zeros(len(steps['start_s']))
    for event in p['events']:
        volume=float((labels==event['pour_id']).sum()*np.prod(g['spacing_m']))
        pred+=volume*curve.released(steps['start_s']-event['activation_s'],steps['end_s']-event['activation_s'])
    np.testing.assert_allclose(pred,steps['hydration_energy_J'],rtol=2e-12,atol=1e-5)
    sensible=np.sum(capacities[active[-1]]*(T[-1,active[-1]]-p['energy_reference_C']))
    expected=sum(float((labels==e['pour_id']).sum()*np.prod(g['spacing_m']))*float(curve.released(0,max(0,p['t_end_s']-e['activation_s']))) for e in p['events'])
    assert abs(steps['hydration_energy_J'].sum()-expected)<.01  # todas las edades > cola del registro
    return dict(status='PASS',base_checks=base,all_time_fields=len(times),global_Tmax_C=maxval,global_delta25_C=maxdelta,peak=peak,delta_peak=delta_peak,
                max_reconstructed_delta_error_C=max_d25_error,energy_reconstructed_final_J=float(sensible),hydration_predicted_J=float(pred.sum()),
                source_integral_MJ_m3=source['selected_total_MJ_m3'],S25_reference_variation=dict(face0mm_max_delta_C=float(np.max(stats['weather_Tmax_C']-face_values)),
                        boundary_cell_center_max_delta_C=float(np.max(stats['weather_Tmax_C']-boundary_values)),depth25mm_max_delta_C=maxdelta),
                source_hash=source['sha256'],dataset_coverage=weather.coverage(),same_units=True,one_sided_events='Se conservan límites izquierdos nextafter(t,-∞) y valores exactos posteriores; sin alterar pasos del solver',
                limitations='Verificación numérica del modelo; S25 es aproximación lineal bajo frontera staircase, no validación experimental')

