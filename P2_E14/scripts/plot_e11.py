"""Regenerar figuras desde los campos existentes, sin simulación ni descargas."""
import json
from mcoc_p2.e11.pipeline import ROOT
from mcoc_p2.e11.plots import make_plots
from mcoc_p2.housekeeping import configure_runtime

if __name__=='__main__':
    configure_runtime(ROOT)
    print(json.dumps(make_plots(ROOT/'results/e11',ROOT/'figures'),indent=2))
