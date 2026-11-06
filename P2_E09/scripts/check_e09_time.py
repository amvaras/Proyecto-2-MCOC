"""Sensibilidad temporal del baseline: mismo IFC y malla, mitad del paso máximo."""
import argparse,json,time
from pathlib import Path
import numpy as np
from mcoc_p2.e07.ifc import read_pours
from mcoc_p2.e07.voxel import voxelize
from mcoc_p2.e08.inputs import events_from_config,boundaries
from mcoc_p2.e08.solver import simulate
from mcoc_p2.e09.analysis import FieldRecorder
from mcoc_p2.e09.pipeline import write_json
from mcoc_p2.housekeeping import configure_runtime
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--result',type=Path,default=ROOT/'results/e09_baseline')
    p.add_argument('--output',type=Path,default=ROOT/'results/verification/temporal_check.json')
    a=p.parse_args();start=time.perf_counter();s=json.loads((a.result/'summary.json').read_text(encoding='utf-8'))
    cfg=s['configuration']['physics'];solids,_=read_pours(ROOT/s['ifc']['relative_path'])
    vox=voxelize(solids,cfg['spacing_m'],margin=cfg['margin_m']);events=events_from_config(cfg);bc=boundaries(cfg)
    recorder=FieldRecorder(vox,events,bc,s['configuration']['analysis']['core_target_m'])
    r=simulate(vox,events,bc,t_end_s=cfg['t_end_s'],max_step_s=cfg['max_step_s']/2,save_interval_s=cfg['save_interval_s'],
               safety=cfg['safety'],energy_reference_C=cfg['energy_reference_C'],observer=recorder)
    with np.load(a.result/'temperature.npz') as base:
        assert np.array_equal(base['times_s'],r.times_s)
        active=base['active_mask'];difference=float(np.max(abs(base['temperature_C'][active]-r.temperature_C[active])))
    report=dict(status='PASS' if all(r.checks.values()) and difference<=.2 else 'FAIL',
        reference_max_step_s=cfg['max_step_s'],refined_max_step_s=cfg['max_step_s']/2,
        field_Linf_difference_C=difference,predeclared_tolerance_C=.2,
        refined_peak=recorder.peak,peak_difference_C=recorder.peak['temperature_C']-s['thermal']['peak']['temperature_C'],
        energy=r.energy,checks=r.checks,elapsed_s=time.perf_counter()-start,
        interpretation='Sensibilidad a dt en misma grilla; no es error exacto ni convergencia espacial de fundación.')
    a.output.parent.mkdir(parents=True,exist_ok=True);write_json(a.output,report);print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report['status']=='PASS' else 1


if __name__=='__main__':configure_runtime(ROOT);raise SystemExit(main())
