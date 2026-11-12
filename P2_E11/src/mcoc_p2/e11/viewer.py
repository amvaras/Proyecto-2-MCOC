"""Visor nativo PyVista: tiempo, visibilidad, corte y clip sobre celdas activas."""
import json
from datetime import timedelta
from pathlib import Path
import numpy as np
import pyvista as pv
from .weather import ROOT
from ..e10.weather import utc_time


class Viewer:
    def __init__(self,vtk_folder=ROOT/'vtk/e11',result=ROOT/'results/e11',off_screen=False,log_path=None):
        self.log_path=Path(log_path) if log_path else ROOT/'results/verification/gui_session.json'
        if not self.log_path.resolve().is_relative_to(ROOT):raise ValueError('Registro dentro de E11')
        self.folder=Path(vtk_folder);self.result=Path(result)
        self.manifest=json.loads((self.folder/'manifest.json').read_text(encoding='utf-8'))
        self.summary=json.loads((self.result/'summary.json').read_text(encoding='utf-8'))
        with np.load(self.result/'statistics.npz') as z:self.stats={k:z[k] for k in z.files}
        self.index=len(self.manifest['states'])-1;self.mode='full';self.visible={p:True for p in range(1,6)};self.actions=[]
        self.clim=(float(self.stats['weather_Tmin_C'].min()),float(self.stats['weather_Tmax_C'].max()))
        self.plotter=pv.Plotter(off_screen=off_screen,window_size=(1100,760),title='E11 - Fundacion - PyVista')
        self.plotter.set_background('white');self.plotter.add_axes()
        self.plotter.add_text('1-5: vertidas | s: slice | c: clip | r: completo | flechas: tiempo | v: captura',position='lower_left',font_size=10,color='black',name='help')
        self.actors={};self.draw()
        for p in range(1,6):self.plotter.add_key_event(str(p),lambda pid=p:self.toggle(pid))
        self.plotter.add_key_event('s',lambda:self.set_mode('slice'));self.plotter.add_key_event('c',lambda:self.set_mode('clip'))
        self.plotter.add_key_event('r',lambda:self.set_mode('full'))
        self.plotter.add_key_event('Left',lambda:self.change(-1));self.plotter.add_key_event('Right',lambda:self.change(1))
        self.plotter.add_key_event('v',self.capture)
        self.plotter.view_isometric();self.plotter.camera.zoom(1.15)

    def log(self,action,**data):
        self.actions.append(dict(action=action,mode=self.mode,index=self.index,**data))
        if self.plotter.off_screen:return  # Pruebas no sobrescriben evidencia nativa.
        out=self.log_path;out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(dict(off_screen=self.plotter.off_screen,actions=self.actions),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    def draw(self):
        self.plotter.clear_plane_widgets()
        self.plotter.remove_actor('probes-points');self.plotter.remove_actor('probes-labels')
        for key in list(self.actors):self.plotter.remove_actor(self.actors[key])
        self.actors={}
        row=self.manifest['states'][self.index];self.image=pv.read(self.folder/row['file'])
        live=self.image.threshold(.5,scalars='active')
        # Filtrar visibilidad solo en copia gráfica; no cambia fichero ni solución.
        keep=np.isin(live['vertida_id'],[pid for pid,value in self.visible.items() if value]);mesh=live.extract_cells(keep)
        opts=dict(scalars='temperature_C',cmap='inferno',clim=self.clim,scalar_bar_args={'title':'Temperatura [°C]'},show_edges=False)
        if mesh.n_cells:
            if self.mode=='slice':
                self.actors['main']=self.plotter.add_mesh_slice(mesh,normal='y',origin=(0,0,1.65),**opts)
            elif self.mode=='clip':
                self.actors['main']=self.plotter.add_mesh_clip_plane(mesh,normal='y',origin=(0,0,1.65),invert=False,**opts)
            else:self.actors['main']=self.plotter.add_mesh(mesh,**opts)
        xyz=[];labels=[];shape=np.array(self.image.dimensions)-1
        stat=int(np.argmin(abs(self.stats['weather_time_s']-row['time_h']*3600)))
        for j,p in enumerate(self.summary['probes']):
            i,k,l=p['index'];cell=i+shape[0]*(k+shape[1]*l)
            if self.image['active'][cell] and self.visible[p['vertida_id']] and self.stats['weather_probe_valid'][stat,j]:
                xyz.append(p['coordinate_m']);labels.append(p['name']+f" {self.stats['weather_probe_temperature_C'][stat,j]:.2f} °C")
        if xyz:self.actors['points']=self.plotter.add_point_labels(np.array(xyz),labels,name='probes',point_color='cyan',point_size=10,font_size=14,text_color='black',always_visible=True,shape_color='white')
        actual=(utc_time(self.summary['simulation_start_utc'])+timedelta(hours=row['time_h'])).isoformat().replace('+00:00','Z')
        self.plotter.add_text(f"E11 · {row['time_h']:g} h · {self.mode}\nClima UTC: {actual}",font_size=12,color='black',name='time')
        self.plotter.render()

    def toggle(self,pid):
        self.visible[pid]=not self.visible[pid];self.draw();self.log('toggle',vertida_id=pid,visible=self.visible[pid])
    def set_mode(self,mode):
        self.mode=mode;self.draw()
        # Operaciones independientes, no solo widgets: comprobar filtro sobre VTK real.
        live=self.image.threshold(.5,scalars='active')
        result=live.slice(normal='y',origin=(0,0,1.65)) if mode=='slice' else live.clip(normal='y',origin=(0,0,1.65)) if mode=='clip' else live
        self.log(mode,cells=result.n_cells)
    def change(self,delta):
        self.index=(self.index+delta)%len(self.manifest['states']);self.draw();self.log('time',time_h=self.manifest['states'][self.index]['time_h'])
    def capture(self):
        path=ROOT/'figures/e11_native.png';self.plotter.screenshot(path);self.log('capture',file='figures/e11_native.png')


def render_figures(folder=ROOT/'vtk/e11',result=ROOT/'results/e11',output=ROOT/'figures'):
    output=Path(output);output.mkdir(parents=True,exist_ok=True);v=Viewer(folder,result,off_screen=True);report={}
    for mode,name in [('full','e11_3d_puntos.png'),('slice','e11_slice.png'),('clip','e11_clip.png')]:
        v.set_mode(mode);v.plotter.screenshot(output/name);report[mode]=dict(file=name,points_identified=len(v.summary['probes']))
    live=v.image.threshold(.5,scalars='active')
    report['filters']=dict(active_cells=live.n_cells,slice_cells=live.slice(normal='y',origin=(0,0,1.65)).n_cells,clipped_cells=live.clip(normal='y',origin=(0,0,1.65)).n_cells)
    v.plotter.close()
    return report
