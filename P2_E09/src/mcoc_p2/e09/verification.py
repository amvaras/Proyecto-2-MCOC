"""Auditoría independiente de artefactos: máscaras, energía, máximos y figuras."""
import hashlib,json,math
from pathlib import Path
import numpy as np
from PIL import Image


def validate_saved_result(folder,root):
    folder=Path(folder).resolve();root=Path(root).resolve()
    s=json.loads((folder/'summary.json').read_text(encoding='utf-8'))
    cfg=s['configuration']['physics'];inputs=json.loads((folder/'inputs.json').read_text(encoding='utf-8'))
    if inputs!=s['configuration']:raise ValueError('Inputs guardados diferentes del reporte')
    with np.load(folder/'temperature.npz') as z:d={k:z[k] for k in z.files}
    with np.load(folder/'grid.npz') as z:g={k:z[k] for k in z.files}
    with np.load(folder/'statistics.npz') as z:a={k:z[k] for k in z.files}
    with np.load(folder/'steps.npz') as z:steps={k:z[k] for k in z.files}
    checks=dict(solver_checks=all(s['checks'].values()),finite_artifacts=all(np.isfinite(v).all() for table in (d,g,a,steps) for v in table.values()),
        ifc_unchanged=hashlib.sha256((root/s['ifc']['relative_path']).read_bytes()).hexdigest()==s['ifc']['sha256'])
    ids=g['vertida_id'][g['occupation_mask']]
    checks['occupied_indexing']=bool(np.array_equal(g['occupied_flat_indices'],np.flatnonzero(g['occupation_mask'])))
    events={e['pour_id']:e for e in cfg['events']}
    birth=np.array([events[int(pid)]['activation_s'] for pid in ids])
    checks['active_schedule']=bool(np.array_equal(d['active_mask'],d['times_s'][:,None]>=birth[None,:]))
    checks['inactive_zero_fill']=bool(np.all(d['temperature_C'][~d['active_mask']]==0))
    checks['duration_exact']=d['times_s'][-1]==cfg['t_end_s'] and steps['end_s'][-1]==cfg['t_end_s']
    checks['event_times']=all(e['activation_s'] in d['times_s'] for e in events.values() if e['activation_s']<=cfg['t_end_s'])
    checks['stable_steps']=bool(np.all(steps['dt_over_limit']<=cfg['safety']*(1+1e-12)))
    checks['time_continuity']=bool(np.array_equal(steps['start_s'][1:],steps['end_s'][:-1]) and np.all(steps['dt_s']>0))
    checks['statistics_every_step']=len(a['time_s'])==len(steps['end_s'])+1 and bool(np.array_equal(a['time_s'][1:],steps['end_s']))
    capacity=np.zeros(len(ids));expected_heat=0.
    volume=float(np.prod(g['spacing_m']))
    for pid,e in events.items():
        mat={**cfg['material'],**e.get('material',{})};curve={**cfg['hydration'],**e.get('hydration',{})}
        select=ids==pid;capacity[select]=mat['rho']*mat['cp']*volume
        age=np.clip((cfg['t_end_s']-e['activation_s'])/curve['duration_s'],0,1)
        expected_heat+=select.sum()*volume*curve['H_vol_J_m3']*(1-math.cos(math.pi*float(age)))/2
    def energy(frame):
        active=d['active_mask'][frame]
        return float(np.sum(capacity[active]*(d['temperature_C'][frame,active]-cfg['energy_reference_C'])))
    initial,final=energy(0),energy(-1)
    residual=final-initial-steps['hydration_energy_J'].sum()+steps['outward_energy_J'].sum()-steps['placement_energy_J'].sum()
    checks['reconstructed_energy_balance']=abs(residual)<=s['energy']['tolerance_J']
    checks['reconstructed_final_energy']=math.isclose(final,s['energy']['final_J'],rel_tol=1e-13,abs_tol=1e-5)
    checks['heat_potential_independent']=math.isclose(float(steps['hydration_energy_J'].sum()),expected_heat,rel_tol=1e-11,abs_tol=1e-6)
    checks['stages_balance']=all(abs(stage['balance_residual_J'])<=s['energy']['tolerance_J'] for stage in s['stages'])
    checks['field_statistics']=True
    for frame,t in enumerate(d['times_s']):
        row=int(np.argmin(abs(a['time_s']-t)));mask=d['active_mask'][frame];values=d['temperature_C'][frame,mask]
        if values.size:
            checks['field_statistics'] &= bool(a['time_s'][row]==t and abs(a['Tmax_C'][row]-values.max())<1e-12 and abs(a['Tmin_C'][row]-values.min())<1e-12 and abs(a['Tmean_C'][row]-values.mean())<1e-12)
    j=int(np.argmax(a['Tmax_C']))
    checks['peak_from_steps']=bool(a['Tmax_C'][j]==s['thermal']['peak']['temperature_C'] and a['time_s'][j]/3600==s['thermal']['peak']['time_h'])
    active=a['probe_valid'][:,0]&a['probe_valid'][:,1]
    delta=a['probe_temperature_C'][:,0]-a['probe_temperature_C'][:,1]
    checks['delta_from_probes']=math.isclose(float(delta[active].max()),s['thermal']['center_top_difference']['maximum_C'],rel_tol=0,abs_tol=1e-12)
    manifest=json.loads((folder/'figure_manifest.json').read_text(encoding='utf-8'))
    field_sha=hashlib.sha256((folder/'temperature.npz').read_bytes()).hexdigest()
    checks['figure_source']=manifest['field_sha256']==field_sha
    figs=(folder/manifest['figure_directory']).resolve()
    checks['figures_in_delivery']=figs.is_relative_to(root);checks['figures_intact']=True
    for name,row in manifest['files'].items():
        path=figs/name
        checks['figures_intact'] &= hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
        with Image.open(path) as image:
            checks['figures_intact'] &= image.width>100 and image.height>100
            if path.suffix=='.png':checks['figures_intact'] &= field_sha in image.info.get('Description','')
    checks['panel_times_real']=all(d['times_s'][j]/3600==t for j,t in zip(manifest['panel_frames'],manifest['panel_times_h']))
    if (folder/'control.npz').exists():
        with np.load(folder/'control.npz') as z:
            checks['control_maximum_principle']=float(z['Tmax_C'].max())<=max(cfg['ambient_C'],*[e['initial_C'] for e in cfg['events']])+1e-10
    if not all(checks.values()):raise ValueError('Auditoría de datos: '+str({k:v for k,v in checks.items() if not v}))
    return dict(status='PASS',checks={k:bool(v) for k,v in checks.items()},reconstructed_balance_J=float(residual),
                expected_hydration_J=float(expected_heat),field_sha256=field_sha,figures=len(manifest['files']))
