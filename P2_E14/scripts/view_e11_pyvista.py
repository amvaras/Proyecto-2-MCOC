"""Abrir visor nativo o generar vistas off-screen explícitamente diferenciadas."""
import argparse,json
from mcoc_p2.e11.viewer import Viewer,render_figures
from mcoc_p2.housekeeping import configure_runtime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--off-screen',action='store_true')
    p.add_argument('--result',type=Path,default=ROOT/'results/e11');p.add_argument('--vtk-dir',type=Path,default=ROOT/'vtk/e11');p.add_argument('--session-log',type=Path)
    a=p.parse_args()
    if any(not path.resolve().is_relative_to(ROOT) for path in (a.result,a.vtk_dir)):raise ValueError('Visor dentro de E11')
    if a.off_screen:
        report=render_figures(a.vtk_dir,a.result);out=ROOT/'results/verification/render.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
    else:
        v=Viewer(a.vtk_dir,a.result,log_path=a.session_log);v.log('native_open')
        try:v.plotter.show(auto_close=False)
        finally:v.log('native_closed');v.plotter.close()
if __name__=='__main__':configure_runtime(ROOT);main()
