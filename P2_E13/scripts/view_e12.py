"""Abrir el campo oficial E12 en el visor PyVista reutilizado."""
from mcoc_p2.e11.pipeline import ROOT
from mcoc_p2.e11.viewer import Viewer
from mcoc_p2.housekeeping import configure_runtime
def main():
    viewer=Viewer(ROOT/'vtk/e13',ROOT/'results/e13/representative',log_path=ROOT/'results/verification/native_session.json')
    viewer.log('native_open')
    try:viewer.plotter.show(auto_close=False)
    finally:viewer.log('native_closed');viewer.plotter.close()
if __name__=='__main__':configure_runtime(ROOT);main()

