"""Demo E11 offline por defecto: weather real, control constante y VTK."""
import argparse,json
from pathlib import Path
from mcoc_p2.e11.pipeline import run
from mcoc_p2.housekeeping import configure_runtime
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,default=ROOT/'configs/e11/demo.json')
    p.add_argument('--output',type=Path,default=ROOT/'results/e11');p.add_argument('--hours',type=float);p.add_argument('--spacing',type=float,nargs=3)
    p.add_argument('--no-plots',action='store_true');p.add_argument('--no-vtk',action='store_true')
    p.add_argument('--vtk-dir',type=Path);p.add_argument('--figures-dir',type=Path)
    a=p.parse_args();c=json.loads(a.config.read_text(encoding='utf-8'))
    if a.hours is not None:c['physics']['t_end_s']=a.hours*3600
    if a.spacing is not None:c['physics']['spacing_m']=a.spacing
    # La ejecución de simulación usa exclusivamente snapshots: se impide HTTP.
    from unittest.mock import patch
    def offline(*args,**kwargs):raise RuntimeError('Simulación E11 offline: adquisición HTTP deshabilitada')
    with patch('urllib.request.urlopen',offline),patch('mcoc_p2.e10.weather.urlopen',offline):
        r=run(c,a.output,plots=not a.no_plots,export=not a.no_vtk,vtk_dir=a.vtk_dir,figure_dir=a.figures_dir)
    print(json.dumps({k:r[k] for k in ('status','steps','peaks','comparison','elapsed_s')},ensure_ascii=False,indent=2))
if __name__=='__main__':configure_runtime(ROOT);main()
