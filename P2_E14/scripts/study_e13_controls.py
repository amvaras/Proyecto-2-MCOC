"""Controles dirigidos: áreas, malla, paso, cola, capacidad y lumping; mismo solver."""
from copy import deepcopy
from pathlib import Path
import json
import numpy as np
from mcoc_p2.e11.pipeline import ROOT,write_json
from mcoc_p2.e13.weather import read,member_payload,validate_snapshot
from mcoc_p2.e13.evaluator import Evaluator,CaseRecorder
from mcoc_p2.e13.plans import make_plan
from mcoc_p2.e13.risk import scenarios,probability
from mcoc_p2.e07.faces import exposed_faces
from mcoc_p2.e07.voxel import Voxelization
from mcoc_p2.e07.construction import PourEvent
from mcoc_p2.e08.solver import simulate
from mcoc_p2.e11.pipeline import make_environment
from mcoc_p2.e11.weather import window,normalized_bytes
from mcoc_p2.e10.weather import save_snapshot,Snapshot
from mcoc_p2.e12.source import load_curve
from mcoc_p2 import Material
def area_reference(ev,vox):
    total=contact=0.;base=None;previous=None
    for solid in ev.solids:
        tri=solid.mesh.tri;area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
        bottom=np.all(abs(tri[:,:,2]-solid.mesh.low[2])<1e-8,axis=1);b=float(area[bottom].sum())
        if base is None:base=b
        if previous is not None:
            assert abs(previous.mesh.high[2]-solid.mesh.low[2])<1e-8 and previous.mesh.convex
            assert np.all(previous.mesh.classify(tri[bottom].reshape(-1,3))>=0);contact+=b
        total+=float(area.sum());previous=solid
    actual=total-2*contact;faces=exposed_faces(vox);ground=(faces.axis==2)&(faces.sign==-1)&(faces.indices[:,2]==0)
    voxel_ground=float(faces.areas[ground].sum());voxel_air=float(faces.areas[~ground].sum())
    return dict(IFC_exterior_m2=actual,voxel_exterior_m2=voxel_ground+voxel_air,bias=(voxel_ground+voxel_air)/actual-1,
       air_factor=(actual-base)/voxel_air,ground_factor=base/voxel_ground,
       meaning='Sensibilidad global por área aire/suelo, sin corregir posiciones S25; no es cut-cell ni solución geométricamente exacta. Caras frente a futuras sin reescalar.')
def make_member(member):
    from datetime import datetime
    import hashlib
    raw=read(ROOT/'data/ensemble/raw.json');meta=read(ROOT/'data/ensemble/metadata.json');payload=member_payload(raw,member)
    b=(json.dumps(payload,separators=(',',':'),ensure_ascii=False)+'\n').encode()
    target=ROOT/'data/weather'/f"forecast-{datetime.fromisoformat(meta['retrieved_at_utc']):%Y%m%dT%H%M%S%fZ}-{hashlib.sha256(b).hexdigest()[:12]}"
    if target.exists():return target.relative_to(ROOT).as_posix()
    target=save_snapshot(ROOT/'data/weather',b,source='Open-Meteo',kind='forecast',model='gfs05',latitude=meta['latitude'],longitude=meta['longitude'],url=meta['request_url'],retrieved_at=datetime.fromisoformat(meta['retrieved_at_utc']))
    snap=Snapshot.load(target);csv=normalized_bytes(snap);(target/'temperature.csv').write_bytes(csv);m=snap.metadata
    m.update(e11_schema=1,e13_ensemble_member=member,ensemble_parent='data/ensemble/raw.json',ensemble_parent_sha256=meta['raw_sha256'],normalized_sha256=hashlib.sha256(csv).hexdigest(),interval_s=3600,provider_elevation_m=payload.get('elevation'),provider_model_version=None,representativeness=meta['caveat'],license_url=meta['license'],role='Control de miembro omitido; no se añade peso a la distribución oficial')
    write_json(target/'metadata.json',m);validate_snapshot(target);return target.relative_to(ROOT).as_posix()
def main():
    cfg=read(ROOT/'configs/e13/study.json');report=read(ROOT/'results/e13/summary.json');ev=Evaluator();sc=scenarios(read(ROOT/'data/ensemble/reduction.json'));control=next(s for s in sc if s['curve']=='M4_SS' and s['member']==0)
    target=ROOT/'results/verification/controls.json'
    if target.exists():raise ValueError('Preservar controles existentes')
    result=dict(status='RUNNING',area_reference=area_reference(ev,ev.grid(cfg['spacing_m'])),cases=[],weight_sensitivity=[],capacity_admissibility=[])
    def case(label,p,s=control,**kw):
        row,arrays,record,solution=ev.case(p,s,**kw);row['control']=label;result['cases'].append(row);write_json(target,result)
        print(label,p['id'],s['id'],f"T={row['Tmax_C']:.4f}, delta={row['delta_C']:.4f}, {row['elapsed_s']:.1f} s",flush=True)
        return row,arrays,record,solution
    f=result['area_reference'];factors=[f['air_factor'],f['ground_factor']]
    for p in cfg['plans']:
        case('fine_mesh',p,spacing=[.3,.3,.055])
        case('area_rescale',p,area_factors=factors)
    chosen=next(p for p in cfg['plans'] if p['id']==report['illustrative_plan'])
    case('half_dt',chosen,max_step_s=450)
    for tau in (12,48):
        s=deepcopy(next(s for s in sc if s['curve']=='M1_SS' and s['member']==0));s.update(tau_h=tau);case('tail_tau_'+str(tau),chosen,s)
    for rate in (45,60):
        for old in cfg['plans']:
            wait=0.5 if old['id']=='protegido_rapido' else 6 if old['id']=='propuesto_6h' else 12
            try:p=make_plan(old['id'],ev.volumes,rate,wait_h=wait,single=old['partition']=='single',baseline=old['id']=='E12_referencia',initial_C=old['initial_C'][0],protected=old['protected'])
            except ValueError as exc:result['capacity_admissibility'].append(dict(rate_m3_h=rate,plan=old['id'],admissible=False,reason=str(exc)));continue
            result['capacity_admissibility'].append(dict(rate_m3_h=rate,plan=old['id'],admissible=True,D_h=p['D_h']));case('capacity_'+str(rate),p)
    for rule in ('midpoint','finish'):
        p=deepcopy(cfg['plans'][0]);p['activation_rule']=rule;case('single_lumping_'+rule,p)
    # Comprobar en la fundación real la equivalencia de las cinco regiones
    # simultáneas con una única etiqueta; no modificar el IFC original.
    row,a,rec,sol=case('single_union_reference',cfg['plans'][0])
    vox=ev.grid(cfg['spacing_m']);union=Voxelization(vox.grid,np.where(vox.occupation_mask,1,0).astype(np.uint16),{1:'computational-union'},{1:sum(ev.volumes)})
    curve,_=load_curve(ROOT/'data/hydration/source_terms.txt',control['curve'],tail='exponential');mat=Material(**ev.base['physics']['material']);events=[PourEvent(1,0,20,mat,curve)]
    w=window(ROOT/control['snapshot'],cfg['start_utc'],408*3600);env=make_environment(union,w,ev.base['environment']);r=CaseRecorder(union,events,env,ev.base['core_target_m'])
    other=simulate(union,events,t_end_s=408*3600,max_step_s=900,save_interval_s=43200,safety=.8,energy_reference_C=20,observer=r,boundary_update=env,boundary_change_times_s=env.change_times_s)
    np.testing.assert_array_equal(sol.temperature_C,other.temperature_C);np.testing.assert_array_equal(sol.times_s,other.times_s)
    result['single_union']=dict(status='PASS',field_Linf_C=0.,all_saved_fields_equal=True,Tmax_C=r.peak['temperature_C'],delta_C=r.delta_peak['value_C'],interpretation='Misma edad/material/fuente en cinco regiones simultáneas, contactos perfectos y sin convección interna; igualdad con la unión de etiquetas')
    # Miembros excluidos: extremos de media temporal y más alejados por cluster,
    # elegidos por meteorología, no por respuesta térmica del hormigón.
    raw=read(ROOT/'data/ensemble/raw.json');red=read(ROOT/'data/ensemble/reduction.json');series=np.array([member_payload(raw,i)['hourly']['temperature_2m'] for i in range(31)])
    from mcoc_p2.e10.weather import utc_time
    t=np.array(member_payload(raw,0)['hourly']['time']);mask=(t>=utc_time(cfg['start_utc']).timestamp())&(t<=utc_time(cfg['start_utc']).timestamp()+408*3600);series=series[:,mask]
    assigned=np.array(red['assignment']);omitted={int(np.argmin(series.mean(axis=1))),int(np.argmax(series.mean(axis=1)))}
    for j,m in enumerate(red['medoids']):
        candidates=np.flatnonzero(assigned==j);omitted.add(int(candidates[np.argmax(np.mean((series[candidates]-series[m])**2,axis=1))]))
    omitted-=set(red['medoids']);result['omitted_members']=sorted(omitted)
    for m in sorted(omitted):
        s=deepcopy(control);s.update(id=f'M4_SS_omitted_m{m:02d}',member=m,snapshot=make_member(m),weight=0,climate_weight=0);case('omitted_weather',chosen,s)
    rows=read(ROOT/'results/e13/cases.json')
    for label,pm in [('uniform_eight',[.125]*8),('SS_only',[.25]*4+[0.]*4),('22A_only',[0.]*4+[.25]*4)]:
        alt=scenarios(red,pm);w={s['id']:s['weight'] for s in alt}
        for p in cfg['plans']:
            rs=[x for x in rows if x['plan']==p['id']];result['weight_sensitivity'].append(dict(model=label,plan=p['id'],**probability(rs,[w[x['scenario']] for x in rs])))
    result['status']='PASS';result['decision_controls']=[]
    for label in ('fine_mesh','area_rescale'):
        for p in cfg['plans']:
            row=next(x for x in result['cases'] if x['control']==label and x['plan']==p['id']);lower=control['weight'] if row['Tmax_C']>70 or row['delta_C']>20 else 0.
            result['decision_controls'].append(dict(control=label,plan=p['id'],P_joint_lower_bound=lower,proves_infeasible=lower>.05,meaning='Una excedencia con peso 0.2×15/31 ya supera 5%; no requiere estimar el resto como si estuviese verificado'))
    write_json(target,result)
if __name__=='__main__':main()
