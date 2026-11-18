"""Evidencia de comparación y curvas: solo datos calculados o entradas auténticas."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ..e11.pipeline import ROOT
from ..e12.source import read_sources
from ..e12.plots import make_plots
from .weather import read
def plot_study(folder=None,destination=None):
    folder=Path(folder or ROOT/'results/e13');dest=Path(destination or ROOT/'figures');dest.mkdir(parents=True,exist_ok=True)
    s=read(folder/'summary.json');rows=read(folder/'cases.json');cfg=read(folder/'inputs.json')['configuration'];out=[]
    plt.rcParams.update({'figure.dpi':130,'font.size':10,'axes.grid':True,'grid.alpha':.2})
    def save(fig,name):
        path=dest/name;fig.savefig(path,dpi=160,bbox_inches='tight');plt.close(fig);out.append(path.relative_to(ROOT).as_posix())
    curves,meta=read_sources(ROOT/'data/hydration/source_terms.txt');fig,ax=plt.subplots(1,2,figsize=(11,3.6),layout='constrained')
    for j,(name,(t,q)) in enumerate(curves.items()):ax[j//4].plot(t/3600,q,label=name)
    for a,title in zip(ax,['SS · mayor confianza reportada','22A · menor confianza; fin de registro 163 h']):a.set(title=title,xlabel='Edad desde activación [h]',ylabel='Q [W/m³]');a.legend()
    save(fig,'e13_ocho_fuentes.png')
    red=read(ROOT/'data/ensemble/reduction.json');fig,ax=plt.subplots(figsize=(11,3.5));origin=__import__('mcoc_p2.e10.weather',fromlist=['utc_time']).utc_time(cfg['start_utc']).timestamp()
    for member,path,w in zip(red['medoids'],red['snapshots'],red['weights']):
        raw=read(ROOT/path/'weather.json');t=(np.array(raw['hourly']['time'])-origin)/3600;use=(t>=0)&(t<=600);ax.plot(t[use],np.array(raw['hourly']['temperature_2m'])[use],label=f'Miembro {member}: peso {w:.4f}')
    ax.axvspan(336,cfg['horizon_h'],alpha=.12,color='orange',label='Horizonte extendido');ax.set(xlabel='Desde 19/11 08:00 Chile [h]',ylabel='T aire [°C]',title='GFS 0.5° auténtico · historias completas, sin sorteo horario');ax.legend(ncol=2);save(fig,'e13_climas.png')
    fig,ax=plt.subplots(figsize=(11,4.2));colors=plt.cm.tab10.colors
    for i,p in enumerate(cfg['plans']):
        if p['partition']=='single':ax.broken_barh([(p['start_h'][0],p['duration_h'][0])],(i-.3,.6),facecolors=colors[0])
        else:
            for j,(start,duration) in enumerate(zip(p['start_h'],p['duration_h'])):ax.broken_barh([(start,duration)],(i-.3,.6),facecolors=colors[j])
        ax.text(p['D_h']+.5,i,f"D={p['D_h']:.3f} h",va='center')
    ax.set(yticks=range(len(cfg['plans'])),yticklabels=[p['id'] for p in cfg['plans']],xlabel='Tiempo físico desde t0 [h]',title='Una bomba hipotética de 50 m³/h · bloques V/r; huecos = esperas')
    ax.set_xlim(0,max(p['D_h'] for p in cfg['plans'])+16);save(fig,'e13_cronogramas.png')
    names=[p['plan'] for p in s['plans']];sc=[x['id'] for x in s['scenarios']]
    for key,threshold,label,name in [('Tmax_C',70,'Máximo global [°C]','e13_Tmax_escenarios.png'),('delta_C',20,'Máximo diferencial S25 [°C]','e13_delta_escenarios.png')]:
        a=np.array([[next(r[key] for r in rows if r['plan']==p and r['scenario']==x) for x in sc] for p in names]);fig,ax=plt.subplots(figsize=(13,4.3),layout='constrained');im=ax.imshow(a,aspect='auto',cmap='inferno');fig.colorbar(im,ax=ax,label=label)
        ax.set(xticks=range(len(sc)),xticklabels=sc,yticks=range(len(names)),yticklabels=names,title=f'{label} · límite {threshold} °C · cada columna conserva su fuente e historia');ax.tick_params(axis='x',rotation=70,labelsize=8)
        for i in range(len(names)):
            for j in range(len(sc)):ax.text(j,i,f'{a[i,j]:.1f}',ha='center',va='center',fontsize=6,color='cyan' if a[i,j]>threshold else 'white')
        save(fig,name)
    x=np.arange(len(s['plans']));fig,ax=plt.subplots(figsize=(11,3.6))
    for j,(key,label) in enumerate([('P_T','P(Tmax>70)'),('P_delta','P(ΔT>20)'),('P_joint','Pf conjunta OR')]):ax.bar(x+(j-1)*.24,[100*p[key] for p in s['plans']],width=.24,label=label)
    ax.axhline(5,color='red',ls='--',label='Límite 5 % conjunto');ax.set(xticks=x,xticklabels=names,ylabel='Peso de falla [%]',ylim=(0,110),title='Enumeración exacta del modelo discreto hipotético, no confiabilidad de obra');ax.tick_params(axis='x',rotation=12);ax.legend(ncol=2);save(fig,'e13_probabilidades.png')
    fig,ax=plt.subplots(figsize=(9,4))
    for i,p in enumerate(s['plans']):ax.scatter(p['D_h'],100*p['P_joint'],s=65,color=colors[i],label=p['plan'])
    ax.axhline(5,color='red',ls='--',label='5 %');ax.set(xlabel='Duración física D [h]',ylabel='Pf conjunta [%]',ylim=(-3,110),title='Duración–riesgo · menor duración solo entre planes factibles');ax.legend(fontsize=8,ncol=2);save(fig,'e13_duracion_riesgo.png')
    rep=folder/'representative'
    if rep.exists():out.extend(make_plots(rep,dest,ROOT/'vtk/e13',only={'e12_temperaturas.png','e12_diferencial.png','e12_secciones.png','e12_3d.png'}))
    return out
