"""Regenerar evidencia gráfica E13 desde datos locales."""
from mcoc_p2.e13.plots import plot_study
from mcoc_p2.housekeeping import configure_runtime
from mcoc_p2.e11.pipeline import ROOT
if __name__=='__main__':
    configure_runtime(ROOT)
    for path in plot_study():print(path)
