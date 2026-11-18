"""Figuras científicas de datos E12 reales; sin reconstruir geometría alternativa."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ..e11.pipeline import ROOT
from ..e11.weather import validate
from .source import read_sources,load_curve
from .pipeline import arrays

def make_plots(folder,destination,vtk_folder=None,*,only=None):
    folder=Path(folder);dest=Path(destination);dest.mkdir(parents=True,exist_ok=True)
    s=json.loads((folder/'summary.json').read_text(encoding='utf8'));c=s['configuration'];g=arrays(folder/'grid.npz');f=arrays(folder/'fields.npz');a=arrays(folder/'statistics.npz');steps=arrays(folder/'weather_steps.npz');paths=[]
    plt.rcParams.update({'font.size':10,'axes.grid':True,'grid.alpha':.2,'figure.dpi':130})
    def save(fig,name):
        if only is not None and name not in only:plt.close(fig);return
        path=dest/(name.replace('e12_',s.get('delivery','E12').lower()+'_'));fig.savefig(path,dpi=160,bbox_inches='tight');plt.close(fig);paths.append(path.relative_to(ROOT).as_posix())
    curve,_=load_curve(ROOT/c['experimental_source']['file'],c['experimental_source']['curve'],c['experimental_source']['tail'],c['experimental_source'].get('tau_s',86400))
    sources,_=read_sources(ROOT/c['experimental_source']['file'])
    fig,ax=plt.subplots(1,2,figsize=(11,3.7))
    for name in list(sources)[:4]:
        t,q=sources[name];ax[0].plot(t/3600,q,label=name,lw=2.5 if name==curve.name else 1,alpha=1 if name==curve.name else .5)
    t=np.linspace(0,336,2000);ax[1].plot(t,curve.primitive(t*3600)/1e6,color='#a33e27',label=curve.name)
    ax[0].set(xlabel='Edad desde activación [h]',ylabel='Fuente [W/m³]',title='SS original: selección por representatividad')
    ax[1].set(xlabel='Edad desde activación [h]',ylabel='Calor acumulado [MJ/m³]',title='Integral exacta de fuente lineal; cola nula')
    for a0 in ax:a0.legend()
    save(fig,'e12_fuente.png')
    snap=validate(ROOT/c['snapshot']);origin=np.array(snap.seconds)-__import__('mcoc_p2.e10.weather',fromlist=['utc_time']).utc_time(c['simulation_start_utc']).timestamp()
    fig,ax=plt.subplots(figsize=(10,3.5));ax.plot(origin/3600,snap.air,color='#1e6f80');ax.axvspan(0,c['physics']['t_end_s']/3600,color='#e8b96d',alpha=.18,label='Ventana simulada, sin extensión')
    ax.set(xlabel='Horas respecto del inicio '+s.get('delivery','E12'),ylabel='Temperatura ambiente [°C]',title='Forecast Open-Meteo congelado · '+snap.metadata['retrieved_at_utc']);ax.legend();save(fig,'e12_clima.png')
    t=a['weather_time_s']/3600;valid=a['weather_probe_valid'];pv=a['weather_probe_temperature_C']
    fig,ax=plt.subplots(figsize=(11,4.4))
    ax.plot(t,a['weather_Tmax_C'],label='Máximo de Ω activo',color='#ad3b28',lw=2)
    ax.plot(t,np.where(valid[:,0],pv[:,0],np.nan),label='Núcleo: centro de celda',color='#b27a24')
    ax.plot(t,np.where(valid[:,1],pv[:,1],np.nan),label='Cara superior reconstruida',color='#388a91')
    ax.plot(t,a['weather_S25min_C'],label='Mínimo global a ≈25 mm (aprox.)',color='#244866')
    ax.plot(t,a['weather_ambient_C'],label='Ambiente',color='#6b747c',alpha=.7)
    ax.axhline(70,color='red',ls='--',label='Límite docente 70 °C');ax.set(xlabel='Tiempo [h]',ylabel='Temperatura [°C]',xlim=(0,c['physics']['t_end_s']/3600),title=s.get('delivery','E12')+f' · {c["physics"]["t_end_s"]/3600:g} h · '+curve.name);ax.legend(ncol=2);save(fig,'e12_temperaturas.png')
    fig,ax=plt.subplots(figsize=(10,3.8))
    ax.plot(t,a['weather_delta25_C'],label='Máximo activo − mínimo S25',lw=2,color='#a13b32')
    ax.plot(t,a['weather_Tmax_C']-a['weather_face_min_C'],label='Referencia: mínimo en cara (0 mm)',alpha=.7)
    ax.plot(t,a['weather_Tmax_C']-a['weather_boundary_cell_min_C'],label='Referencia: centro de celda de borde',alpha=.7)
    ax.axhline(20,color='red',ls='--',label='Límite docente 20 °C');ax.set(xlabel='Tiempo [h]',ylabel='Diferencial [°C]',title='Criterio global del curso; no diferencia entre dos sondas arbitrarias');ax.legend(ncol=2);save(fig,'e12_diferencial.png')
    fig,ax=plt.subplots(figsize=(10,3.8));tt=steps['end_s']/3600
    for key,label in [('hydration_energy_J','Hidratación'),('outward_energy_J','Salida neta aire + suelo'),('placement_energy_J','Colocación posterior a t=0')]:
        ax.plot(tt,np.cumsum(steps[key])/1e9,label=label)
    internal=s['energy']['weather']['initial_J']+np.cumsum(steps['hydration_energy_J']-steps['outward_energy_J']+steps['placement_energy_J'])
    ax.plot(tt,internal/1e9,label='Energía sensible, referencia 20 °C',ls='--')
    ax.set(xlabel='Tiempo [h]',ylabel='Energía [GJ]',title='Balance conservativo: acumulación, fuente y pérdidas');ax.legend();save(fig,'e12_energia.png')
    # Cortes de campos reales, incluidos los dos máximos exactos.
    times=[s['global_maximum']['time_s'],s['global_delta25_maximum']['time_s'],c['physics']['t_end_s']]
    fig,axs=plt.subplots(2,3,figsize=(12,6.5),layout='constrained');origin=g['origin_m'];spacing=g['spacing_m'];shape=g['vertida_id'].shape
    z=int(np.clip(round((1.65-origin[2])/spacing[2]-.5),0,shape[2]-1));y=int(np.clip(round((0-origin[1])/spacing[1]-.5),0,shape[1]-1))
    extent=[origin[0],origin[0]+shape[0]*spacing[0],origin[1],origin[1]+shape[1]*spacing[1]]
    lower=min(15.,float(a['weather_Tmin_C'].min()));upper=s['global_maximum']['temperature_C']
    for j,time_s in enumerate(times):
        frame=int(np.argmin(abs(f['times_s']-time_s)));T=np.full(shape,np.nan);flat=T.ravel();flat[g['occupied_flat_indices']]=np.where(f['active'][frame],f['weather_C'][frame],np.nan)
        im=axs[0,j].imshow(T[:,:,z].T,origin='lower',extent=extent,cmap='inferno',vmin=lower,vmax=upper);axs[0,j].set(title=f'XY · z={origin[2]+(z+.5)*spacing[2]:.3f} m · {time_s/3600:.2f} h',xlabel='X [m]',ylabel='Y [m]')
        axs[1,j].imshow(T[:,y,:].T,origin='lower',extent=[extent[0],extent[1],origin[2],origin[2]+shape[2]*spacing[2]],aspect='auto',cmap='inferno',vmin=lower,vmax=upper);axs[1,j].set(title=f'XZ · y={origin[1]+(y+.5)*spacing[1]:.3f} m · {time_s/3600:.2f} h',xlabel='X [m]',ylabel='Z [m]')
    fig.colorbar(im,ax=axs,label='Temperatura [°C]',shrink=.85);save(fig,'e12_secciones.png')
    # Columna más próxima al eje IFC, solo celdas ocupadas.
    indices=np.argwhere(g['occupation_mask']);xyz=origin+(indices+.5)*spacing
    dist=np.sum(xyz[:,:2]**2,axis=1);column=indices[int(np.argmin(dist)),:2]
    select=np.flatnonzero(np.all(indices[:,:2]==column,axis=1));select=select[np.argsort(xyz[select,2])]
    fig,ax=plt.subplots(figsize=(10,4))
    zvalues=xyz[select,2];T=np.where(f['active'][:,select],f['weather_C'][:,select],np.nan)
    im=ax.pcolormesh(f['times_s']/3600,zvalues,T.T,shading='nearest',cmap='inferno',vmin=lower,vmax=upper);fig.colorbar(im,ax=ax,label='Temperatura [°C]')
    ax.set(xlabel='Tiempo [h]',ylabel='Altura del centro [m]',title='Tiempo–altura · columna ocupada próxima al eje · vacío/futuro sin color');save(fig,'e12_tiempo_altura.png')
    if vtk_folder is not None and (Path(vtk_folder)/'manifest.json').exists():
        import pyvista as pvlib
        m=json.loads((Path(vtk_folder)/'manifest.json').read_text());row=min(m['states'],key=lambda x:abs(x['time_h']-s['global_maximum']['time_h']))
        live=pvlib.read(Path(vtk_folder)/row['file']).threshold(.5,scalars='active')
        plot=pvlib.Plotter(shape=(1,3),off_screen=True,window_size=(1740,590))
        for j,mode in enumerate(['full','slice','clip']):
            plot.subplot(0,j);plot.set_background('#142638')
            mesh=live if mode=='full' else live.slice(normal='y',origin=(0,0,1.65)) if mode=='slice' else live.clip(normal='y',origin=(0,0,1.65))
            plot.add_mesh(mesh,scalars='temperature_C',cmap='inferno',clim=(lower,upper),show_edges=False,scalar_bar_args={'title':'T [degC] · escala comun','color':'white','title_font_size':12,'label_font_size':11,'position_y':.05})
            plot.add_text(f'{s.get("delivery","E12")} · {mode} · {row["time_h"]:.2f} h',font_size=11,color='white');plot.show_axes();plot.camera_position='iso'
            if mode=='full':
                stat=int(np.argmin(abs(a['weather_time_s']-row['time_h']*3600)))
                choices=[k for k in range(2) if a['weather_probe_valid'][stat,k]]
                labels=[('Nucleo (centro)' if k==0 else 'Cara superior')+f" {a['weather_probe_temperature_C'][stat,k]:.2f} C" for k in choices]
                if choices:plot.add_point_labels(np.array([s['probes'][k]['coordinate_m'] for k in choices]),labels,always_visible=True,point_color='cyan',point_size=7,font_size=12,text_color='white',shape_color='#263746',shape_opacity=.8)
        path=dest/(s.get('delivery','E12').lower()+'_3d.png');plot.screenshot(path);plot.close();paths.append(path.relative_to(ROOT).as_posix())
    return paths

