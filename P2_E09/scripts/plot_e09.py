"""Regenera figuras desde el campo guardado, sin resolver otra vez el calor."""
import argparse,json
from pathlib import Path
from mcoc_p2.e09.plots import generate_figures
from mcoc_p2.housekeeping import configure_runtime
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--result',type=Path,default=ROOT/'results/e09_baseline')
    p.add_argument('--figures-dir',type=Path,default=ROOT/'figures');p.add_argument('--no-animation',action='store_true')
    p.add_argument('--azim',type=float,default=-62);p.add_argument('--elev',type=float,default=26)
    a=p.parse_args();print(json.dumps(generate_figures(a.result,a.figures_dir,animation=not a.no_animation,azim=a.azim,elev=a.elev),indent=2))


if __name__=='__main__':configure_runtime(ROOT);main()
