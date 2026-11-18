"""Regenerar VTK y figuras desde los campos oficiales ya calculados."""
import argparse,json
from pathlib import Path
from mcoc_p2.e11.pipeline import ROOT,write_json
from mcoc_p2.e11.vtkio import export_result
from mcoc_p2.e12.plots import make_plots
from mcoc_p2.housekeeping import configure_runtime
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--result',type=Path,default=ROOT/'results/e13/representative')
    p.add_argument('--vtk-dir',type=Path,default=ROOT/'vtk/e13');p.add_argument('--figures-dir',type=Path,default=ROOT/'figures');a=p.parse_args()
    if any(not x.resolve().is_relative_to(ROOT) for x in (a.result,a.vtk_dir,a.figures_dir)):raise ValueError('Artefactos dentro de E12')
    s=json.loads((a.result/'summary.json').read_text(encoding='utf8'))
    if not (a.vtk_dir/'manifest.json').exists():
        s['vtk']=export_result(a.result,a.vtk_dir,sorted(set([*s['configuration']['export_hours'],s['global_maximum']['time_h'],s['global_delta25_maximum']['time_h']])),collection_name='e12.pvd')
    write_json(a.result/'summary.json',s);s['figures']=make_plots(a.result,a.figures_dir,a.vtk_dir);write_json(a.result/'summary.json',s)
    print(json.dumps({'vtk':len(s['vtk']['states']),'figures':s['figures']},ensure_ascii=False,indent=2))
if __name__=='__main__':configure_runtime(ROOT);main()

