"""Figuras E14 reproducibles desde entradas y resultados guardados; sin solver."""
from pathlib import Path
import hashlib,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw,ImageFont,PngImagePlugin
from mcoc_p2.e11.pipeline import ROOT
from mcoc_p2.e12.source import read_sources
from mcoc_p2.e12.plots import make_plots
from mcoc_p2.e14.io import read,write
from mcoc_p2.e14.statistics import zero_failure_upper
from mcoc_p2.housekeeping import configure_runtime

def main():
    dest=ROOT/'figures';dest.mkdir(exist_ok=True)
    en=read(ROOT/'results/e14/enumeration/summary.json');mc=read(ROOT/'results/e14/monte_carlo/summary.json')
    manifest=read(ROOT/'results/e14/enumeration/manifest.json');cfg=manifest['configuration'];num=read(ROOT/'results/verification/numerics_e14.json')
    rows=[e['row'] for p in (ROOT/'results/e14/enumeration/chunks').glob('*.json') for e in read(p)['entries']]
    paths=[];provenance={};names=[p['plan'] for p in en['plans']]
    plt.rcParams.update({'font.size':10,'figure.dpi':130,'axes.grid':True,'grid.alpha':.2})
    def save(fig,name,source,context):
        path=dest/name;fig.savefig(path,dpi=160,bbox_inches='tight');plt.close(fig);paths.append(path)
        provenance[path.name]=dict(source=source,context=context,configuration='configs/e14/study.json',manifest=manifest['fingerprint'])
    curves,_=read_sources(ROOT/'data/hydration/source_terms.txt');fig,axs=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for name,(t,q) in curves.items():axs[0 if name.endswith('SS') else 1].plot(t/3600,q,label=name)
    for ax,title in zip(axs,['SS originales','22A originales: registro hasta 163 h']):
        ax.set(title=title,xlabel='Edad desde activación [h]',ylabel='Fuente [W/m³]');ax.legend()
    save(fig,'e14_fuentes.png','data/hydration/source_terms.txt','Ocho curvas experimentales; sin nuevos ensayos ni calibración')
    red=read(ROOT/'data/ensemble/reduction.json');origin=__import__('mcoc_p2.e10.weather',fromlist=['utc_time']).utc_time(read(ROOT/'configs/e13/study.json')['start_utc']).timestamp()
    fig,ax=plt.subplots(figsize=(11,4))
    for member,path,w in zip(red['medoids'],red['snapshots'],red['weights']):
        raw=read(ROOT/path/'weather.json');t=(np.array(raw['hourly']['time'])-origin)/3600;use=(t>=0)&(t<=744)
        ax.plot(t[use],np.array(raw['hourly']['temperature_2m'])[use],label=f'Miembro {member}; peso {w:.4f}')
    ax.set(xlabel='Tiempo desde 19/11/2026 08:00 Chile [h]',ylabel='Temperatura ambiente [°C]',title='GFS congelado 17/11/2026 · historias completas, sin extrapolación');ax.legend()
    save(fig,'e14_climas.png','data/ensemble/reduction.json','Tres medoids de 31 miembros; cada escenario conserva su historia')
    fig,axs=plt.subplots(1,2,figsize=(13,4.6),layout='constrained');colors=plt.cm.tab10.colors
    for i,p in enumerate(cfg['plans']):
        c=p['construction']
        for j,(start,duration) in enumerate(zip(c['start_h'],c['duration_h'])):axs[0].broken_barh([(start,duration)],(i-.3,.6),facecolors=colors[j])
        axs[1].barh(i,c['remove_at_h'],color=colors[i%10],alpha=.7)
    for ax in axs:ax.set(yticks=range(8),yticklabels=names,xlabel='Tiempo desde inicio [h]');ax.invert_yaxis()
    axs[0].set_title('Colocación: una bomba hipotética 50 m³/h');axs[1].set_title('Retiro de protección; después se sigue simulando')
    save(fig,'e14_cronogramas.png','configs/e14/study.json','Color de bloques = vertida; activación instantánea al inicio de cada bloque')
    fig,axs=plt.subplots(1,2,figsize=(12,4.5),layout='constrained')
    for ax,key,limit,title in zip(axs,['Tmax_C','delta_C'],[70,20],['Máximo térmico','Máximo diferencial S25']):
        ax.barh(names,[p[key] for p in en['plans']],color=colors[:8]);ax.axvline(limit,color='red',ls='--',label=f'Límite {limit} °C');ax.set(xlabel='Temperatura o diferencia [°C]',title=title);ax.invert_yaxis();ax.legend()
    save(fig,'e14_extremos.png','results/e14/enumeration/chunks/*.json','Cada barra: envolvente de los 24 escenarios; H = 408/600/744 h según plan')
    fig,ax=plt.subplots(figsize=(11,4.5));x=np.arange(8);exact=[p['P_joint']*100 for p in en['plans']];est=[p['P_joint']*100 for p in mc['plans']]
    ci=np.array([p['CI'] for p in mc['plans']]).T*100
    ax.bar(x-.16,exact,.3,label='Enumeración ponderada exacta');ax.errorbar(x+.16,est,yerr=np.maximum(0,np.vstack([np.array(est)-ci[0],ci[1]-np.array(est)])),fmt='o',capsize=4,label='MC: N=10000; IC bilateral 95%')
    ax.axhline(5,color='red',ls='--',label='Objetivo 5%');ax.set(xticks=x,xticklabels=names,ylabel='Pf conjunta OR [%]',ylim=(-2,106),title='Riesgo condicional al modelo discreto hipotético; no confiabilidad de obra');ax.tick_params(axis='x',rotation=20);ax.legend(fontsize=9)
    save(fig,'e14_probabilidades.png','results/e14/{enumeration,monte_carlo}/summary.json','Semilla 20261119; 24 átomos; IC solo de muestreo IID')
    fig,ax=plt.subplots(figsize=(10,4.3))
    for p in mc['plans'][-3:]:
        a=p['Pf_N'];n=[v['N'] for v in a];pf=np.array([v['Pf'] for v in a])*100;lo=[v['CI'][0]*100 for v in a];hi=[v['CI'][1]*100 for v in a]
        line,=ax.plot(n,pf,'o-',label=p['plan']);ax.fill_between(n,lo,hi,color=line.get_color(),alpha=.13)
        ax.axhline(next(e['P_joint'] for e in en['plans'] if e['plan']==p['plan'])*100,color=line.get_color(),ls=':',alpha=.8)
    ax.set(xscale='log',xlabel='Número N de realizaciones [1]',ylabel='Pf conjunta [%]',title='Pf(N): IC Clopper–Pearson 95% marginal en cada N; no banda simultánea');ax.legend()
    save(fig,'e14_pf_N.png','results/e14/monte_carlo/summary.json','Mismo banco aleatorio entre planes; líneas punteadas = enumeración exacta')
    fig,ax=plt.subplots(figsize=(8,3.8));n=np.arange(1,1001);ax.plot(n,[zero_failure_upper(int(v))*100 for v in n]);ax.axhline(5,color='red',ls='--');ax.scatter([59],[zero_failure_upper(59)*100],color='red')
    ax.set(xlabel='N hipotético con cero fallas IID [1]',ylabel='Cota unilateral 95% de Pf [%]',title='Cero fallas no prueba Pf=0 · cálculo ilustrativo, no resultado de estos planes')
    save(fig,'e14_cero_fallas.png','src/mcoc_p2/e14/statistics.py','Cota 1−0.05^(1/N); hipótesis IID condicional al modelo')
    fig,ax=plt.subplots(figsize=(10,4.2))
    for i,p in enumerate(en['plans']):ax.scatter(p['D_h'],100*p['P_joint'],s=60,color=colors[i],label=p['plan'])
    ax.axhline(5,color='red',ls='--',label='Objetivo 5%');ax.set(xlabel='Duración de colocación D [h]',ylabel='Pf conjunta [%]',ylim=(-2,105),title='Duración–riesgo · ningún plan factible entre los ocho evaluados');ax.legend(ncol=2,fontsize=8)
    save(fig,'e14_duracion_riesgo.png','results/e14/enumeration/summary.json','D no es horizonte de curado; no se afirma óptimo global')
    fig,ax=plt.subplots(figsize=(12,4.3));labels=[];changes=[]
    for r in num['controls']:
        nom=next(v for v in rows if v['plan']==r['plan'] and v['scenario']==r['scenario']);labels.append(r['plan']+'\n'+r['scenario']+'\n'+r['control']);changes.append(r['delta_C']-nom['delta_C'])
    ax.bar(range(len(labels)),changes,color='#397f8c');ax.axhline(0,color='black',lw=.6);ax.set(xticks=range(len(labels)),xticklabels=labels,ylabel='Cambio del máximo ΔT respecto al nominal [°C]',title='13 controles dirigidos · sin cambio de clase observado; sin cota de error global');ax.tick_params(axis='x',labelsize=6,rotation=35)
    save(fig,'e14_sensibilidad.png','results/verification/numerics_e14.json','Malla .30/.30/.055 m; dt/2; reescala global de área: aproximación exploratoria')
    rep=ROOT/'results/e14/representative';r=read(rep/'summary.json')
    for name in make_plots(rep,dest,ROOT/'vtk/e14',only={'e12_temperaturas.png','e12_diferencial.png','e12_secciones.png','e12_tiempo_altura.png','e12_energia.png'}):
        path=ROOT/name;paths.append(path);provenance[path.name]=dict(source='results/e14/representative/{summary.json,fields.npz,statistics.npz}',context=f"{r['illustrative_plan']} · {r['illustrative_scenario']} · H=744 h · caso crítico ΔT, no plan factible",configuration='results/e14/representative/summary.json')
    # Pie visible y procedencia embebida también para las imágenes 3D generadas por VTK.
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13) if (Path('C:/Windows/Fonts/arial.ttf')).exists() else ImageFont.load_default()
    records=[]
    for path in paths:
        entry=provenance[path.name]
        with Image.open(path) as im:
            canvas=Image.new('RGB',(im.width,im.height+48),'white');canvas.paste(im.convert('RGB'),(0,0));draw=ImageDraw.Draw(canvas)
            for j,line in enumerate([entry['context'],'E14 · '+entry['source']]):draw.text((12,im.height+3+21*j),line,fill='#233647',font=font)
            info=PngImagePlugin.PngInfo();info.add_text('provenance',json.dumps(entry,ensure_ascii=False));canvas.save(path,pnginfo=info)
        records.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),**entry))
    write(ROOT/'results/e14/figures.json',dict(count=len(records),figures=records),replace=True)
    print('Figuras reproducidas:',len(records))
if __name__=='__main__':configure_runtime(ROOT);main()
