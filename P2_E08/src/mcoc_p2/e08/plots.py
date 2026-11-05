"""Figuras de temperaturas realmente integradas y balances, no de colocación."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from ..e07.faces import exposed_faces


def create_figures(voxels,result,study,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);paths=[]
    hours=result.times_s/3600
    fig,ax=plt.subplots(figsize=(9,5),layout='constrained')
    for pid in voxels.guid_by_id:
        values=[next(p['mean_C'] for p in row['by_pour'] if p['vertida_id']==pid) for row in result.metrics]
        ax.plot(hours,[np.nan if v is None else v for v in values],label=f'Vertida {pid}')
    ax.set(xlabel='Tiempo desde el inicio [h]',ylabel='Temperatura media [°C]',title='E08 · evolución térmica integrada por vertida')
    ax.legend(ncol=3);ax.grid(alpha=.2)
    paths.append('e08_temperaturas.png');fig.savefig(output/paths[-1],dpi=150);plt.close(fig)
    fig,(ax,b)=plt.subplots(2,1,figsize=(9,6),layout='constrained')
    rows=result.metrics;initial=result.energy['initial_J']
    ax.plot(hours,[(r['energy_J']-initial)/1e9 for r in rows],label='Cambio de energía sensible')
    ax.plot(hours,[(r['hydration_energy_J']-r['outward_energy_J']+r['placement_energy_J'])/1e9 for r in rows],'--',label='Hidratación − pérdidas + material entrante')
    ax.set(ylabel='Energía respecto al inicio [GJ]',title='Balance global con incorporación de material');ax.legend(fontsize=8);ax.grid(alpha=.2)
    b.plot(hours,[r['balance_residual_J'] for r in rows]);b.set(xlabel='Tiempo [h]',ylabel='Residuo [J]');b.grid(alpha=.2)
    paths.append('e08_energia.png');fig.savefig(output/paths[-1],dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,5),layout='constrained')
    h=[r['spacing_m'][0] for r in study]
    ax.plot(h,[100*r['relative_error'] for r in study],'o-',lw=2,label='Total')
    for pid in voxels.guid_by_id:
        ax.plot(h,[100*next(p['relative_error'] for p in r['by_pour'] if p['vertida_id']==pid) for r in study],'.--',label=f'Vertida {pid}',alpha=.6)
    ax.set(xlabel='Paso cúbico del estudio [m]',ylabel='Error de volumen [%]',title='Volumen: total y por pieza; no se presupone monotonía')
    ax.legend(ncol=2,fontsize=8);ax.grid(alpha=.2)
    paths.append('e08_volumen.png');fig.savefig(output/paths[-1],dpi=150);plt.close(fig)
    full=np.full(voxels.grid.shape,np.nan);full[voxels.occupation_mask]=result.temperature_C[-1]
    active=np.isfinite(full);faces=exposed_faces(voxels,active)
    origin=np.array(voxels.grid.origin);spacing=np.array(voxels.grid.spacing)
    quads=[];temperatures=[]
    direction=np.array([.47,-.67,.57])
    for index,axis,sign,normal in zip(faces.indices,faces.axis,faces.sign,faces.normals):
        if normal@direction<=0:continue
        center=origin+(index+.5)*spacing;center[axis]+=sign*spacing[axis]/2
        a,b=[i for i in range(3) if i!=axis];quad=[]
        for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]:
            point=center.copy();point[a]+=x*spacing[a]/2;point[b]+=y*spacing[b]/2;quad.append(point)
        quads.append(quad);temperatures.append(full[tuple(index)])
    fig=plt.figure(figsize=(9,6),layout='constrained');ax=fig.add_subplot(projection='3d')
    finite=result.temperature_C[np.isfinite(result.temperature_C)]
    low=float(finite.min()) if finite.size else 0.;high=max(low+1,float(finite.max())) if finite.size else 1.
    norm=plt.Normalize(low,high);cmap=plt.get_cmap('inferno')
    if quads:ax.add_collection3d(Poly3DCollection(quads,facecolor=cmap(norm(temperatures)),edgecolor='none'))
    ax.set(xlim=(origin[0],voxels.grid.upper[0]),ylim=(origin[1],voxels.grid.upper[1]),zlim=(origin[2],voxels.grid.upper[2]),xlabel='x [m]',ylabel='y [m]',zlabel='z [m]')
    ax.set_box_aspect(np.array(voxels.grid.upper)-origin);ax.view_init(30,-55);ax.set_proj_type('ortho')
    ax.set_xticks(np.linspace(origin[0],voxels.grid.upper[0],3));ax.set_yticks(np.linspace(origin[1],voxels.grid.upper[1],3))
    ax.set_zticks(np.linspace(origin[2],voxels.grid.upper[2],5));ax.tick_params(labelsize=9)
    ax.set_title(f'Temperatura calculada · t={hours[-1]:g} h')
    fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap=cmap),ax=ax,label='T [°C]',shrink=.6)
    paths.append('e08_final_3d.png');fig.savefig(output/paths[-1],dpi=150);plt.close(fig)
    return ['figures/'+name for name in paths]
