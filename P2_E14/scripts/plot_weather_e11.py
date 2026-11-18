"""Mostrar metadata y regenerar gráfico desde el snapshot normalizado validado."""
import argparse,json
from pathlib import Path
from mcoc_p2.e11.weather import validate
from mcoc_p2.e11.plots import plot_weather
from mcoc_p2.housekeeping import configure_runtime
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,default=ROOT/'configs/e11/demo.json')
    a=p.parse_args();cfg=json.loads(a.config.read_text(encoding='utf-8'));folder=ROOT/cfg['snapshot']
    print(json.dumps(validate(folder).metadata,ensure_ascii=False,indent=2));plot_weather(folder,ROOT/'figures/e11_ambiente.png')
if __name__=='__main__':configure_runtime(ROOT);main()
