"""Controles dirigidos, incluidos escenarios cercanos al límite de 20°C."""
from concurrent.futures import ProcessPoolExecutor,as_completed
from copy import deepcopy
from mcoc_p2.e11.pipeline import ROOT
from mcoc_p2.e14.io import read,write
from mcoc_p2.e14.model import Model,catalog
from mcoc_p2.e14.workflow import initialize
from mcoc_p2.e14.store import Store
from mcoc_p2.housekeeping import configure_runtime
_MODEL=None
def init():
    global _MODEL
    _MODEL=Model()
def control(task):
    item,scenario,label,spacing,step,area=task
    row,a,_,_=_MODEL.evaluate(item,scenario,spacing=spacing,step_s=step,area_factors=area)
    row.update(control=label,delta_face0_C=float((a['Tmax_C']-a['face_min_C']).max()),delta_boundary_centers_C=float((a['Tmax_C']-a['boundary_cell_min_C']).max()))
    return row
def main():
    folder=ROOT/'results/e14/enumeration';m=read(folder/'manifest.json');rows=[e['row'] for p in (folder/'chunks').glob('*.json') for e in read(p)['entries']]
    new=[p for p in m['configuration']['plans'] if p['design']];sc=catalog();worst=next(s for s in sc if s['curve']=='M4_SS' and s['member']==0)
    reference=read(ROOT/'results/verification/controls.json')['area_reference'];area=[reference['air_factor'],reference['ground_factor']];tasks=[]
    for item in new:
        tasks.extend([(item,worst,'fine_mesh',[.3,.3,.055],900,None),(item,worst,'area_rescale',[.45,.45,.11],900,area)])
    best=min(read(folder/'summary.json')['plans'],key=lambda p:(p['P_joint'],p['delta_C']));chosen=next(p for p in new if p['id']==best['plan'])
    tasks.append((chosen,worst,'half_dt',[.45,.45,.11],450,None))
    close=sorted((r for r in rows if r['plan'] in {p['id'] for p in new}),key=lambda r:abs(r['delta_C']-20))[:3]
    for r in close:
        p=next(p for p in new if p['id']==r['plan']);s=next(s for s in sc if s['id']==r['scenario'])
        for label,spacing,factor in [('near20_fine',[.3,.3,.055],None),('near20_area',[.45,.45,.11],area)]:
            if not any(t[0]['id']==p['id'] and t[1]['id']==s['id'] and t[2].endswith('fine')==label.endswith('fine') and t[3]==spacing for t in tasks):tasks.append((p,s,label,spacing,900,factor))
    output=ROOT/'results/verification/numerics_e14.json'
    if output.exists():raise ValueError('Preservar controles existentes')
    data=dict(status='RUNNING',area_reference=reference,controls=[],near20_nominal=[dict(plan=r['plan'],scenario=r['scenario'],delta_C=r['delta_C']) for r in close],meaning='Variaciones observadas: no cotas rigurosas, no IC estadísticos ni corrección cut-cell')
    with ProcessPoolExecutor(max_workers=2,initializer=init) as pool:
        for f in as_completed([pool.submit(control,t) for t in tasks]):
            r=f.result();data['controls'].append(r);write(output,data,replace=True);print(r['control'],r['plan'],r['scenario'],r['delta_C'],flush=True)
    data['observed_classification_changes']=[]
    for r in data['controls']:
        nominal=next(x for x in rows if x['plan']==r['plan'] and x['scenario']==r['scenario'])
        if (nominal['delta_C']>20)!=(r['delta_C']>20):data['observed_classification_changes'].append(dict(plan=r['plan'],scenario=r['scenario'],control=r['control'],nominal_delta_C=nominal['delta_C'],changed_delta_C=r['delta_C']))
    envelopes=[]
    for p in new:
        lo=hi=0.
        for s in sc:
            nominal=next(r for r in rows if r['plan']==p['id'] and r['scenario']==s['id']);variants=[nominal,*[r for r in data['controls'] if r['plan']==p['id'] and r['scenario']==s['id']]]
            failure=[r['Tmax_C']>70 or r['delta_C']>20 for r in variants];lo+=s['weight']*all(failure);hi+=s['weight']*any(failure)
        envelopes.append(dict(plan=p['id'],observed_risk_envelope=[lo,hi],meaning='Envolvente de las variantes calculadas, no intervalo de confianza ni cota completa del error IFC'))
    data.update(status='PASS',observed_risk_envelopes=envelopes,all_checks=all(all(r['checks'].values()) for r in data['controls']));write(output,data,replace=True)
if __name__=='__main__':configure_runtime(ROOT);main()
