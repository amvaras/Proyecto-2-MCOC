"""Genera dossier y figuras E06 exclusivamente desde ejecuciones e IFC reales."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

from check_ifc import inspect_model
from check_e06_dossier import inspect_dossier
from mcoc_p2.verification_e05 import make_config,_system,eigenvalues,sine_mode
from mcoc_p2.thermal_nd import CartesianGrid
from mcoc_p2.diffusion_1d import Material

ROOT=Path(__file__).resolve().parents[1]


def write_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def reference_audit():
    """Compara operador real con autovalores derivados; no llama al solver."""
    rows=[]
    for dim in (1,2,3):
        cfg=make_config('exact_'+str(dim)+'d',dict(shape=tuple(5+i for i in range(dim)),
                        lengths_m=tuple(1.2+.3*i for i in range(dim)),k=1.7,rho=2300,cp=870))
        grid=CartesianGrid(cfg.lengths_m,cfg.shape);system=_system('exact_'+str(dim)+'d',cfg)
        material=Material(cfg.k,cfg.rho,cfg.cp);alpha=cfg.k/(cfg.rho*cfg.cp)
        continuous=alpha*sum((math.pi/L)**2 for L in cfg.lengths_m)
        discrete=alpha*sum(4*math.sin(math.pi/(2*n))**2/dx**2 for n,dx in zip(cfg.shape,grid.spacing))
        reported=eigenvalues(grid,material)
        np.testing.assert_allclose(reported,[continuous,discrete],rtol=2e-15,atol=0)
        theta=sine_mode(grid)
        # Dirichlet T0: aplicar potencia al campo T0+theta y dividir C.
        operator=system.power(cfg.initial_C+theta)/system.capacity
        residual=float(np.max(abs(operator+discrete*theta)))
        tolerance=1e-11*max(continuous,discrete)
        if residual>tolerance:raise ValueError('El modo no es autovector del operador real')
        rows.append(dict(dimension=dim,continuous_rate_s_minus1=continuous,
                         discrete_rate_s_minus1=discrete,operator_residual_K_s=residual,
                         tolerance_K_s=tolerance,status='PASS'))
    return dict(status='PASS',method='Sustitución de seno en PDE; autovalor derivado de diferencias centradas y medias celdas Dirichlet; operador real por unidad de capacidad.',cases=rows)


def bim_audit():
    report=inspect_model(ROOT/'geometry/foundation.ifc')
    model=ifcopenshell.open(str(ROOT/'geometry/foundation.ifc'))
    site=model.by_type('IfcSite')[0]
    if site.RefLatitude or site.RefLongitude or model.by_type('IfcMapConversion'):
        raise ValueError('Revisar simplificación: IFC ahora tiene georreferencia')
    if model.by_type('IfcReinforcingBar') or model.by_type('IfcMechanicalFastener'):
        raise ValueError('Revisar simplificaciones: aparecieron armaduras o anclajes')
    total_mesh=sum(x['volume_mesh_m3'] for x in report['items'])
    total_analytic=sum(x['volume_analytic_m3'] for x in report['items'])
    if abs(total_analytic-636.89)>.01:raise ValueError('Volumen incompatible con caso docente')
    if not math.isclose(report['global_max_m'][2]-report['global_min_m'][2],4.3,abs_tol=1e-7):
        raise ValueError('Altura global incompatible')
    report.update(status='PASS',total_mesh_m3=total_mesh,total_analytic_m3=total_analytic,
                  mesh_relative_volume_error=abs(total_mesh-total_analytic)/total_analytic,
                  global_height_m=4.3,outer_across_faces_m=18.,edge_thickness_m=1.1,
                  central_thickness_m=3.3,pedestal_diameter_m=7.,pedestal_extra_height_m=1.,
                  global_georeferencing=False,reinforcement_present=False,anchors_present=False,
                  ifc_sha256=hashlib.sha256((ROOT/'geometry/foundation.ifc').read_bytes()).hexdigest(),
                  group='G2 — Freirina / Parque Eólico Sarco',climate_latitude=-28.856102,
                  climate_longitude=-71.421831,
                  volume_note='Suma exacta de troncos octagonales y cilindro desde perfiles IFC; la malla triangular aproxima el círculo. Cota relativa por pieza 5e-4; cotas octagonales 1e-7 m y círculo teselado 2 mm.')
    return report


def plot_convergence(report,path,spatial):
    rows=report['rows'];x=np.array([r['spacing_m'][0] if spatial else r['effective_dt_s'] for r in rows])
    error=np.array([r['error_Linf_C'] for r in rows]);order=2 if spatial else 1
    fig,ax=plt.subplots(figsize=(7.2,4.7),layout='constrained')
    ax.loglog(x,error,'o-',color='#145c80',lw=2,label='Error L∞ calculado')
    ax.loglog(x,error[-1]*(x/x[-1])**order,'--',color='#b15e1a',label=f'Pendiente de referencia {order}')
    for a,b,row in zip(x,error,rows):
        label='×'.join(map(str,row['shape'])) if spatial else f"{row['steps']} pasos"
        ax.annotate(label,(a,b),xytext=(5,8),textcoords='offset points',fontsize=9)
    ax.set(xlabel='Δx = Δy [m]' if spatial else 'Δt efectivo [s]',ylabel='Error máximo [°C]',
           title=('Convergencia espacial · referencia continua' if spatial else 'Convergencia temporal · referencia semidiscreta')+'\n'+'Órdenes observados: '+', '.join(f'{p:.4f}' for p in report['observed_orders']))
    ax.grid(True,which='both',alpha=.22);ax.legend(loc='lower right');ax.margins(.2)
    fig.savefig(path,dpi=190);plt.close(fig)


def plot_bim(path,report):
    model=ifcopenshell.open(str(ROOT/'geometry/foundation.ifc'));settings=ifcopenshell.geom.settings();settings.set('use-world-coords',True)
    colours=['#285f8d','#6daacb','#e5af50','#c96b3d','#728654']
    meshes=[]
    for el in sorted(model.by_type('IfcFooting'),key=lambda e:e.Name):
        shape=ifcopenshell.geom.create_shape(settings,el)
        v=np.array(shape.geometry.verts).reshape(-1,3);f=np.array(shape.geometry.faces).reshape(-1,3)
        meshes.append(v[f])
    fig=plt.figure(figsize=(12,6.5),layout='constrained');gs=fig.add_gridspec(2,2,width_ratios=[1.25,1])
    ax=fig.add_subplot(gs[:,0],projection='3d');elev=25;azim=-55
    direction=np.array([np.cos(np.deg2rad(elev))*np.cos(np.deg2rad(azim)),np.cos(np.deg2rad(elev))*np.sin(np.deg2rad(azim)),np.sin(np.deg2rad(elev))])
    exterior=[];facecolours=[]
    for i,(tri,c) in enumerate(zip(meshes,colours)):
        horizontal=np.ptp(tri[:,:,2],axis=1)<1e-8
        exposed=np.ones(len(tri),dtype=bool)
        if i>0:exposed &= ~(horizontal & np.isclose(tri[:,0,2],tri[:,:,2].min()))
        if i<3:exposed &= ~(horizontal & np.isclose(tri[:,0,2],tri[:,:,2].max()))
        normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);visible=exposed & (normals@direction>1e-10)
        exterior.extend(tri[visible]);facecolours.extend([c]*int(visible.sum()))
    # Una colección permite ordenar los triángulos entre todas las vertidas.
    ax.add_collection3d(Poly3DCollection(exterior,facecolor=facecolours,edgecolor='none',antialiased=False,zsort='average'))
    ax.set(xlim=(-10,10),ylim=(-10,10),zlim=(0,4.5),xlabel='x [m]',ylabel='y [m]',zlabel='z [m]',title='Isométrica · escala geométrica sin exageración')
    ax.set_box_aspect((20,20,4.5));ax.view_init(elev=elev,azim=azim);ax.set_proj_type('ortho')
    ax.set_xticks([-9,0,9]);ax.set_yticks([-9,0,9]);ax.set_zticks([0,1.1,3.3,4.3])
    plan=fig.add_subplot(gs[0,1]);section=fig.add_subplot(gs[1,1])
    # Contornos extraídos de los vértices IFC, sin reconstruir una geometría ilustrativa.
    def hull(points):
        points=sorted(set(map(tuple,points)))
        def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
        lower=[];upper=[]
        for p in points:
            while len(lower)>=2 and cross(lower[-2],lower[-1],p)<=1e-12:lower.pop()
            lower.append(p)
        for p in reversed(points):
            while len(upper)>=2 and cross(upper[-2],upper[-1],p)<=1e-12:upper.pop()
            upper.append(p)
        return np.array(lower[:-1]+upper[:-1])
    for tri,c in zip(meshes,colours):
        points=tri.reshape(-1,3)
        for axis,indices in ((plan,[0,1]),(section,[0,2])):
            polygon=hull(points[:,indices]);axis.fill(polygon[:,0],polygon[:,1],color=c,ec='white',lw=.6)
    for axis in (plan,section):
        axis.set_aspect('equal');axis.grid(alpha=.15);axis.set_xlabel('x [m]')
    plan.set(xlim=(-10.7,10.7),ylim=(-11.2,10.2),ylabel='y [m]',title='Planta · octágono exterior y pedestal circular')
    plan.annotate('',xy=(9,-10),xytext=(-9,-10),arrowprops=dict(arrowstyle='<->'))
    plan.text(0,-10.25,'18 m entre caras',ha='center',va='top',fontsize=9)
    plan.annotate('',xy=(3.5,0),xytext=(-3.5,0),arrowprops=dict(arrowstyle='<->'))
    plan.text(0,.45,'Ø 7 m',ha='center',fontsize=9)
    section.set(xlim=(-10,11),ylim=(-.3,5),ylabel='z [m]',title='Proyección lateral · alturas en metros')
    section.annotate('',xy=(10,4.3),xytext=(10,0),arrowprops=dict(arrowstyle='<->'))
    section.text(10.2,2.15,'4,30 m',rotation=90,va='center',fontsize=9)
    section.set_yticks([0,.55,1.1,2.2,3.3,4.3])
    fig.legend(handles=[Patch(color=c,label=f"{r['name']} ({r['bbox_min_m'][2]:.2f}–{r['bbox_max_m'][2]:.2f} m)") for c,r in zip(colours,report['items'])],loc='outside lower center',ncol=3,fontsize=9)
    fig.suptitle('G2 · Fundación docente Freirina / Sarco\nIFC real leído por IfcOpenShell; visualización Python, sin interfaz Bonsai',fontsize=13)
    fig.savefig(path,dpi=190);plt.close(fig)


from e06_document import document_text


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence',type=Path,required=True)
    parser.add_argument('--document',type=Path,required=True)
    parser.add_argument('--figures',type=Path,required=True)
    args=parser.parse_args()
    evidence=args.evidence.resolve();document=args.document.resolve();figures=args.figures.resolve()
    if document.exists():parser.error('El dossier de destino ya existe')
    names=['e06_convergencia_espacial.png','e06_convergencia_temporal.png','e06_bim_fundacion.png']
    if any((figures/name).exists() for name in names):parser.error('Las figuras de destino ya existen')
    verification=json.loads((evidence/'thermal/verification.json').read_text(encoding='utf-8'))
    battery=json.loads((evidence/'thermal/battery/battery.json').read_text(encoding='utf-8'))
    if verification['status']!='passed' or battery['status']!='PASS':raise ValueError('Evidencia térmica no aprobada')
    reports={r['case']:r for r in battery['cases']}
    extra=json.loads((evidence/'robin25/battery.json').read_text(encoding='utf-8'))
    if extra['status']!='PASS':raise ValueError('Robin h25 no aprobado')
    references=reference_audit();bim=bim_audit()
    write_json(evidence/'referencias.json',references);write_json(evidence/'bim.json',bim)
    figures.mkdir(parents=True,exist_ok=True);document.parent.mkdir(parents=True,exist_ok=True)
    plot_convergence(reports['spatial'],figures/names[0],True)
    plot_convergence(reports['temporal'],figures/names[1],False)
    plot_bim(figures/names[2],bim)
    document.write_text(document_text(evidence,figures,document,reports,bim,verification),encoding='utf-8')
    count=inspect_dossier(document);write_json(evidence/'dossier_check.json',count)
    print(json.dumps(dict(status='PASS',prose_words=count['prose_words'],all_visible_words=count['all_visible_words'],figures=names),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
