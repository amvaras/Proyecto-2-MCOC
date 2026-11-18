"""Figuras científicas regenerables exclusivamente desde IFC y arrays guardados."""
import hashlib
import io
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize,ListedColormap
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from PIL import Image
from ..e07.ifc import read_pours
from ..e07.voxel import VoxelGrid,Voxelization
from ..e07.faces import exposed_faces

ROOT=Path(__file__).resolve().parents[3]
COLORS=['#4679a8','#72b9c4','#e2b35b','#c8704c','#748b59']
GRAY='#c9cdd1'


def load_result(folder):
    folder=Path(folder)
    summary=json.loads((folder/'summary.json').read_text(encoding='utf-8'))
    with np.load(folder/'grid.npz') as z:grid={k:z[k] for k in z.files}
    with np.load(folder/'temperature.npz') as z:data={k:z[k] for k in z.files}
    with np.load(folder/'statistics.npz') as z:stats={k:z[k] for k in z.files}
    shape=grid['vertida_id'].shape
    vg=VoxelGrid(tuple(grid['origin_m']),tuple(grid['spacing_m']),shape)
    voxels=Voxelization(vg,grid['vertida_id'],{r['vertida_id']:r['guid'] for r in summary['grid']['by_pour']},
                       {r['vertida_id']:r['volume_reference_m3'] for r in summary['grid']['by_pour']})
    return summary,grid,data,stats,voxels


def full_frame(grid,data,frame):
    shape=grid['vertida_id'].shape;flat=grid['occupied_flat_indices']
    field=np.zeros(np.prod(shape));active=np.zeros(np.prod(shape),dtype=bool)
    field[flat]=data['temperature_C'][frame];active[flat]=data['active_mask'][frame]
    return field.reshape(shape),active.reshape(shape)


def cut_payload(grid,data,frame,kind,horizontal_z=1.65):
    field,active=full_frame(grid,data,frame);ids=grid['vertida_id']
    j=int(np.argmin(abs(grid['y_m'])));k=int(np.argmin(abs(grid['z_m']-horizontal_z)))
    if kind=='vertical':values=field[:,j,:].T;valid=active[:,j,:].T;solid=ids[:,j,:].T>0;actual=float(grid['y_m'][j])
    elif kind=='horizontal':values=field[:,:,k].T;valid=active[:,:,k].T;solid=ids[:,:,k].T>0;actual=float(grid['z_m'][k])
    else:raise ValueError('Corte desconocido')
    return dict(values=values,valid=valid,future=solid&~valid,coordinate_m=actual)


def _draw_cut(ax,grid,data,frame,kind,z,norm):
    p=cut_payload(grid,data,frame,kind,z);o=grid['origin_m'];upper=o+np.array(grid['vertida_id'].shape)*grid['spacing_m']
    extent=[o[0],upper[0],o[2],upper[2]] if kind=='vertical' else [o[0],upper[0],o[1],upper[1]]
    ax.imshow(np.ma.masked_where(~p['future'],p['future']),origin='lower',extent=extent,cmap=ListedColormap([GRAY]),vmin=0,vmax=1,interpolation='nearest')
    im=ax.imshow(np.ma.masked_where(~p['valid'],p['values']),origin='lower',extent=extent,cmap='inferno',norm=norm,interpolation='nearest')
    ax.set(xlabel='X [m]',ylabel='Z [m]' if kind=='vertical' else 'Y [m]')
    ax.set_aspect('equal')
    return im,p['coordinate_m']


def face_geometry(voxels,half=True):
    mask=voxels.occupation_mask.copy()
    if half:
        j=int(np.argmin(abs(voxels.grid.coordinates[1])))
        mask[:,:j,:]=False
    faces=exposed_faces(voxels,mask)
    centers=np.array(voxels.grid.origin)+(faces.indices+.5)*np.array(voxels.grid.spacing)
    centers[np.arange(len(centers)),faces.axis]+=faces.sign*np.array(voxels.grid.spacing)[faces.axis]/2
    quads=[]
    for center,axis in zip(centers,faces.axis):
        axes=[i for i in range(3) if i!=axis]
        quad=np.tile(center,(4,1))
        for q,(a,b) in enumerate([(-1,-1),(1,-1),(1,1),(-1,1)]):
            quad[q,axes[0]]+=a*voxels.grid.spacing[axes[0]]/2;quad[q,axes[1]]+=b*voxels.grid.spacing[axes[1]]/2
        quads.append(quad)
    return faces,np.array(quads)


def _set_3d(ax,voxels,azim,elev,half=True):
    o=voxels.grid.origin;u=voxels.grid.upper
    y0=0 if half else o[1]
    ax.set(xlim=(o[0],u[0]),ylim=(y0,u[1]),zlim=(o[2],u[2]))
    ax.set_box_aspect((u[0]-o[0],u[1]-y0,u[2]-o[2]))
    ax.set_proj_type('ortho');ax.view_init(elev=elev,azim=azim)
    ax.set_xticks([-9,0,9]);ax.set_yticks([0,9] if half else [-9,0,9]);ax.set_zticks([0,2.2,4.3])
    ax.tick_params(labelsize=6,pad=0)
    ax.set_xlabel('X [m]',fontsize=7,labelpad=0);ax.set_ylabel('Y [m]',fontsize=7,labelpad=0);ax.set_zlabel('Z [m]',fontsize=7,labelpad=0)


def generate_figures(folder,output,*,animation=True,azim=-62,elev=26):
    if not np.isfinite([azim,elev]).all():raise ValueError('Ángulos de vista finitos')
    folder=Path(folder).resolve();output=Path(output).resolve()
    if not folder.is_relative_to(ROOT) or not output.is_relative_to(ROOT):raise ValueError('Figuras y resultados dentro de la entrega')
    output.mkdir(parents=True,exist_ok=True)
    s,g,d,a,v=load_result(folder)
    field_sha=hashlib.sha256((folder/'temperature.npz').read_bytes()).hexdigest()
    live=a['active_count']>0;lo=float(a['Tmin_C'][live].min());hi=float(a['Tmax_C'][live].max())
    norm=Normalize(lo,hi if hi>lo else lo+1)
    horizon=float(d['times_s'][-1]/3600);requested=s['configuration']['analysis'].get('panel_hours',[0,horizon])
    hours=sorted({float(h) for h in requested if h<=horizon}|{horizon})
    frames=sorted({int(np.argmin(abs(d['times_s']/3600-h))) for h in hours})
    manifest=dict(field_sha256=field_sha,plot_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  color_range_C=[norm.vmin,norm.vmax],panel_frames=frames,
                  panel_times_h=(d['times_s'][frames]/3600).tolist(),files={},source='Arrays reales; sin interpolación temporal ni modificación del solver')
    def save(fig,name,kind,extra=None):
        fig.savefig(output/name,dpi=160,metadata={'Description':json.dumps(dict(field_sha256=field_sha,kind=kind),ensure_ascii=False)})
        plt.close(fig);manifest['files'][name]=dict(kind=kind,sha256=hashlib.sha256((output/name).read_bytes()).hexdigest(),**(extra or {}))
    plt.rcParams.update({'font.size':9,'axes.titlesize':10,'figure.titlesize':14})
    # BIM: triángulos originales, sin sustituir por una reconstrucción idealizada.
    solids,_=read_pours(ROOT/s['ifc']['relative_path'])
    fig=plt.figure(figsize=(10,5.5),layout='constrained');ax=fig.add_subplot(111,projection='3d')
    triangles=[];colors=[]
    camera=np.array([np.cos(np.deg2rad(elev))*np.cos(np.deg2rad(azim)),np.cos(np.deg2rad(elev))*np.sin(np.deg2rad(azim)),np.sin(np.deg2rad(elev))])
    for solid in solids:
        mesh=solid.mesh.vertices[solid.mesh.triangles]
        normals=np.cross(mesh[:,1]-mesh[:,0],mesh[:,2]-mesh[:,0])
        keep=normals@camera>1e-10
        # En estos sólidos convexos, tres vértices dentro de otro sólido
        # garantizan que todo el triángulo está enterrado en una interfaz.
        for other in solids:
            if other.pour_id!=solid.pour_id and other.mesh.convex:
                buried=(other.mesh.classify(mesh.reshape(-1,3))>=0).reshape(-1,3).all(axis=1)
                keep &= ~buried
        mesh=mesh[keep];triangles.extend(mesh);colors.extend([COLORS[(solid.pour_id-1)%5]]*len(mesh))
    ax.add_collection3d(Poly3DCollection(triangles,facecolors=colors,edgecolors='none'))
    _set_3d(ax,v,azim,elev,False);ax.set_title('Geometría BIM original · mallas del IFC real')
    fig.legend(handles=[Patch(color=COLORS[i],label=f'Vertida {i+1}') for i in range(5)],loc='lower center',ncol=5)
    fig.suptitle('Fundación G2 · IfcOpenShell / Matplotlib · no es captura Bonsai')
    save(fig,'e09_bim.png','ifc_mesh',{'ifc_sha256':s['ifc']['sha256']})
    # Vóxeles por ID.
    faces,quads=face_geometry(v,False)
    fig=plt.figure(figsize=(10,5.5),layout='constrained');ax=fig.add_subplot(111,projection='3d')
    ax.add_collection3d(Poly3DCollection(quads,facecolors=[COLORS[(int(p)-1)%5] for p in faces.pour_id],edgecolors='none'))
    _set_3d(ax,v,azim,elev,False);ax.set_title(f"Voxelización por centros · {s['grid']['occupied_cells']:,} celdas ocupadas")
    fig.suptitle('Cinco vertidas conservan identidad IFC')
    fig.legend(handles=[Patch(color=COLORS[i],label=f'Vertida {i+1}') for i in range(5)],loc='lower center',ncol=5)
    save(fig,'e09_voxelizacion.png','voxel_labels')
    fig,ax=plt.subplots(figsize=(8,4.8),layout='constrained')
    study=s['volume_study'];hs=[r['spacing_m'][0] for r in study]
    ax.plot(hs,[100*r['relative_error'] for r in study],'ko-',label='Error total',lw=2)
    for pid in v.guid_by_id:
        ax.plot(hs,[100*next(p['relative_error'] for p in r['by_pour'] if p['vertida_id']==pid) for r in study],'.--',label=f'Vertida {pid}')
    ax.set(xlabel='Paso cúbico del estudio [m]',ylabel='Error de volumen [%]',title='Error total y por vertida · refinamiento no necesariamente monótono');ax.legend(ncol=3);ax.grid(alpha=.25)
    save(fig,'e09_error_volumen.png','volume_study')
    t=a['time_s']/3600;valid=a['probe_valid'];pv=np.where(valid,a['probe_temperature_C'],np.nan)
    fig,ax=plt.subplots(figsize=(10,4.5),layout='constrained')
    ax.plot(t,a['Tmax_C'],label='Máxima',color='#ba3f34',lw=2);ax.plot(t,a['Tmean_C'],label='Media activa',color='#547b8d');ax.plot(t,a['Tmin_C'],label='Mínima',color='#337eb1')
    if (folder/'control.npz').exists():
        with np.load(folder/'control.npz') as control:ax.plot(control['time_s']/3600,control['Tmax_C'],'--',c='#777777',label='Máxima sin hidratación')
    ax.axhline(70,c='black',ls=':',lw=1,label='70 °C: referencia del curso')
    for event in s['configuration']['physics']['events']:ax.axvline(event['activation_s']/3600,c='#b9bec1',lw=.6)
    ax.set(xlabel='Tiempo desde primera colocación [h]',ylabel='Temperatura [°C]',title='Temperatura del dominio activo · cada paso de integración')
    ax.legend(ncol=3,fontsize=8);ax.grid(alpha=.2);save(fig,'e09_tmax.png','statistics_every_step')
    fig,(ax,b)=plt.subplots(2,1,figsize=(10,7),layout='constrained')
    labels=['Núcleo (centro de celda)','Cara superior (Robin)','Cara lateral (Robin)','Cerca de base (centro)']
    for j,label in enumerate(labels):ax.plot(t,pv[:,j],label=label)
    ax.set(ylabel='Temperatura [°C]',title='Sondas fijas · caras reconstruidas y centros diferenciados');ax.legend(ncol=2,fontsize=8);ax.grid(alpha=.2)
    for j,p in enumerate(s['thermal']['probes'][4:],start=4):b.plot(t,pv[:,j],label='Vertida '+str(p['vertida_id']))
    b.set(xlabel='Tiempo [h]',ylabel='Temperatura en centro representativo [°C]');b.legend(ncol=5,fontsize=8);b.grid(alpha=.2)
    save(fig,'e09_sondas.png','fixed_probes')
    fig,ax=plt.subplots(figsize=(10,4),layout='constrained');delta=pv[:,0]-pv[:,1]
    ax.plot(t,delta,c='#a84236',lw=2);ax.axhline(20,c='black',ls='--',label='20 °C: referencia del curso')
    ax.set(xlabel='Tiempo [h]',ylabel='T núcleo − T cara superior [°C]',title='Diferencia vertical en la misma línea · válida cuando existen ambas sondas')
    ax.legend();ax.grid(alpha=.25);save(fig,'e09_diferencia.png','center_top_difference')
    # Cortes, escala y ejes comparables.
    z=s['configuration']['analysis'].get('horizontal_z_m',1.65)
    for kind in ('vertical','horizontal'):
        cols=3;rows=int(np.ceil(len(frames)/cols))
        fig,axes=plt.subplots(rows,cols,figsize=(13,3.2*rows),layout='constrained',squeeze=False)
        for ax,frame in zip(axes.flat,frames):
            im,coordinate=_draw_cut(ax,g,d,frame,kind,z,norm)
            ax.set_title(f"t={d['times_s'][frame]/3600:g} h · {'Y' if kind=='vertical' else 'Z'}={coordinate:.3f} m")
        for ax in list(axes.flat)[len(frames):]:ax.axis('off')
        fig.colorbar(im,ax=list(axes.flat),label='Temperatura [°C]',shrink=.7)
        fig.suptitle(f"Cortes {'verticales' if kind=='vertical' else 'horizontales'} · gris=futuro, blanco=vacío")
        save(fig,f'e09_cortes_{kind}.png','spatial_cut',dict(frames=frames,coordinate_m=coordinate))
    faces,quads=face_geometry(v,True)
    lookup=np.full(v.grid.shape,-1,dtype=int);lookup[v.occupation_mask]=np.arange(v.occupation_mask.sum())
    cell_lookup=lookup[tuple(faces.indices.T)]
    direction=np.array([np.cos(np.deg2rad(elev))*np.cos(np.deg2rad(azim)),np.cos(np.deg2rad(elev))*np.sin(np.deg2rad(azim)),np.sin(np.deg2rad(elev))])
    visible=faces.normals@direction>0
    fig=plt.figure(figsize=(14,3.4*int(np.ceil(len(frames)/3))),layout='constrained')
    for n,frame in enumerate(frames):
        ax=fig.add_subplot(int(np.ceil(len(frames)/3)),3,n+1,projection='3d')
        active=d['active_mask'][frame,cell_lookup];colors=plt.colormaps['inferno'](norm(d['temperature_C'][frame,cell_lookup]));colors[~active]=matplotlib.colors.to_rgba(GRAY)
        ax.add_collection3d(Poly3DCollection(quads[visible],facecolors=colors[visible],edgecolors='none'))
        _set_3d(ax,v,azim,elev,True)
        ids=np.unique(v.vertida_id[v.occupation_mask][d['active_mask'][frame]])
        ax.set_title(f"t={d['times_s'][frame]/3600:g} h · {len(ids)}/5 vertidas activas",fontsize=10)
    fig.colorbar(plt.cm.ScalarMappable(norm=norm,cmap='inferno'),ax=fig.axes,label='Temperatura [°C]',shrink=.65,pad=.015)
    fig.suptitle('Evolución espacial de la temperatura en la fundación\nMedio dominio seccionado; gris=futuro · misma geometría y escala de color',fontsize=15)
    save(fig,'e09_evolucion_espacial.png','3d_cutaway',dict(frames=frames,occupied_face_indices=faces.indices[visible].tolist()))
    rows=s['snapshot_balance'];ts=np.array([r['time_s'] for r in rows])/3600;initial=s['energy']['initial_J']
    fig,(ax,b)=plt.subplots(2,1,figsize=(10,6),layout='constrained')
    ax.plot(ts,[(r['energy_J']-initial)/1e9 for r in rows],label='Cambio sensible')
    ax.plot(ts,[(r['hydration_energy_J']-r['outward_energy_J']+r['placement_energy_J'])/1e9 for r in rows],'--',label='Hidratación − salida + colocación')
    ax.set(ylabel='Energía [GJ]',title='Balance con entrada de material separada de la hidratación');ax.legend();ax.grid(alpha=.2)
    b.plot(ts,[r['balance_residual_J'] for r in rows]);b.set(xlabel='Tiempo [h]',ylabel='Residuo global [J]');b.grid(alpha=.2)
    save(fig,'e09_balance.png','energy_balance')
    from ..e08.inputs import events_from_config
    events=events_from_config(s['configuration']['physics'])
    fig,(ax,b)=plt.subplots(2,1,figsize=(10,6),layout='constrained')
    for e in events:
        ax.plot(t,e.hydration.source(a['time_s']-e.activation_s),label=f'Vertida {e.pour_id}')
        b.plot([e.activation_s/3600,horizon],[e.pour_id,e.pour_id],lw=5,color=COLORS[(e.pour_id-1)%5])
        b.plot(e.activation_s/3600,e.pour_id,'ko',ms=4)
    ax.set(ylabel='Fuente volumétrica [W/m³]',title='Hidratación por edad propia · cronograma ilustrativo');ax.legend(ncol=5,fontsize=8);ax.grid(alpha=.2)
    b.set(xlabel='Tiempo [h]',ylabel='VertidaID',yticks=[e.pour_id for e in events]);b.grid(alpha=.2)
    save(fig,'e09_hidratacion_vertidas.png','hydration_schedule')
    if animation:
        gif_frames=sorted(set(frames)|{int(np.argmin(abs(d['times_s']/3600-h))) for h in np.linspace(0,horizon,min(29,len(d['times_s'])))} )
        images=[]
        for frame in gif_frames:
            fig,axes=plt.subplots(1,2,figsize=(8.6,4),layout='constrained')
            for ax,kind in zip(axes,('vertical','horizontal')):im,_=_draw_cut(ax,g,d,frame,kind,z,norm);ax.set_title('Corte '+kind)
            fig.colorbar(im,ax=list(axes),label='Temperatura [°C]',shrink=.75)
            fig.suptitle(f"E09 · t={d['times_s'][frame]/3600:g} h · gris=futuro",fontsize=12)
            buffer=io.BytesIO();fig.savefig(buffer,format='png',dpi=100);plt.close(fig);buffer.seek(0)
            with Image.open(buffer) as image:images.append(image.convert('RGB').copy())
        path=output/'e09_evolucion.gif';images[0].save(path,save_all=True,append_images=images[1:],duration=350,loop=0)
        manifest['files'][path.name]=dict(kind='animation',frames=gif_frames,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        for image in images:image.close()
    # Todo se puede enlazar desde el resultado con ruta relativa dentro de E09.
    import os
    manifest['figure_directory']=Path(os.path.relpath(output,folder)).as_posix()
    (folder/'figure_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return dict(directory=manifest['figure_directory'],files=list(manifest['files']),field_sha256=field_sha)
