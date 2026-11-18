"""Enumeración E13 offline; solo métricas, sin VTK/PNG por escenario."""
from pathlib import Path
import argparse,json
from mcoc_p2.e11.pipeline import ROOT
from mcoc_p2.e13.evaluator import run_study
from mcoc_p2.housekeeping import configure_runtime
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,default=ROOT/'configs/e13/study.json');p.add_argument('--output',type=Path,default=ROOT/'results/e13');p.add_argument('--resume',action='store_true');a=p.parse_args()
    cfg=json.loads(a.config.read_text(encoding='utf8'))
    def show(s):print(f"{s['completed']}/{s['total']} {s['plan']} {s['scenario']} {s['last_elapsed_s']:.2f} s",flush=True)
    print(json.dumps(run_study(cfg,a.output,resume=a.resume,progress=show),ensure_ascii=False,indent=2))
if __name__=='__main__':configure_runtime(ROOT);main()
