"""Un único caso crítico ilustrativo; sin presentarlo como recomendación si no hay factible."""
from pathlib import Path
from time import perf_counter
import numpy as np
from mcoc_p2.e11.pipeline import ROOT,write_json
from mcoc_p2.e12.pipeline import run
from mcoc_p2.e13.weather import read
from mcoc_p2.housekeeping import configure_runtime
def main():
    study=read(ROOT/'results/e13/summary.json');rows=read(ROOT/'results/e13/cases.json');selected=[r for r in rows if r['plan']==study['illustrative_plan']]
    critical=max(selected,key=lambda r:(r['delta_C'],r['Tmax_C']));cfg=critical['configuration'];start=perf_counter()
    s=run(cfg,ROOT/'results/e13/representative',plots=False,vtk_dir=ROOT/'vtk/e13',keep_all_steps=True)
    assert s['global_maximum']['temperature_C']==critical['Tmax_C'] and s['global_delta25_maximum']['value_C']==critical['delta_C']
    s.update(illustrative_plan=critical['plan'],illustrative_scenario=critical['scenario'],illustrative_is_recommendation=study['best_feasible'] is not None,
             E13_risk_status='Riesgo del plan en results/e13/summary.json; este campo representa un solo escenario')
    write_json(ROOT/'results/e13/representative/summary.json',s)
    write_json(ROOT/'results/verification/representative.json',dict(status='PASS',plan=critical['plan'],scenario=critical['scenario'],matched_batch_Tmax_C=critical['Tmax_C'],matched_batch_delta_C=critical['delta_C'],elapsed_s=perf_counter()-start,role='Caso crítico ilustrativo, no recomendación si ningún plan es factible'))
    print(critical['plan'],critical['scenario'],s['global_maximum'],s['global_delta25_maximum'])
if __name__=='__main__':configure_runtime(ROOT);main()
