"""Cinco figuras científicas de datos E07; sin utilizar la interfaz Bonsai."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.patches import Patch
from matplotlib.colors import ListedColormap,BoundaryNorm
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from .faces import exposed_faces,contacts

COLORS=['#315d92','#71b0d3','#e5ac45','#bc653e','#728952']


def create_figures(voxels,study,timeline,events,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);paths=[]
    grid=voxels.grid;origin=np.array(grid.origin);spacing=np.array(grid.spacing)
    pids=sorted(voxels.guid_by_id)
    palette=COLORS if len(pids)<=len(COLORS) else [plt.get_cmap('tab20')(i%20) for i in range(len(pids))]
    color_by_id={pid:palette[i] for i,pid in enumerate(pids)}
    faces=exposed_faces(voxels);quads=[];colors=[]
    elev=30;azim=-55;direction=np.array([np.cos(np.deg2rad(elev))*np.cos(np.deg2rad(azim)),np.cos(np.deg2rad(elev))*np.sin(np.deg2rad(azim)),np.sin(np.deg2rad(elev))])
    for index,axis,sign,pid,normal in zip(faces.indices,faces.axis,faces.sign,faces.pour_id,faces.normals):
        if normal@direction<=0:continue
        center=origin+(index+.5)*spacing;center[axis]+=sign*spacing[axis]/2
        a,b=[i for i in range(3) if i!=axis]
        quad=[]
        for sa,sb in ((-1,-1),(1,-1),(1,1),(-1,1)):
            point=center.copy();point[a]+=sa*spacing[a]/2;point[b]+=sb*spacing[b]/2;quad.append(point)
        quads.append(quad);colors.append(color_by_id[int(pid)])
    fig=plt.figure(figsize=(10,6.6),layout='constrained');ax=fig.add_subplot(projection='3d')
    ax.add_collection3d(Poly3DCollection(quads,facecolor=colors,edgecolor='none',antialiased=False))
    ax.set(xlim=(grid.origin[0],grid.upper[0]),ylim=(grid.origin[1],grid.upper[1]),zlim=(grid.origin[2],grid.upper[2]),xlabel='x [m]',ylabel='y [m]',zlabel='z [m]')
    ax.set_box_aspect(np.array(grid.upper)-origin);ax.view_init(elev=elev,azim=azim);ax.set_proj_type('ortho')
    ax.set_xticks(np.linspace(origin[0],grid.upper[0],3));ax.set_yticks(np.linspace(origin[1],grid.upper[1],3));ax.set_zticks(np.linspace(origin[2],grid.upper[2],5))
    fig.suptitle('IFC real → fundación voxelizada por centros\nΔ='+str(tuple(round(float(x),4) for x in grid.spacing))+' m · Python/IfcOpenShell')
    fig.legend(handles=[Patch(color=color_by_id[pid],label=f'Vertida {pid:02}') for pid in pids],loc='outside lower center',ncol=min(5,len(pids)))
    paths.append(out/'e07_fundacion_voxelizada.png');fig.savefig(paths[-1],dpi=170);plt.close(fig)
    fig,ax=plt.subplots(figsize=(7.5,4.8),layout='constrained')
    h=[row['spacing_m'][0] for row in study]
    errors=[100*row['relative_error'] for row in study]+[100*p['relative_error'] for row in study for p in row['by_pour']]
    ax.set_xscale('log')
    if any(error==0 for error in errors):
        positive=[error for error in errors if error>0]
        ax.set_yscale('symlog',linthresh=min(positive)/10 if positive else 1e-6)
    else:ax.set_yscale('log')
    ax.plot(h,[100*row['relative_error'] for row in study],'o-',label='Total frente a malla IFC',lw=2)
    for pid in voxels.guid_by_id:
        ax.plot(h,[100*next(p['relative_error'] for p in row['by_pour'] if p['vertida_id']==pid) for row in study],'.--',label=f'Vertida {pid:02}',alpha=.7)
    ax.set(xlabel='Tamaño de celda cúbica Δ [m]',ylabel='Error relativo absoluto [%]',title='Error de volumen · regla por centros\nOscilaciones de alineamiento; no se impone orden ni monotonía')
    ax.grid(which='both',alpha=.2);ax.legend(fontsize=8,ncol=2)
    paths.append(out/'e07_error_volumen.png');fig.savefig(paths[-1],dpi=180);plt.close(fig)
    fig,(ax,bars)=plt.subplots(1,2,figsize=(12,5),layout='constrained',width_ratios=[1.3,1])
    j=grid.shape[1]//2
    cmap=ListedColormap(['white',*[color_by_id[pid] for pid in pids]])
    norm=BoundaryNorm(np.arange(-.5,len(pids)+1.5),cmap.N)
    # El color depende de la posición en la leyenda, no del valor numérico ID.
    section_ids=voxels.vertida_id[:,j,:].T;display=np.zeros(section_ids.shape,dtype=int)
    for ordinal,pid in enumerate(pids,start=1):display[section_ids==pid]=ordinal
    ax.imshow(display,origin='lower',extent=[origin[0],grid.upper[0],origin[2],grid.upper[2]],cmap=cmap,norm=norm,interpolation='nearest',aspect='equal')
    segments=[]
    for index,axis,sign in zip(faces.indices,faces.axis,faces.sign):
        if index[1]!=j or axis==1:continue
        p=origin+(index+.5)*spacing;p[axis]+=sign*spacing[axis]/2;other=2 if axis==0 else 0
        a=p[[0,2]].copy();b=a.copy();a[0 if other==0 else 1]-=spacing[other]/2;b[0 if other==0 else 1]+=spacing[other]/2;segments.append([a,b])
    ax.add_collection(LineCollection(segments,colors='#147c9a',linewidths=1.2,label='Exterior final'))
    interfaces=contacts(voxels);segments=[]
    for index,axis in zip(interfaces['first'],interfaces['axis']):
        if index[1]!=j or axis==1:continue
        p=origin+(index+.5)*spacing;p[axis]+=spacing[axis]/2;other=2 if axis==0 else 0
        a=p[[0,2]].copy();b=a.copy();a[0 if other==0 else 1]-=spacing[other]/2;b[0 if other==0 else 1]+=spacing[other]/2;segments.append([a,b])
    ax.add_collection(LineCollection(segments,colors='#a71f35',linewidths=1.5,label='Interfaz interna'))
    ax.set(xlabel='x [m]',ylabel='z [m]',title=f'Corte y={grid.coordinates[1][j]:.3f} m');ax.legend(fontsize=8,loc='upper right')
    report=faces.report();names=list(report['area_by_orientation_m2']);areas=list(report['area_by_orientation_m2'].values())
    bars.bar(names,areas,color='#147c9a');bars.set(ylabel='Área staircase [m²]',xlabel='Normal exterior',title='Exterior final por orientación')
    fig.suptitle('Caras exteriores frente a interfaces · datos voxelizados reales')
    paths.append(out/'e07_superficies_interfaces.png');fig.savefig(paths[-1],dpi=180);plt.close(fig)
    fig,(ax,b)=plt.subplots(2,1,figsize=(8,6),layout='constrained')
    end=max(row['time_s'] for row in timeline)
    for event in events:
        if event.activation_s<=end:
            ax.broken_barh([(event.activation_s/3600,(end-event.activation_s)/3600)],(event.pour_id-.3,.6),facecolor=color_by_id[event.pour_id])
            ax.plot(event.activation_s/3600,event.pour_id,'ko',ms=3)
    ax.set(ylabel='VertidaID',yticks=[e.pour_id for e in events],title='Cronograma FICTICIO de demostración; no plan constructivo real')
    ax.set_xlim(0,max(end/3600,1/3600))
    b.step([r['time_s']/3600 for r in timeline],[r['active_volume_m3'] for r in timeline],where='post');b.set(xlabel='Tiempo [h]',ylabel='Volumen activo [m³]');b.grid(alpha=.2)
    paths.append(out/'e07_activacion_temporal.png');fig.savefig(paths[-1],dpi=180);plt.close(fig)
    fig,(a,b)=plt.subplots(1,2,figsize=(10,5.5),layout='constrained')
    for event in sorted(events,key=lambda event:event.pour_id):
        age=np.linspace(0,1.3*event.hydration.duration_s,400)
        a.plot(age/3600,event.hydration.adiabatic_temperature(age,event.material,event.initial_C),color=color_by_id[event.pour_id],label=f'Vertida {event.pour_id}')
        b.plot(age/3600,event.hydration.source(age),color=color_by_id[event.pour_id])
    a.set(xlabel='Edad real desde vertido [h]',ylabel='T adiabática prescrita [°C]')
    b.set(xlabel='Edad real [h]',ylabel='q̇_h [W/m³]')
    for axis in (a,b):axis.grid(alpha=.2)
    fig.legend(*a.get_legend_handles_labels(),loc='outside lower center',ncol=min(5,len(events)))
    fig.suptitle('Curvas PRELIMINARES por vertida · parámetros efectivos\nSin dependencia de temperatura ni pérdidas; curvas iguales pueden coincidir')
    paths.append(out/'e07_hidratacion_preliminar.png');fig.savefig(paths[-1],dpi=180);plt.close(fig)
    return [str(p) for p in paths]
