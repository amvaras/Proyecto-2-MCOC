"""Un caso E14 crítico ilustrativo; nunca presentar como factible si no cumple."""
from time import perf_counter
from mcoc_p2.e11.pipeline import ROOT
from mcoc_p2.e14.io import read,write
from mcoc_p2.e14.model import Model,catalog
from mcoc_p2.e12.pipeline import run
from mcoc_p2.housekeeping import configure_runtime
def main():
    path=ROOT/'results/e14/enumeration';s=read(path/'summary.json');m=read(path/'manifest.json')
    best=min(s['plans'],key=lambda p:(p['P_joint'],p['delta_C'],p['D_h']));item=next(p for p in m['configuration']['plans'] if p['id']==best['plan'])
    rows=[e['row'] for p in (path/'chunks').glob('*.json') for e in read(p)['entries'] if e['row']['plan']==item['id']]
    critical=max(rows,key=lambda r:r['delta_C']);scenario=next(s for s in catalog() if s['id']==critical['scenario'])
    cfg,_=Model().configuration(item,scenario);cfg['physics']['description']='E14: caso crítico ilustrativo, no recomendación de factibilidad';start=perf_counter()
    r=run(cfg,ROOT/'results/e14/representative',plots=False,keep_all_steps=True,vtk_dir=ROOT/'vtk/e14')
    assert r['global_maximum']['temperature_C']==critical['Tmax_C'] and r['global_delta25_maximum']['value_C']==critical['delta_C']
    r.update(illustrative_plan=item['id'],illustrative_scenario=critical['scenario'],best_feasible=best if best['P_joint']<=.05 else None,
             E14_Pf_joint=best['P_joint'],role='Caso ilustrativo de menor riesgo evaluado; no cumple si Pf>5%')
    write(ROOT/'results/e14/representative/summary.json',r,replace=True)
    write(ROOT/'results/verification/representative_e14.json',dict(status='PASS',plan=item['id'],scenario=critical['scenario'],Tmax_C=critical['Tmax_C'],delta_C=critical['delta_C'],elapsed_s=perf_counter()-start,matched_enumeration=True))
    print(item['id'],critical['scenario'],critical['Tmax_C'],critical['delta_C'])
if __name__=='__main__':configure_runtime(ROOT);main()
