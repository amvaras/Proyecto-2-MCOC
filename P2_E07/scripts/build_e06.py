"""Genera dossier y figuras E06 exclusivamente desde ejecuciones e IFC reales."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys

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


def document_text(evidence,figures,document,reports,bim,verification):
    def link(path):return Path(os.path.relpath(path,document.parent)).as_posix()
    b=lambda name:link(evidence/'thermal/battery'/name/'summary.json')
    s=reports['spatial'];t=reports['temporal'];e=reports['energy'];q=reports['source'];r=reports['robin'];n=reports['neumann']
    matrix=[]
    for dim in (1,2,3):
        case='exact_'+str(dim)+'d';a=reports[case]
        matrix.append(f"| [Exacta {dim}D]({b(case)}) | Seno continuo, centros y caras | L∞={a['error_Linf_C']:.7g} °C ≤ 0,03 °C | {a['status']} |")
    matrix.extend([
        f"| [Convergencia espacial]({b('spatial')}) | Referencia continua; Δt fijo | p={s['observed_orders'][0]:.5f}/{s['observed_orders'][1]:.5f}; 2±0,30 | {s['status']} |",
        f"| [Convergencia temporal]({b('temporal')}) | Referencia semidiscreta; malla fija | p={t['observed_orders'][0]:.5f}/{t['observed_orders'][1]:.5f}; 1±0,15 | {t['status']} |",
        f"| [Conservación adiabática]({b('energy')}) | Capacidad heterogénea ponderada | residuo {e['energy_balance_max_error_J']:.3e} J ≤ {e['energy_tolerance_J']:.3e} J | {e['status']} |",
        f"| [Fuente uniforme]({b('source')}) | Ley lineal y energía generada | L∞={q['error_Linf_C']:.3e} °C ≤ 2,463e-10 °C | {q['status']} |",
        f"| [Neumann]({b('neumann')}) | Flujo × área y signo saliente | residuo {n['energy_balance_max_error_J']:.3e} J ≤ {n['energy_tolerance_J']:.3e} J | {n['status']} |",
        f"| [Robin]({b('robin')}) | Media celda, película y balance | residuo {r['energy_balance_max_error_J']:.3e} J ≤ {r['energy_tolerance_J']:.3e} J | {r['status']} |",
        f"| [Estabilidad]({b('stability')}) | Monotonía y rechazo de exceso | 0,99·límite aceptado; 1,01 rechazado; exceso ≤ 1e-10 °C | {reports['stability']['status']} |"])
    spatial_rows='\n'.join(f"| {'×'.join(map(str,a['shape']))} | {a['spacing_m'][0]:.8f} | {a['error_Linf_C']:.9f} | {a['temporal_contamination_C']:.3e} |" for a in s['rows'])
    temporal_rows='\n'.join(f"| {a['effective_dt_s']:.6f} | {a['steps']} | {a['error_Linf_C']:.9f} |" for a in t['rows'])
    bim_rows='\n'.join(f"| {a['name']} | {a['bbox_min_m'][2]:.2f}–{a['bbox_max_m'][2]:.2f} | {a['volume_analytic_m3']:.5f} |" for a in bim['items'])
    return fr'''# E06 — Dossier de verificación y BIM del caso base

## Identificación y alcance

MCOC, Proyecto 2, Grupo 2: Freirina / Parque Eólico Sarco. Entrega del viernes
30 de octubre de 2026, sin actividad sincrónica, 3 puntos. Evidencia calculada
el 28 de octubre. El objetivo es congelar la verificación del solver básico y
documentar una versión coherente del BIM. Se conservaron físicamente los
archivos de E05 y se reconstruyó el entorno dentro de E06; los antecedentes
históricos permanecen separados de las nuevas ejecuciones.

El IFC representa la geometría constructiva. El solver trabaja sobre cajas
cartesianas ideales de verificación: todavía no existe integración mediante
voxelización. Por tanto, las temperaturas y energías siguientes no constituyen
una predicción térmica de la fundación de Freirina. No se incorporaron etapas
posteriores, hidratación ni condiciones climáticas transientes.

## Repositorio y commit

Repositorio: [amvaras/Proyecto-2-MCOC](https://github.com/amvaras/Proyecto-2-MCOC).
Commit evaluado: **COMMIT E06 PENDIENTE DE PUBLICACIÓN**.
La consulta remota encontró main en una entrega E01, sin dossier E06.
Ese antecedente no identifica estos archivos. No se crearon commits ni se
publicaron cambios. La integridad local queda identificada mediante SHA256;
el cierre formal exige publicar E06 y consignar su commit con autorización.

## Matriz de verificación

Cada enlace conduce a parámetros, referencias, métricas y tolerancias de una
ejecución nueva desde E06. PASS exige satisfacer todos los controles del caso.
La suite completa aprobó **{verification['tests']['tests']} pruebas**, sin fallos, errores ni omisiones;
también aprobaron diez casos nominales y sesenta variantes. Los rechazos
deliberados de estabilidad, unidades y precisión se comprobaron por motivo y
código de salida, sin contarlos como fallos inesperados de pytest.

| Test | Qué verifica | Error/métrica | Resultado |
|---|---|---|---|
{chr(10).join(matrix)}

La referencia continua es
$$T=T_0+A\prod_j\sin(\pi x_j/L_j)\exp[-\alpha\sum_j(\pi/L_j)^2t],\qquad\alpha=k/(\rho c_p).$$
Se evalúa en centros físicos; las caras mantienen Dirichlet T₀. Sustituirla
en la ecuación confirma la referencia sin recurrir a resultados del solver.
L∞ es el máximo error puntual. El balance suma capacidades por temperatura;
las potencias internas se cancelan y los flujos externos positivos extraen
energía. Los criterios se fijaron antes de observar las nuevas corridas.

## Convergencia espacial

Caja bidimensional de 1×1 m, k=2 W/(m·K), ρ=2400 kg/m³, cₚ=900 J/(kg·K),
T₀=20 °C, A=10 °C y tiempo final 10000 s. Se empleó Δt=3,125 s en las tres
mallas. El error temporal, medido contra el modo semidiscreto, representa
como máximo {100*max(a['temporal_contamination_C']/a['error_Linf_C'] for a in s['rows']):.3f}% del error total, inferior al límite previo del 10%.

| Celdas | Δx [m] | L∞ [°C] | Componente temporal [°C] |
|---|---:|---:|---:|
{spatial_rows}

Los cocientes son {s['error_ratios'][0]:.5f} y {s['error_ratios'][1]:.5f}. El orden observado se
aproxima a dos; la malla gruesa aún presenta efectos preasintóticos.
La recta auxiliar de la figura ilustra pendiente, sin ajustar ni ocultar puntos.

![Convergencia espacial]({link(figures/'e06_convergencia_espacial.png')})
Figura 1. Refinamiento espacial con referencia continua y paso temporal fijo.

## Convergencia temporal

Se mantuvo la malla 6×6 y las mismas propiedades. Para aislar el error de Euler
se comparó con el modo exacto del sistema espacial discretizado, cuyo
decaimiento es αΣⱼ4sin²(π/(2nⱼ))/Δxⱼ². Este autovalor se contrastó también
contra el operador real. No se mezcló refinamiento temporal con espacial.

| Δt efectivo [s] | Pasos | L∞ [°C] |
|---|---:|---:|
{temporal_rows}

Los cocientes {t['error_ratios'][0]:.5f} y {t['error_ratios'][1]:.5f} y los órdenes de la matriz
confirman primer orden temporal en este régimen. Todos los pasos satisfacen
la cota local de monotonía, calculada con capacidades y conductancias.

![Convergencia temporal]({link(figures/'e06_convergencia_temporal.png')})
Figura 2. Malla fija y comparación semidiscreta; pendiente esperada igual a uno.

## Conservación de energía

La caja 3D adiabática utiliza un perfil cosenoidal no uniforme, fuente cero y
dos regiones materiales. En la segunda mitad se multiplican k, ρ y cₚ por
3, 1,15 y 0,8. Se calcula E=ΣᵢρᵢcₚᵢVᵢ(Tᵢ−20 °C), evitando medias sin
ponderación. El cambio final es {e['energy_final_J']-e['energy_initial_J']:.3e} J y el residuo máximo figura en
la matriz. El rango térmico disminuye de {e['initial_range_C']:.5f} a {e['final_range_C']:.5f} °C: hay redistribución
interna sin creación de energía. La tolerancia combina 1e-7 J y 5e-12 de una
escala energética definida por capacidad, temperaturas y generación.

## Fuente volumétrica uniforme

Con inicial uniforme de 20 °C, aislamiento, q̇=1000 W/m³, V=1 m³ y las
propiedades anteriores, T(t)=T₀+q̇t/(ρcₚ). A 10000 s, el incremento esperado
es 4,629629630 °C y el calculado es {q['final_min_C']-20:.9f} °C.
La energía esperada es 10000000 J; la calculada es {q['energy_final_J']-q['energy_initial_J']:.8f} J.
Se verificaron temperatura y balance en todos los tiempos guardados.
La fuente es volumétrica; un flujo Neumann se expresa por unidad de superficie.

## Robin

El caso 3D parte de 50 °C, con ambiente a 20 °C y h=12 W/(m²·K) en sus seis
caras. Se usa R″=Δn/(2k)+1/h y q″=(T_celda−T_ambiente)/R″.
La resistencia de media celda evita identificar temperatura central con
superficial; esta última tampoco tiene que coincidir con el ambiente.
El flujo inicial sale del sólido y el enfriamiento pierde
{abs(r['energy_final_J']-r['energy_initial_J']):.5f} J. Se comprobaron ambas resistencias, ley superficial,
principio máximo y balance integrado usando el estado previo de Euler.
Una ejecución adicional con h=25 también aprobó; no se presenta la curva
numérica como solución analítica exacta del problema Robin general.

## BIM base

El [IFC incluido]({link(ROOT/'geometry/foundation.ifc')}) es IFC4, en metros, con cinco
IfcFooting identificables. Se validaron esquema, jerarquía, propiedades,
orientación, mallas cerradas y diez pares sin solapamiento volumétrico.
Las cotas reales confirman octágono exterior de 18 m entre caras, borde de
1,10 m, centro de 3,30 m y pedestal circular Ø7 m con 1,00 m adicional:
altura global 4,30 m. Las coordenadas climáticas docentes son
−28.856102, −71.421831; el IFC utiliza origen local sin georreferenciación.

| Elemento | Intervalo z [m] | Volumen analítico [m³] |
|---|---:|---:|
{bim_rows}

El volumen exacto de perfiles y troncos es {bim['total_analytic_m3']:.5f} m³, coherente con
636,89 m³. La malla triangular arroja {bim['total_mesh_m3']:.5f} m³; la pequeña diferencia
proviene de teselar el círculo. La tolerancia relativa por pieza es 5e-4.

![Fundación IFC real]({link(figures/'e06_bim_fundacion.png')})
Figura 3. Geometría leída del IFC mediante IfcOpenShell y dibujada en Python;
no es una captura de Bonsai. Colores identifican vertidas y cotas globales.

## Simplificaciones geométricas

- Octágono idealizado respecto de la fundación que inspira la guía docente.
- Borde de 1,10 m adoptado para el ejercicio, no medido directamente del paper.
- Transición inclinada mediante dos troncos octagonales de caras planas.
- Cinco vertidas iniciales; no representan un plan constructivo optimizado.
- Pedestal adicional de 1,00 m adoptado por la guía.
- Omisión de armaduras, pernos, anclajes y detalles menores no definidos.
- Origen local, sin georreferenciación global IFC ni integración térmica voxelizada.

## Reproducibilidad y conclusión

Desde la raíz, instalar según el [README]({link(ROOT/'README.md')}) y ejecutar
`.venv/Scripts/python.exe -B scripts/verify_e06.py --output results/e06_repeticion`.
El comando repite suite, batería, IFC, figuras y controles documentales en un
destino nuevo. Para inspección directa: `.venv/Scripts/python.exe -B scripts/check_ifc.py geometry/foundation.ifc`.
En Bonsai, abrir ese archivo y seleccionar Vertida_01 a Vertida_05 para revisar
geometría y propiedades. El generador acepta un destino distinto y rechaza
sobrescribir el IFC de referencia. Las referencias analíticas, datos completos,
versiones, comandos y SHA256 están en [evidencia E06]({link(evidence/'e06.json')}).
El alcance técnico queda verificado; la publicación y su commit siguen pendientes.
'''


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
