"""Ejecuta E09 desde IFC/config; la representación gráfica no modifica la física."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from mcoc_p2.housekeeping import configure_runtime
from mcoc_p2.e09.pipeline import run_baseline

ROOT=Path(__file__).resolve().parents[1]


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ifc',type=Path,default=ROOT/'geometry/foundation.ifc')
    p.add_argument('--config',type=Path,default=ROOT/'configs/e09/baseline.json')
    p.add_argument('--output',type=Path,default=ROOT/'results/e09_baseline')
    p.add_argument('--figures-dir',type=Path,default=ROOT/'figures')
    p.add_argument('--spacing',type=float,nargs='+');p.add_argument('--hours',type=float)
    p.add_argument('--ambient',type=float);p.add_argument('--h',type=float);p.add_argument('--max-step',type=float)
    p.add_argument('--placement-offset',type=float);p.add_argument('--heat-mj-m3',type=float)
    p.add_argument('--activation-interval-hours',type=float)
    p.add_argument('--no-animation',action='store_true');p.add_argument('--no-plots',action='store_true');p.add_argument('--no-control',action='store_true')
    a=p.parse_args(argv)
    try:
        cfg=deepcopy(json.loads(a.config.read_text(encoding='utf-8-sig')));f=cfg['physics']
        if a.spacing is not None:f['spacing_m']=a.spacing*3 if len(a.spacing)==1 else a.spacing
        for arg,key,scale in [('hours','t_end_s',3600),('ambient','ambient_C',1),('h','h_W_m2K',1),('max_step','max_step_s',1)]:
            if getattr(a,arg) is not None:f[key]=getattr(a,arg)*scale
        if a.placement_offset is not None:
            for event in f['events']:event['initial_C']+=a.placement_offset
        if a.heat_mj_m3 is not None:f['hydration']['H_vol_J_m3']=a.heat_mj_m3*1e6
        if a.activation_interval_hours is not None:
            import math
            if not math.isfinite(a.activation_interval_hours) or a.activation_interval_hours<0:raise ValueError('Intervalo no negativo finito')
            for i,event in enumerate(sorted(f['events'],key=lambda e:e['pour_id'])):event['activation_s']=i*a.activation_interval_hours*3600
        if a.no_animation:cfg['analysis']['animation']=False
        if not a.figures_dir.resolve().is_relative_to(ROOT):raise ValueError('Figuras dentro de E09')
        r=run_baseline(a.ifc,cfg,a.output,plots=not a.no_plots,control=not a.no_control,figure_dir=a.figures_dir)
        print(json.dumps(dict(status=r['status'],duration_h=r['duration_h'],peak=r['thermal']['peak'],delta=r['thermal']['center_top_difference'],energy=r['energy']),ensure_ascii=False,indent=2))
        return 0
    except (ValueError,TypeError,KeyError,OSError,RuntimeError,OverflowError,FloatingPointError) as exc:
        print('ERROR: '+str(exc));return 2


if __name__=='__main__':
    configure_runtime(ROOT)
    raise SystemExit(main())
