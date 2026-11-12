"""Mismo integrador E10: clima variable frente a control constante en igual grilla."""
from copy import deepcopy
import hashlib,json,time
from pathlib import Path
import numpy as np
from ..e07.ifc import read_pours
from ..e07.voxel import voxelize
from ..e07.coupling import MaskedAssembly
from ..e08.inputs import validate_config,events_from_config
from ..e08.solver import simulate
from ..e09.analysis import select_probes
from ..e10.weather import WeatherSample
from ..e10.boundaries import Air,Soil,Formwork,Layer,Environment
from .weather import window,iso_utc
ROOT=Path(__file__).resolve().parents[3]


def write_json(path,data):
    def scalar(value):
        if isinstance(value,np.generic):return value.item()
        raise TypeError('Tipo JSON no admitido: '+type(value).__name__)
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False,default=scalar)+'\n',encoding='utf-8')


class ConstantWeather:
    def __init__(self,original,temperature):
        if not np.isfinite(temperature) or temperature<=-273.15:raise ValueError('Ambiente constante físico')
        self.original=original;self.temperature=temperature;self.change_times_s=original.change_times_s
    def at(self,t):
        self.original.at(t)  # También exige cobertura real y límites temporales.
        return WeatherSample(self.temperature,0.,0.,'constant_reference')


def make_environment(voxels,weather,cfg):
    if cfg['air']['h_wind_per_m_s']!=0 or cfg['air']['solar_absorptivity']!=0:raise ValueError('Baseline E11 no usa viento ni radiación')
    mold=cfg['formwork']
    return Environment(voxels,weather,Air(**cfg['air']),Soil(**cfg['soil']),
        Formwork(tuple(mold['orientations']),mold['remove_at_s'],tuple(Layer(**x) for x in mold['layers'])))


class Recorder:
    def __init__(self,voxels,events,environment,target):
        self.voxels=voxels;self.environment=environment;self.materials={e.pour_id:e.material for e in events}
        self.probes=select_probes(voxels,target)[:3];self.assembly=None;self.rows=[];self.valid=[];self.peak=None
    def __call__(self,t,T,active):
        if self.assembly is None or not np.array_equal(active,self.assembly.active):
            self.assembly=MaskedAssembly(self.voxels,active,self.materials)
        a=self.assembly;self.environment(a,t)
        vals=T[active];point_values=[];valid=[]
        for p in self.probes:
            key=tuple(p['index']);ok=bool(active[key]);value=0.
            if ok:
                value=float(T[key])
                if p['kind']=='reconstructed_face':
                    axis='xyz'.index(p['face'][0]);sign=1 if p['face'][1]=='+' else -1
                    rows=np.flatnonzero(np.all(a.faces.indices==p['index'],axis=1)&(a.faces.axis==axis)&(a.faces.sign==sign))
                    ok=bool(len(rows))
                    if ok:
                        j=rows[0];q=(a.face_g[j]*(T[key]-a.reservoir[j])+a.prescribed[j])/a.faces.areas[j]
                        value=float(T[key]-q*p['half_cell_m']/self.materials[p['vertida_id']].k)
            point_values.append(value if ok else 0.);valid.append(ok)
        maximum=float(vals.max()) if len(vals) else 0.
        self.rows.append([t,self.environment.weather.at(t).air_C,maximum,float(vals.min()) if len(vals) else 0.,
                          float(vals.mean()) if len(vals) else 0.,*point_values])
        self.valid.append(valid)
        if len(vals) and (self.peak is None or maximum>self.peak['temperature_C']):
            index=np.unravel_index(np.argmax(np.where(active,T,-np.inf)),active.shape)
            self.peak=dict(temperature_C=maximum,time_h=t/3600,index=list(map(int,index)),
                           coordinate_m=(np.array(self.voxels.grid.origin)+(np.array(index)+.5)*self.voxels.grid.spacing).tolist(),
                           vertida_id=int(self.voxels.vertida_id[index]))
    def arrays(self):
        r=np.asarray(self.rows)
        return dict(time_s=r[:,0],ambient_C=r[:,1],Tmax_C=r[:,2],Tmin_C=r[:,3],Tmean_C=r[:,4],
                    probe_temperature_C=r[:,5:],probe_valid=np.asarray(self.valid,dtype=bool))


def run(config,output,*,plots=True,export=True,vtk_dir=None,figure_dir=None):
    start=time.perf_counter();cfg=deepcopy(config);output=Path(output).resolve()
    if not output.is_relative_to(ROOT) or output.exists():raise ValueError('Elegir destino nuevo dentro de E11')
    if any(path is not None and not Path(path).resolve().is_relative_to(ROOT) for path in (vtk_dir,figure_dir)):raise ValueError('Artefactos dentro de E11')
    ifc=(ROOT/cfg['ifc']).resolve();snapshot=(ROOT/cfg['snapshot']).resolve()
    if not ifc.is_relative_to(ROOT) or not snapshot.is_relative_to(ROOT):raise ValueError('Inputs dentro de E11')
    solids,meta=read_pours(ifc);p=validate_config(cfg['physics'],solids)
    if p['t_end_s']<=0:raise ValueError('Duración positiva')
    p['save_interval_s']=min(p['save_interval_s'],p['t_end_s']/2);cfg['physics']=p
    weather=window(snapshot,cfg['simulation_start_utc'],p['t_end_s'])
    vox=voxelize(solids,p['spacing_m'],margin=p['margin_m']);events=events_from_config(p)
    solutions={};records={}
    for name,w in [('weather',weather),('constant',ConstantWeather(weather,cfg['constant_reference_C']))]:
        env=make_environment(vox,w,cfg['environment']);record=Recorder(vox,events,env,cfg['core_target_m'])
        print('E11 '+name+f": {vox.occupation_mask.sum()} celdas, {p['t_end_s']/3600:g} h",flush=True)
        solutions[name]=simulate(vox,events,t_end_s=p['t_end_s'],max_step_s=p['max_step_s'],save_interval_s=p['save_interval_s'],
                                safety=p['safety'],energy_reference_C=p['energy_reference_C'],observer=record,
                                boundary_update=env,boundary_change_times_s=env.change_times_s)
        records[name]=record
    a,b=solutions['weather'],solutions['constant']
    if [r['dt_s'] for r in a.steps]!=[r['dt_s'] for r in b.steps]:raise ValueError('La comparación requiere mismos pasos')
    output.mkdir(parents=True)
    labels=vox.vertida_id[vox.occupation_mask]
    births=np.array([next(e.activation_s for e in events if e.pour_id==int(pid)) for pid in labels])
    active=a.times_s[:,None]>=births
    np.savez_compressed(output/'grid.npz',vertida_id=vox.vertida_id,occupation_mask=vox.occupation_mask,
        origin_m=vox.grid.origin,spacing_m=vox.grid.spacing,occupied_flat_indices=np.flatnonzero(vox.occupation_mask))
    np.savez_compressed(output/'fields.npz',times_s=a.times_s,active=active,
        weather_C=np.where(active,a.temperature_C,0.),constant_C=np.where(active,b.temperature_C,0.))
    stats={}
    for name in solutions:
        stats.update({name+'_'+k:v for k,v in records[name].arrays().items()})
        np.savez_compressed(output/(name+'_steps.npz'),**{k:np.array([r[k] if r[k] is not None else 0. for r in solutions[name].steps]) for k in solutions[name].steps[0]})
    np.savez_compressed(output/'statistics.npz',**stats)
    x=records['weather'].arrays();y=records['constant'].arrays();both=x['probe_valid'][:,0]&x['probe_valid'][:,1]
    dx=x['probe_temperature_C'][:,0]-x['probe_temperature_C'][:,1];dy=y['probe_temperature_C'][:,0]-y['probe_temperature_C'][:,1]
    report=dict(status='PASS',configuration=cfg,simulation_start_utc=iso_utc(weather.start),simulation_end_utc=iso_utc(weather.start+p['t_end_s']),
        coverage=weather.coverage(),weather_metadata=weather.snapshot.metadata,ifc_sha256=hashlib.sha256(ifc.read_bytes()).hexdigest(),
        grid=vox.report(),probes=records['weather'].probes,peaks={name:records[name].peak for name in records},
        energy={name:solutions[name].energy for name in solutions},checks={name:solutions[name].checks for name in solutions},
        comparison=dict(final_field_Linf_C=float(np.max(abs(a.temperature_C[-1,active[-1]]-b.temperature_C[-1,active[-1]]))) if active[-1].any() else None,
            Tmax_max_difference_C=float(np.max(abs(x['Tmax_C']-y['Tmax_C']))),
            final_core_C={name:float(records[name].arrays()['probe_temperature_C'][-1,0]) if records[name].arrays()['probe_valid'][-1,0] else None for name in records},
            final_top_face_C={name:float(records[name].arrays()['probe_temperature_C'][-1,1]) if records[name].arrays()['probe_valid'][-1,1] else None for name in records},
            max_core_top_difference_C=dict(weather=float(dx[both].max()),constant=float(dy[both].max())) if both.any() else {},
            outward_energy_difference_J=a.energy['outward_J']-b.energy['outward_J']),
        same_time_steps=True,activation_events=a.events,saved_frames=len(a.times_s),steps=len(a.steps),
        assumption='Temperatura meteorológica variable y h constante; sin viento ni radiación explícitos. Suelo resistivo y moldaje E10 declarados; sin calibración de obra.',
        storage='Campos [frame, occupied C-order]; ceros solo como relleno junto a active. Probes son núcleo en centro y temperatura de cara de hormigón reconstruida Tc-q_out*R_half.',
        source_sha256={f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((ROOT/'src').rglob('*.py'))},
        elapsed_s=time.perf_counter()-start)
    write_json(output/'inputs.json',cfg);write_json(output/'summary.json',report)
    if export:
        from .vtkio import export_result
        report['vtk']=export_result(output,vtk_dir or ROOT/'vtk/e11',cfg['export_hours'])
    if plots:
        from .plots import make_plots
        report['figures']=make_plots(output,figure_dir or ROOT/'figures')
    write_json(output/'summary.json',report)
    return report
