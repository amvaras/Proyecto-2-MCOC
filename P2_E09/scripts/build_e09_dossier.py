"""Redacta el dossier a partir de métricas calculadas, sin resultados fijados a mano."""
import argparse,json,os
from pathlib import Path
from check_e09_dossier import PUBLICATION_REF, PUBLICATION_URL, inspect_dossier
ROOT=Path(__file__).resolve().parents[1]


def build(result,output):
    result=Path(result).resolve();output=Path(output).resolve()
    if not result.is_relative_to(ROOT) or not output.is_relative_to(ROOT):raise ValueError('Documento y datos dentro de E09')
    s=json.loads((result/'summary.json').read_text(encoding='utf-8'));m=json.loads((result/'figure_manifest.json').read_text(encoding='utf-8'))
    cfg=s['configuration']['physics'];grid=s['grid'];thermal=s['thermal'];peak=thermal['peak'];delta=thermal['center_top_difference']
    points={p['name']:p for p in thermal['probes']}
    def link(path):return Path(os.path.relpath(path,output.parent)).as_posix()
    figures=(result/m['figure_directory']).resolve()
    def fig(name,title):return f'![{title}]({link(figures/name)})'
    volumes='; '.join(f"V{r['vertida_id']}: {r['volume_voxel_m3']:.3f} m³ ({100*r['relative_error']:.2f}%)" for r in grid['by_pour'])
    placements=', '.join(f"V{e['pour_id']}: {e['activation_s']/3600:g} h/{e['initial_C']:g} °C" for e in cfg['events'])
    coord=', '.join(f'{x:.3f}' for x in peak['coordinate_m'])
    upper=points['superficie_superior'];core=points['nucleo'];side=points['superficie_lateral'];base=points['cerca_base']
    state='no supera' if peak['temperature_C']<=70 else 'supera'
    dstate='supera' if delta['maximum_C']>20 else 'no supera'
    adiabatic_rise=cfg['hydration']['H_vol_J_m3']/(cfg['material']['rho']*cfg['material']['cp'])
    time_note=''
    time_check=ROOT/'results/verification/temporal_check.json'
    if time_check.exists():
        tc=json.loads(time_check.read_text(encoding='utf-8'))
        time_note=f"Al reducir el paso a {tc['refined_max_step_s']:g} s, la diferencia máxima de campos fue {tc['field_Linf_difference_C']:.5f} °C; el pico cambió {tc['peak_difference_C']:.5f} °C. Es sensibilidad temporal, no error exacto."
    text=f"""# E09 — Baseline 3D con hidratación
Grupo 2 · MCOC, Universidad de los Andes · 6 de noviembre de 2026.

## Repositorio y alcance
Repositorio: [amvaras/Proyecto-2-MCOC](https://github.com/amvaras/Proyecto-2-MCOC).
Commit evaluado: [{PUBLICATION_REF}]({PUBLICATION_URL})

Se simula la fundación docente del Parque Eólico Sarco, Freirina, durante
{s['duration_h']/24:g} días completos. Las coordenadas climáticas de referencia son
−28,856102; −71,421831, pero no se utilizaron registros meteorológicos.
Es un baseline numérico interpretable, no una predicción calibrada de obra.

## BIM, grilla y error geométrico
El [IFC real]({link(ROOT/s['ifc']['relative_path'])}) contiene cinco IfcFooting,
con GUID y propiedades conservados. Se verifican metros, transformaciones,
mallas cerradas y cotas. La planta octagonal mide 18 m entre caras; borde
1,10 m, centro 3,30 m y pedestal Ø7 m con 1 m adicional: altura total 4,30 m.
La imagen representa sus triángulos originales con IfcOpenShell; no es una captura de Bonsai.

{fig('e09_bim.png','BIM original leído del IFC')}

Una celda se ocupa si su centro pertenece al sólido; la caja envolvente solo
acelera la clasificación. Se utilizan pasos {grid['spacing_m'][0]:g} ×
{grid['spacing_m'][1]:g} × {grid['spacing_m'][2]:g} m,
{grid['grid_cells']:,} celdas totales y {grid['occupied_cells']:,} ocupadas.
El volumen calculado es {grid['volume_voxel_m3']:.6f} m³, frente a
{grid['volume_reference_mesh_m3']:.6f} m³ teselados: diferencia absoluta
{grid['absolute_error_m3']:.6f} m³, error {100*grid['relative_error']:.5f}%.
La referencia analítica docente es 636,885036 m³.

Por vertida, volumen y error respecto del IFC: {volumes}.
El error global no oculta el del pedestal. El estudio cúbico usa 0,55,
0,275 y 0,1375 m; su error oscila por alineamiento. La frontera staircase
también sesga el área expuesta. Esta resolución permite completar la duración;
no demuestra convergencia espacial del campo térmico real.

{fig('e09_voxelizacion.png','Vóxeles e identidad de las cinco vertidas')}
{fig('e09_error_volumen.png','Errores total y por vertida')}

## Vertidas, hidratación y ambiente
Calendario ilustrativo, editable en JSON: {placements}. Las cotas
son 0–0,55; 0,55–1,10; 1,10–2,20; 2,20–3,30 y 3,30–4,30 m.
Antes de colocarse, una vertida no aporta capacidad, conducción ni fuente.
La colocación inicializa únicamente sus celdas y reinicia su propia edad.
Dos vertidas activas intercambian calor con contacto perfecto; frente a una
futura, la cara existente queda expuesta. La visibilidad gráfica no altera esto.

Se adoptan k={cfg['material']['k']:g} W/(m·K), rho={cfg['material']['rho']:g} kg/m³ y
cp={cfg['material']['cp']:g} J/(kg·K). Para edad a y duración tau,
xi=[1−cos(pi·clip(a/tau,0,1))]/2 y q_h=H_vol·d(xi)/dt, en W/m³.
H_vol={cfg['hydration']['H_vol_J_m3']/1e6:g} MJ/m³ y tau={cfg['hydration']['duration_s']/3600:g} h
equivalen a {adiabatic_rise:g} K adiabáticos con esta capacidad. Son hipótesis, no ensayos;
no existe Arrhenius. Se integra exactamente el calor liberado por intervalo.

Las caras superiores y laterales expuestas usan Robin, ambiente constante
{cfg['ambient_C']:g} °C y h={cfg['h_W_m2K']:g} W/(m²·K). La base z− es adiabática:
representa aislamiento ideal, sin suelo explícito. Las interfaces activas no reciben Robin.

{fig('e09_hidratacion_vertidas.png','Fuente por edad y calendario hipotético')}

## Integración y resultados
El balance por celda activa es C_i·dT_i/dt=sum G_ij(T_j−T_i)+q_h·V−P_salida,
con C_i=rho·cp·V y resistencias de media celda en los contactos y Robin.
Euler explícito ejecutó {s['temporal']['integration_steps']} pasos de
{s['temporal']['max_step_s']:g} s y guardó {s['temporal']['saved_frames']} campos.
La mínima cota local fue {s['temporal']['smallest_stable_step_s']:.2f} s;
max(dt/cota)={s['temporal']['max_dt_over_limit']:.4f}, inferior a safety={cfg['safety']:g}.
{time_note}

El máximo, registrado en todos los pasos, fue {peak['temperature_C']:.4f} °C a
{peak['time_h']:g} h, en V{peak['vertida_id']} y coordenadas ({coord}) m.
El control sin hidratación alcanzó {s['control_no_hydration']['peak_C']:.2f} °C.
El calentamiento procede de la fuente; después domina la disipación, mientras
la base aislada conserva calor y recibe redistribución desde otras capas.

{fig('e09_tmax.png','Máxima, mínima, media y control sin hidratación')}

La sonda núcleo es el centro ocupado más cercano a (0,0,1,65) m.
La cara superior queda en la misma línea vertical; se reconstruye mediante
Ts=(Tc+h·dn/(2k)·Ta)/(1+h·dn/(2k)), no se confunde con el centro.
La sonda lateral es la cara x+ más cercana al objetivo exterior; sus coordenadas
y las de cada centro de vertida están en summary.json. La sonda basal
usa el centro ocupado inferior de la línea central.

Máximos de núcleo/superior/lateral/base:
{core['maximum_C']:.3f}/{upper['maximum_C']:.3f}/{side['maximum_C']:.3f}/{base['maximum_C']:.3f} °C;
ocurren a {core['maximum_time_h']:g}/{upper['maximum_time_h']:g}/{side['maximum_time_h']:g}/{base['maximum_time_h']:g} h.
No se comparan como si tuvieran igual edad desde colocación.
La diferencia núcleo–cara superior alcanza {delta['maximum_C']:.4f} °C a
{delta['time_h']:g} h; solo se evalúa cuando existen ambas sondas.
El máximo {state} 70 °C, pero el diferencial {dstate} 20 °C.
Esto identifica una observación del baseline, sin certificar seguridad constructiva.

{fig('e09_sondas.png','Sondas fijas y centros representativos por vertida')}
{fig('e09_diferencia.png','Diferencia vertical frente a referencia del curso')}

## Evolución espacial y energía
Los cortes revelan interior caliente y enfriamiento exterior. La lámina usa
la misma orientación y escala térmica; gris significa vertida futura, blanco
vacío. El seccionamiento es solo visual. La continuidad conductiva redistribuye
calor entre vertidas, mientras cada una conserva su edad de hidratación.

{fig('e09_evolucion_espacial.png','Evolución espacial de la temperatura en la fundación')}
{fig('e09_cortes_vertical.png','Cortes verticales del campo calculado')}
{fig('e09_cortes_horizontal.png','Cortes horizontales del campo calculado')}

Con referencia energética de {cfg['energy_reference_C']:g} °C, hidratación:
{s['energy']['hydration_J']/1e9:.5f} GJ; salida neta:
{s['energy']['outward_J']/1e9:.5f} GJ; entrada posterior:
{s['energy']['placement_after_zero_J']/1e9:.5f} GJ. Se comprueba
DeltaE=Q_h−Q_salida+E_colocación, por etapa y globalmente.
Residuo global {s['energy']['residual_J']:.3g} J, frente a tolerancia
{s['energy']['tolerance_J']:.3g} J; no se atribuye la energía entrante a hidratación.

{fig('e09_balance.png','Balance energético con material incorporado')}

## Comparación crítica con Ju y Lei
Referencia: Ju, Y. y Lei, H. (2019), *Actual Temperature Evolution of Thick Raft
Concrete Foundations and Cracking Risk Analysis*, Advances in Materials Science
and Engineering, 7029671. [Artículo original](https://doi.org/10.1155/2019/7029671).

**Qué reproduce.** El interior se calienta por hidratación, alcanza un pico
y luego se enfría. La superficie permanece más fría y la base retiene calor.
Son tendencias también observadas en la fundación 1 (sección 3.1).

**Qué no reproduce.** Ju y Lei midieron cerca de 73 °C en el núcleo al
cuarto día y una diferencia núcleo–superficie de 35 °C al noveno día. Nuestra
sonda de núcleo alcanza {core['maximum_C']:.2f} °C a {core['maximum_time_h']:g} h
y el diferencial alcanza {delta['maximum_C']:.2f} °C a {delta['time_h']:g} h.
El pico global del modelo está en el pedestal. El terreno del artículo
permite que la base se enfríe lentamente. Aquí se aísla y la sonda basal
alcanza su máximo cerca del final. El ensayo adiabático, la edad equivalente,
el clima variable y la evaluación de fisuras quedan fuera de esta comparación.

## Reproducibilidad y límites
Desde esta carpeta, instalar con scripts/install.ps1; ejecutar
examples/run_e09.py, scripts/plot_e09.py, scripts/build_e09_dossier.py y
scripts/verify_e09.py, según [README]({link(ROOT/'README.md')}).
Los [arrays y métricas]({link(result/'summary.json')}) conservan configuración,
máscaras, coordenadas, sondas, pasos y balances. Las figuras registran el SHA
del campo utilizado; se verifica el límite de palabras y todos los enlaces.
Faltan calibración, clima y suelo reales, convergencia espacial de esta fundación
y validación experimental. El siguiente uso debe estudiar sensibilidad y fronteras
antes de proponer decisiones constructivas.
"""
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(text,encoding='utf-8')
    return inspect_dossier(output)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--result',type=Path,default=ROOT/'results/e09_baseline')
    p.add_argument('--output',type=Path,default=ROOT/'docs/E09_DOSSIER.md')
    a=p.parse_args();print(json.dumps(build(a.result,a.output),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
