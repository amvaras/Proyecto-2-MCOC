"""Ejecutar E12 offline desde su propia carpeta; resultados nuevos, sin reemplazar."""
import argparse,json
from copy import deepcopy
from pathlib import Path
from mcoc_p2.e11.pipeline import ROOT
from mcoc_p2.e12.pipeline import run
from mcoc_p2.housekeeping import configure_runtime
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,default=ROOT/'configs/e12/baseline.json')
    p.add_argument('--output',type=Path,default=ROOT/'results/e12');p.add_argument('--vtk-dir',type=Path,default=ROOT/'vtk/e12');p.add_argument('--figures-dir',type=Path,default=ROOT/'figures')
    p.add_argument('--no-plots',action='store_true');p.add_argument('--no-export',action='store_true');p.add_argument('--summary-only-fields',action='store_true')
    a=p.parse_args();cfg=json.loads(a.config.read_text(encoding='utf8'))
    s=run(cfg,a.output,plots=not a.no_plots,export=not a.no_export,keep_all_steps=not a.summary_only_fields,vtk_dir=a.vtk_dir,figure_dir=a.figures_dir)
    print(json.dumps({k:s[k] for k in ('delivery','steps','saved_frames','global_maximum','global_delta25_maximum','deterministic_status','elapsed_s')},ensure_ascii=False,indent=2))
if __name__=='__main__':
    configure_runtime(ROOT);main()

