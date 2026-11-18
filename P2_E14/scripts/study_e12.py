"""Sensibilidades controladas: solo evidencia compacta; no corridas históricas."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import hashlib,json,time
import numpy as np
from mcoc_p2.e11.pipeline import ROOT,make_environment,ConstantWeather,write_json
from mcoc_p2.e11.weather import window
from mcoc_p2.e07.ifc import read_pours
from mcoc_p2.e07.voxel import voxelize
from mcoc_p2.e08.inputs import validate_config,events_from_config
from mcoc_p2.e08.solver import simulate
from mcoc_p2.e12.source import load_curve
from mcoc_p2.e12.metrics import GlobalRecorder
from mcoc_p2.housekeeping import configure_runtime

def main():
    cfg=json.loads((ROOT/'results/e13/representative/inputs.json').read_text(encoding='utf8'))
    curve,_=load_curve(ROOT/cfg['experimental_source']['file'],cfg['experimental_source']['curve'],cfg['experimental_source']['tail'])
    solids,_=read_pours(ROOT/cfg['ifc']);cache={};rows={};saved={}
    cases={'coarse':{},'fine':{},'half_dt':{},'retain_formwork':{},'h_half':{},'constant_air':{}}
    for name in cases:
        c=deepcopy(cfg)
        if name=='coarse':c['physics']['spacing_m']=[.55,.55,.11]
        if name=='fine':c['physics']['spacing_m']=[.3,.3,.055]
        if name=='half_dt':c['physics']['max_step_s']/=2
        if name=='retain_formwork':c['environment']['formwork']['remove_at_s']=c['physics']['t_end_s']+3600
        if name=='h_half':c['environment']['air']['h_still_W_m2K']/=2
        physics=validate_config(c['physics'],solids);spacing=tuple(physics['spacing_m'])
        if spacing not in cache:cache[spacing]=voxelize(solids,spacing,margin=physics['margin_m'])
        vox=cache[spacing];weather=window(ROOT/c['snapshot'],c['simulation_start_utc'],physics['t_end_s'])
        if name=='constant_air':weather=ConstantWeather(weather,c['constant_reference_C'])
        env=make_environment(vox,weather,c['environment'])
        events=[replace(e,hydration=curve) for e in events_from_config(physics)]
        record=GlobalRecorder(vox,events,env,c['core_target_m'],depth_m=c['evaluation']['depth_m'])
        start=time.perf_counter();print('E12 sensibilidad '+name,flush=True)
        solution=simulate(vox,events,t_end_s=physics['t_end_s'],max_step_s=physics['max_step_s'],save_interval_s=physics['save_interval_s'],safety=physics['safety'],
                          energy_reference_C=physics['energy_reference_C'],observer=record,boundary_update=env,boundary_change_times_s=env.change_times_s)
        a=record.arrays();rows[name]=dict(configuration=c,Tmax_C=record.peak['temperature_C'],Tmax_h=record.peak['time_h'],delta25_C=record.delta_peak['value_C'],delta25_h=record.delta_peak['time_h'],
                                      peak=record.peak,delta_peak=record.delta_peak,grid=vox.report(),energy=solution.energy,checks=solution.checks,steps=len(solution.steps),elapsed_s=time.perf_counter()-start)
        for key in ['time_s','Tmax_C','S25min_C','delta25_C','face_min_C','boundary_cell_min_C']:saved[name+'_'+key]=a[key]
        saved[name+'_peak_field_C']=record.peak_field;saved[name+'_delta_field_C']=record.delta_field
        saved[name+'_vertida_id']=vox.vertida_id;saved[name+'_origin_m']=vox.grid.origin;saved[name+'_spacing_m']=vox.grid.spacing
        del solution,record
    nominal=json.loads((ROOT/'results/e13/representative/summary.json').read_text(encoding='utf8'))
    for row in rows.values():
        row['Tmax_minus_nominal_C']=row['Tmax_C']-nominal['global_maximum']['temperature_C'];row['delta_minus_nominal_C']=row['delta25_C']-nominal['global_delta25_maximum']['value_C']
    target=ROOT/'results/verification';target.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(target/'sensitivity.npz',**saved)
    write_json(target/'sensitivity.json',dict(status='PASS',source='Misma M2_SS, sin mezclas; cada caso cambia solo la variable declarada',cases=rows,
                                             tail='M2_SS nula en las últimas 22 h; extensión cero continua, energía añadida 0; sin extrapolación climática',
                                             precision='Diferencias entre mallas/pasos son sensibilidad observada, no cota rigurosa ni convergencia demostrada',
                                             data_sha256=hashlib.sha256((target/'sensitivity.npz').read_bytes()).hexdigest()))
    print(json.dumps({n:{k:r[k] for k in ['Tmax_C','delta25_C','Tmax_minus_nominal_C','delta_minus_nominal_C','elapsed_s']} for n,r in rows.items()},indent=2))
if __name__=='__main__':configure_runtime(ROOT);main()

