"""Riesgo independiente, trazabilidad, evidencia en campos y reproducción dirigida offline."""
from pathlib import Path
from time import perf_counter
import argparse,hashlib,json,math
import numpy as np
from mcoc_p2.e11.pipeline import ROOT,write_json
from mcoc_p2.e12.source import read_sources,load_curve
from mcoc_p2.e12.verification import verify
from mcoc_p2.e13.weather import read,validate_snapshot
from mcoc_p2.e13.evaluator import Evaluator,signature,validate_study
from mcoc_p2.e13.risk import scenarios
from mcoc_p2.housekeeping import configure_runtime
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--reproduce',action='store_true');a=ap.parse_args();start=perf_counter()
    folder=ROOT/'results/e13';inputs=read(folder/'inputs.json');ev=Evaluator();cfg=validate_study(inputs['configuration'],ev)
    assert inputs==signature(cfg),'Inputs/código cambió después del cálculo: conservar evidencia y recalcular'
    summary=read(folder/'summary.json');rows=read(folder/'cases.json');red=read(ROOT/'data/ensemble/reduction.json');sc=scenarios(red,cfg['material_weights'])
    assert len(rows)==len(cfg['plans'])*24 and len({(r['plan'],r['scenario']) for r in rows})==len(rows)
    _,sources=read_sources(ROOT/'data/hydration/source_terms.txt');voxel=ev.grid(cfg['spacing_m']);v=voxel.report();risks=[]
    for name in red['snapshots']:validate_snapshot(ROOT/name)
    for p in cfg['plans']:
        selected=[r for r in rows if r['plan']==p['id']];assert {r['scenario'] for r in selected}=={s['id'] for s in sc}
        for r in selected:
            scenario=next(s for s in sc if s['id']==r['scenario']);assert r['weight']==scenario['weight'] and r['D_h']==p['D_h']
            assert r['coverage']['tail_hours']==0 and r['horizon_h']>=336 and r['last_pour_age_h']>=240 and all(r['checks'].values())
            assert r['first336_Tmax_C']<=r['Tmax_C'] and r['first336_delta_C']<=r['delta_C']
            assert not r['Tmax_peak_in_last24h'] and not r['delta_peak_in_last24h']
            e=r['energy'];assert abs(e['final_J']-e['initial_J']-e['hydration_J']+e['outward_J']-e['placement_after_zero_J'])<=e['tolerance_J']
            spec=r['configuration']['experimental_source'];curve,_=load_curve(ROOT/spec['file'],spec['curve'],spec['tail'],spec['tau_s'])
            expected=sum(x['volume_voxel_m3']*float(curve.released(0,max(0,cfg['horizon_h']*3600-next(t['activation_s'] for t in r['configuration']['physics']['events'] if t['pour_id']==x['vertida_id'])))) for x in v['by_pour'])
            assert abs(e['hydration_J']-expected)<.01
            np.testing.assert_allclose(r['delta_C'],r['delta_peak']['hot_temperature_C']-r['delta_peak']['cold']['temperature_C'],rtol=0,atol=1e-12)
            for point in (r['peak'],r['delta_peak']['hot']):
                idx=tuple(point['index']);assert int(voxel.vertida_id[idx])==point['vertida_id'] and voxel.occupation_mask[idx]
                np.testing.assert_allclose(point['coordinate_m'],np.array(voxel.grid.origin)+(np.array(idx)+.5)*voxel.grid.spacing,rtol=0,atol=1e-12)
        # Independiente de risk.probability: sumas Python fsum y OR explícito.
        risk=dict(plan=p['id'],P_T=math.fsum(r['weight'] for r in selected if r['Tmax_C']>70),P_delta=math.fsum(r['weight'] for r in selected if r['delta_C']>20),P_joint=math.fsum(r['weight'] for r in selected if r['Tmax_C']>70 or r['delta_C']>20))
        published=next(x for x in summary['plans'] if x['plan']==p['id'])
        for k in ('P_T','P_delta','P_joint'):assert abs(risk[k]-published[k])<1e-12
        risks.append(risk)
    fields=verify(folder/'representative',ROOT/'vtk/e13')
    controls=read(ROOT/'results/verification/controls.json');assert controls['status']=='PASS'
    assert all(all(r['checks'].values()) for r in controls['cases']) and controls['single_union']['all_saved_fields_equal']
    reproduced=[]
    if a.reproduce:
        identifiers={(summary['illustrative_plan'],max((r for r in rows if r['plan']==summary['illustrative_plan']),key=lambda r:r['delta_C'])['scenario']),
                     (min(rows,key=lambda r:r['delta_C'])['plan'],min(rows,key=lambda r:r['delta_C'])['scenario'])}
        for pid,sid in sorted(identifiers):
            p=next(p for p in cfg['plans'] if p['id']==pid);s=next(s for s in sc if s['id']==sid);r,_,_,_=ev.case(p,s,spacing=cfg['spacing_m'],horizon_h=cfg['horizon_h'],max_step_s=cfg['max_step_s']);original=next(r for r in rows if r['plan']==pid and r['scenario']==sid)
            for k in ('Tmax_C','delta_C','first336_Tmax_C','first336_delta_C'):assert r[k]==original[k]
            assert r['peak']==original['peak'] and r['delta_peak']==original['delta_peak'];reproduced.append(dict(plan=pid,scenario=sid,exact=True))
    report=dict(status='PASS',cases=len(rows),scenario_weights_sum=math.fsum(s['weight'] for s in sc),independent_probabilities=risks,
       original_sources=sources,grid=v,global_fields_verification=fields,scientific_controls='PASS',single_union=controls['single_union'],
       reproduced_cases=reproduced,network='Cada Evaluator.case y pipeline E12 bloquea HTTP; todos los datos son locales',
       conclusion=summary['conclusion'],elapsed_s=perf_counter()-start,limits='Numerically verified discrete exploratory model; not calibrated reliability or experimental validation')
    write_json(ROOT/'results/verification/e13.json',report);print(json.dumps({k:v for k,v in report.items() if k not in ('original_sources','grid','global_fields_verification')},ensure_ascii=False,indent=2))
if __name__=='__main__':configure_runtime(ROOT);main()
