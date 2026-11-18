"""Recheck F02 numerical evidence without a simulation or network call."""
import argparse
import csv
import io
import hashlib
import math
from pathlib import Path

import numpy as np

from mcoc_p2.e07.ifc import read_pours
from mcoc_p2.e11.weather import window
from mcoc_p2.e14.io import ROOT, read, write
from mcoc_p2.e14.model import catalog
from mcoc_p2.f02.study import configuration
from run_f02 import code_version, summarize

root = ROOT
solids = {p.pour_id:p.mesh for p in read_pours(root/'geometry/foundation.ifc')[0]}

def check(r):
    metrics=r['delta_peak']; cold=metrics['cold']; cfg=r['configuration']; env=cfg['environment'];t=metrics['time_s']
    point=np.array(cold['coordinate_m']); face=np.array(cold['face_coordinate_m'])
    solid=solids[cold['vertida_id']]
    axis='xyz'.index(cold['face'][0]); direction=1 if cold['face'][1]=='+' else -1
    center=face.copy(); half=cfg['physics']['spacing_m'][axis]/2; center[axis]-=half*direction
    facing=solid.normals[:,axis]*direction>1e-6
    distance=solid.offsets-solid.normals@center
    plane=np.argmin(np.where(facing,distance/np.where(facing,solid.normals[:,axis]*direction,1),np.inf))
    true=solid.normals[plane]
    true_face=center+distance[plane]*true
    true_s25=true_face-.025*true
    all_depth=solid.offsets-solid.normals@true_s25
    ray_dist=distance[plane]/(solid.normals[plane,axis]*direction)
    if ray_dist<0 or cold['classification']=='future_pour':
        return dict(in_applicable_surface=False)
    expected=max(0.,all_depth.min())
    projected_valid=all_depth.min() >= -1e-9 and abs(all_depth[plane]-.025)<1e-9
    k=cfg['physics']['material']['k']
    ground=axis==2 and direction==-1 and abs(face[2])<1e-9
    if ground:
        soil=env['soil']; temp=soil['temperature_C']; resistance=soil['depth_m']/soil['conductivity_W_mK']+soil['contact_m2K_W']
    else:
        temp=window(root/cfg['snapshot'],cfg['simulation_start_utc'],cfg['physics']['t_end_s']).at(t).air_C
        resistance=1/env['air']['h_still_W_m2K']
        if t<env['formwork']['remove_at_s'] and cold['face'] in env['formwork']['orientations']:
            layers=env['formwork']['layers']; thickness=layers[-1]['thickness_m']
            for h,v in configuration()['insulation_stages_h_m']:
                if t>=h*3600:thickness=v
            resistance+=layers[0]['thickness_m']/layers[0]['conductivity_W_mK']+thickness/layers[-1]['conductivity_W_mK']
    q=(cold['temperature_C']-temp)/(resistance+.025/k)
    tc=cold['temperature_C']+q*(half-.025)/k
    q_true=(tc-temp)/(resistance+distance[plane]/k)
    trueC=tc-q_true*(distance[plane]-.025)/k
    return dict(in_applicable_surface=True,projected_inside=bool(projected_valid),official_xyz=point.tolist(),
                projected_xyz=true_s25.tolist(),nearest_depth_mm=float(1000*expected),
                intended_depth_mm=float(1000*all_depth[plane]),q_W_m2=q,
                nominal_delta_C=r['delta_C'],local_projected_delta_C=float(metrics['hot_temperature_C']-trueC))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'results/f02')
    args=parser.parse_args()
    folder=args.output.resolve()
    nominal=read(folder/'enumeration.json')
    controls=read(folder/'controls.json')
    fields=folder/'fields.npz'
    expected=read(ROOT/'configs/f02/experimental_reference.json')
    weights={s['id']:s['weight'] for s in catalog()}
    if nominal['kernel_sha256']!=controls['kernel_sha256'] or nominal['kernel_sha256']!=code_version():
        raise ValueError('Los resultados no corresponden a este kernel/configuración')
    if hashlib.sha256(fields.read_bytes()).hexdigest()!=nominal['fields_sha256']:
        raise ValueError('Hash de campos F02 incorrecto')
    rows=nominal['rows']
    assert len(rows)==24 and {r['scenario']:r['weight'] for r in rows}==weights
    assert summarize(rows)==nominal['summary']
    assert math.isclose(math.fsum(weights.values()),1.,abs_tol=1e-15)
    comparisons=[]
    for mode, cases in [('nominal',rows),('controls',controls['rows'])]:
        for r in cases:
            p=r['configuration']['physics']
            lookup=expected['nominal'] if mode=='nominal' else expected['controls'][str(p['max_step_s'])+'-'+str(p['spacing_m'][0])]
            error=max(abs(a-b) for a,b in zip((r['Tmax_C'],r['delta_C']),lookup[r['scenario']],strict=True))
            assert error<=1e-8 and all(r['checks'].values())
            assert r['weight']==weights[r['scenario']] and not r['fail_joint']
            assert r['coverage']['covered_hours']==744 and r['coverage']['tail_hours']==0
            assert r['energy']['cooling_J']>0
            comparisons.append(dict(mode=mode,scenario=r['scenario'],spacing_m=p['spacing_m'],
                                    step_s=p['max_step_s'],Tmax_C=r['Tmax_C'],delta_C=r['delta_C'],
                                    balance_residual_J=r['energy']['residual_J'], error_C=error,
                                    nominal_S25_depth_IFC_m=r['S25_depth_IFC_m'],S25_projection=check(r)))
    representative=next(r for r in rows if r['scenario']==nominal['configuration']['scenario_3d'])
    with np.load(fields,allow_pickle=False) as package:
        times=package['times_s']
        expected_shape=(len(times),len(package['labels']))
        assert package['temperature_C'].shape==expected_shape
        assert times[0]==0 and times[-1]==744*3600 and np.all(np.diff(times)>0)
        for peak in ('peak','delta_peak'):
            pos=int(np.flatnonzero(times==representative[peak]['time_s'])[0])
            cap=representative[peak].get('temperature_C',representative[peak].get('hot_temperature_C'))
            assert np.isclose(package['temperature_C'][pos].max(),cap,atol=4e-6,rtol=0)
        assert abs(package['stats_delta_C'].max()-representative['delta_C'])<1e-12
    control_max=max(r['delta_C'] for r in controls['rows'])
    report=dict(status='PASS',kernel_sha256=nominal['kernel_sha256'],summary=nominal['summary'],
                controls_delta_max_C=control_max,controlled_margin_C=20-control_max,
                history_3d_scenario=representative['scenario'],
                historical_metric_max_error_C=max(c['error_C'] for c in comparisons),
                cases=comparisons,
                limitations='S25 lineal bajo la frontera voxelizada. La proyección al plano IFC es un control local, separado de Pf. El modelo no incluye confiabilidad del equipo ni validación de obra.')
    write(folder/'verification.json',report)
    historical=read(ROOT/'results/e14/enumeration/summary.json')['plans']
    table=io.StringIO(newline='')
    columns=('plan','D_h','Tmax_C','delta_C','P_T','P_delta','P_joint','status')
    writer=csv.DictWriter(table,fieldnames=columns,lineterminator='\n')
    writer.writeheader()
    for plan in [*historical,nominal['summary']]:
        row={k:plan[k] for k in columns if k!='status'}
        row['status']='CUMPLE EN EL MODELO' if plan['P_joint']<=.05 else 'NO CUMPLE'
        writer.writerow(row)
    path=folder/'planes.csv'
    contents=table.getvalue()
    if path.exists():
        if path.read_text(encoding='utf8')!=contents:
            raise ValueError('La tabla existente contiene resultados distintos')
    else:
        with path.open('x',encoding='utf8',newline='') as file:
            file.write(contents)
    print('PASS',report['summary'], 'margen controlado [°C]',report['controlled_margin_C'])

if __name__=='__main__':
    main()
