"""E08: IFC→grilla→temperatura por etapas. El calendario se lee de JSON."""
import argparse
import json
from pathlib import Path
from datetime import datetime,timezone
from mcoc_p2.e08.pipeline import run_pipeline

ROOT=Path(__file__).resolve().parents[1]


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ifc',type=Path,default=ROOT/'geometry/foundation.ifc')
    p.add_argument('--config',type=Path,default=ROOT/'configs/e08/demo.json')
    p.add_argument('--output',type=Path)
    p.add_argument('--spacing',type=float,nargs='+')
    p.add_argument('--interval-hours',type=float)
    p.add_argument('--placement-offset',type=float,help='Incremento en °C aplicado a las colocaciones del JSON')
    p.add_argument('--t-end-hours',type=float)
    p.add_argument('--max-step',type=float)
    p.add_argument('--no-plots',action='store_true')
    args=p.parse_args(argv)
    try:
        cfg=json.loads(args.config.read_text(encoding='utf-8-sig'))
        if args.spacing is not None:cfg['spacing_m']=args.spacing*3 if len(args.spacing)==1 else args.spacing
        if args.interval_hours is not None:
            import math
            if not math.isfinite(args.interval_hours) or args.interval_hours<0:raise ValueError('Intervalo no negativo')
            for i,event in enumerate(sorted(cfg['events'],key=lambda e:e['pour_id'])):event['activation_s']=i*args.interval_hours*3600
        if args.placement_offset is not None:
            for event in cfg['events']:event['initial_C']+=args.placement_offset
        if args.t_end_hours is not None:cfg['t_end_s']=args.t_end_hours*3600
        if args.max_step is not None:cfg['max_step_s']=args.max_step
        output=args.output or ROOT/'results/e08'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        report=run_pipeline(args.ifc,cfg,output,plots=not args.no_plots)
        print(json.dumps(dict(status=report['status'],cells=report['nominal']['occupied_cells'],
            volume_error_pct=100*report['nominal']['relative_error'],frames=len(report['times_s']),
            peak_C=report['temperature_range_C'][1],energy=report['energy'],checks=report['checks'],output=str(output)),ensure_ascii=False,indent=2))
        return 0
    except (ValueError,TypeError,KeyError,OSError,OverflowError,RuntimeError,FloatingPointError) as exc:
        print('ERROR: '+str(exc));return 2


if __name__=='__main__':raise SystemExit(main())
