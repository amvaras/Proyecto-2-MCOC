"""Exporta y reimporta los estados del campo guardado, sin resolver de nuevo."""
import argparse,json
from pathlib import Path
from mcoc_p2.e11.vtkio import export_result
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--result',type=Path,default=ROOT/'results/e11');p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if not a.output.resolve().is_relative_to(ROOT):raise ValueError('Salida dentro de E11')
    print(json.dumps(export_result(a.result,a.output,[0,12,36]),indent=2))
if __name__=='__main__':main()
