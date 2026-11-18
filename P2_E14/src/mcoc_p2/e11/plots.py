"""Figuras de datos guardados; no se descargan ni modifican campos térmicos."""
import hashlib,json
from datetime import datetime,timezone,timedelta
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from .weather import validate,ROOT
from ..e10.weather import utc_time


def plot_weather(snapshot,output):
    s=validate(snapshot);output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    dates=[datetime.fromtimestamp(t,timezone.utc) for t in s.seconds]
    fig,ax=plt.subplots(figsize=(10,4),layout='constrained')
    ax.plot(dates,s.air,'o-',ms=2,color='#287e91')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m\n%H:%M',tz=timezone.utc))
    ax.set(xlabel='Fecha/hora UTC',ylabel='Temperatura ambiente [°C]',
           title='Open-Meteo · pronóstico horario real · NO observaciones')
    ax.grid(alpha=.2);fig.suptitle(Path(snapshot).name,fontsize=9)
    fig.savefig(output,dpi=160);plt.close(fig)
    return str(output)


def make_plots(folder,output):
    folder=Path(folder);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    s=json.loads((folder/'summary.json').read_text(encoding='utf-8'))
    with np.load(folder/'statistics.npz') as z:a={k:z[k] for k in z.files}
    with np.load(folder/'fields.npz') as z:f={k:z[k] for k in z.files}
    with np.load(folder/'grid.npz') as z:g={k:z[k] for k in z.files}
    names=[];field_sha=hashlib.sha256((folder/'fields.npz').read_bytes()).hexdigest()
    def save(fig,name):
        fig.savefig(output/name,dpi=160,metadata={'Description':'Solver fields SHA256 '+field_sha});plt.close(fig);names.append(name)
    plot_weather(ROOT/s['configuration']['snapshot'],output/'e11_ambiente.png');names.append('e11_ambiente.png')
    fig,ax=plt.subplots(figsize=(9,4),layout='constrained')
    for name,color,label in [('weather','#a93d34','Pronóstico variable'),('constant','#2b6a90','Referencia constante')]:
        ax.plot(a[name+'_time_s']/3600,a[name+'_Tmax_C'],c=color,label=label)
    ax.set(xlabel='Tiempo relativo de simulación [h]',ylabel='T máxima activa [°C]',title='Fundación IFC: misma física y pasos; solo cambia T ambiente')
    fig.suptitle(s['simulation_start_utc']+' → '+s['simulation_end_utc'],fontsize=10)
    ax.legend();ax.grid(alpha=.2);save(fig,'e11_tmax.png')
    fig,axes=plt.subplots(3,2,figsize=(12,10),layout='constrained')
    t=a['weather_time_s']/3600
    for name,style in [('weather','-'),('constant','--')]:
        valid=a[name+'_probe_valid'];pv=np.where(valid,a[name+'_probe_temperature_C'],np.nan)
        axes[0,0].plot(t,a[name+'_ambient_C'],style,label=name)
        for j in range(3):axes[(j+1)//2,(j+1)%2].plot(t,pv[:,j],style,label=name)
        axes[2,0].plot(t,pv[:,0]-pv[:,1],style,label=name)
        with np.load(folder/(name+'_steps.npz')) as steps:
            axes[2,1].plot(steps['start_s']/3600,steps['outward_energy_J']/steps['dt_s']/1000,style,label=name)
    titles=['Ambiente [°C]','Núcleo: centro de celda [°C]','Cara superior de hormigón [°C]','Cara lateral de hormigón [°C]','Núcleo − cara superior [°C]','Potencia neta saliente: aire + suelo [kW]']
    for ax,title in zip(axes.flat,titles):ax.set(title=title,xlabel='Tiempo simulado [h]');ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Pronóstico vs 20 °C · '+s['simulation_start_utc']+' → '+s['simulation_end_utc'],fontsize=12)
    save(fig,'e11_comparacion.png')
    # Potencia instantánea al aire separada del suelo, calculada desde cada
    # campo guardado; no confundir estas muestras con la integral de pasos.
    from .pipeline import make_environment,ConstantWeather
    from .weather import window
    from ..e07.voxel import VoxelGrid,Voxelization
    from ..e07.coupling import MaskedAssembly
    from ..e08.inputs import events_from_config
    c=s['configuration'];p=c['physics'];rows=s['grid']['by_pour']
    vox=Voxelization(VoxelGrid(tuple(g['origin_m']),tuple(g['spacing_m']),g['vertida_id'].shape),g['vertida_id'],
                     {r['vertida_id']:r['guid'] for r in rows},{r['vertida_id']:r['volume_reference_m3'] for r in rows})
    materials={e.pour_id:e.material for e in events_from_config(p)}
    weather=window(ROOT/c['snapshot'],c['simulation_start_utc'],p['t_end_s'])
    fig,axes=plt.subplots(2,1,figsize=(10,6),layout='constrained')
    for name,w in [('weather',weather),('constant',ConstantWeather(weather,c['constant_reference_C']))]:
        env=make_environment(vox,w,c['environment']);air=[];soil=[]
        for frame,t in enumerate(f['times_s']):
            mask=np.zeros(vox.grid.shape,dtype=bool);mask.flat[g['occupied_flat_indices']]=f['active'][frame]
            T=np.zeros(vox.grid.shape);T.flat[g['occupied_flat_indices']]=f[name+'_C'][frame]
            assembly=MaskedAssembly(vox,mask,materials);env(assembly,t)
            faces=assembly.faces;ground=(faces.axis==2)&(faces.sign==-1)&(faces.indices[:,2]==env.base_index)
            power=assembly.face_g*(T[assembly.face_indices]-assembly.reservoir)+assembly.prescribed
            air.append(power[~ground].sum()/1000);soil.append(power[ground].sum()/1000)
        axes[0].plot(f['times_s']/3600,air,'o-',ms=3,label=name)
        axes[1].plot(f['times_s']/3600,soil,'o-',ms=3,label=name)
    for ax,title in zip(axes,['Potencia al aire por convección (incluye resistencia de moldaje)','Potencia a suelo resistivo']):
        ax.set(title=title,xlabel='Tiempo relativo [h]',ylabel='Potencia saliente [kW]');ax.axhline(0,c='gray',lw=.5);ax.grid(alpha=.2);ax.legend()
    fig.suptitle('Muestras instantáneas de campos guardados · positivo = pérdida de hormigón')
    save(fig,'e11_flujos.png')
    shape=g['vertida_id'].shape;j=int(np.argmin(abs(g['origin_m'][1]+(np.arange(shape[1])+.5)*g['spacing_m'][1])))
    values=[]
    for key in ('weather_C','constant_C'):
        full=np.zeros(np.prod(shape));full[g['occupied_flat_indices']]=f[key][-1];values.append(full.reshape(shape)[:,j,:].T)
    mask_full=np.zeros(np.prod(shape),dtype=bool);mask_full[g['occupied_flat_indices']]=f['active'][-1]
    mask=mask_full.reshape(shape)[:,j,:].T;extent=[g['origin_m'][0],g['origin_m'][0]+shape[0]*g['spacing_m'][0],g['origin_m'][2],g['origin_m'][2]+shape[2]*g['spacing_m'][2]]
    fig,axes=plt.subplots(3,1,figsize=(10,8),layout='constrained')
    for ax,v,title in zip(axes,[*values,values[0]-values[1]],['Temperatura: pronóstico','Temperatura: constante','Diferencia pronóstico − constante']):
        kwargs=dict(cmap='inferno',vmin=min(vv[mask].min() for vv in values),vmax=max(vv[mask].max() for vv in values)) if ax!=axes[2] else dict(cmap='coolwarm',vmin=-max(abs((values[0]-values[1])[mask]).max(),1e-6),vmax=max(abs((values[0]-values[1])[mask]).max(),1e-6))
        im=ax.imshow(np.ma.masked_where(~mask,v),origin='lower',extent=extent,**kwargs)
        ax.set(title=title,xlabel='X [m]',ylabel='Z [m]');fig.colorbar(im,ax=ax,label='°C',shrink=.75)
    fig.suptitle('Campo final calculado · '+s['simulation_end_utc']);save(fig,'e11_campos_finales.png')
    return dict(files=names,fields_sha256=field_sha)
