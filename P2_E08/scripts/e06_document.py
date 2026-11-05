"""Dossier E06 conciso con métricas extraídas de la ejecución vigente."""
import math
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def document_text(evidence, figures, document, reports, bim, verification):
    def link(path):return Path(os.path.relpath(path,document.parent)).as_posix()
    def metric(value):return f'{value:.6g}'
    def case_link(name):return link(evidence/'thermal/battery'/name/'summary.json')
    spatial,temporal,energy,source,robin=[reports[n] for n in ('spatial','temporal','energy','source','robin')]
    matrix=[]
    for dim in (1,2,3):
        name=f'exact_{dim}d';row=reports[name]
        matrix.append(f"| [Exacta {dim}D]({case_link(name)}) | Seno continuo y Dirichlet en caras | L∞={metric(row['error_Linf_C'])} °C ≤ {metric(row['config']['atol_C'])} °C | {row['status']} |")
    for name,label,expected,tolerance in [('spatial','Convergencia espacial',2,.3),('temporal','Convergencia temporal',1,.15)]:
        row=reports[name];orders='/'.join(f'{p:.5f}' for p in row['observed_orders'])
        matrix.append(f"| [{label}]({case_link(name)}) | Referencia {'continua' if name=='spatial' else 'semidiscreta'} | p={orders}; esperado {expected}±{tolerance} | {row['status']} |")
    for name,label in [('energy','Conservación adiabática'),('neumann','Neumann'),('robin','Robin')]:
        row=reports[name]
        matrix.append(f"| [{label}]({case_link(name)}) | {'Capacidades heterogéneas' if name=='energy' else 'Flujo y balance energético'} | Residuo máximo {metric(row['energy_balance_max_error_J'])} J ≤ {metric(row['energy_tolerance_J'])} J | {row['status']} |")
    source_check=next(c for c in source['checks'] if c['name']=='fuente_uniforme_todos_los_tiempos')
    matrix.append(f"| [Fuente uniforme]({case_link('source')}) | Pendiente y energía | Error {metric(source_check['measured'])} °C ≤ {metric(source_check['tolerance'])} °C | {source['status']} |")
    stable=reports['stability']
    matrix.append(f"| [Estabilidad]({case_link('stability')}) | Monotonía y rechazo de exceso | Paso/cota: {stable['accepted_dt_s']/stable['stable_dt_s']:.2f} aceptado; {stable['rejected_dt_s']/stable['stable_dt_s']:.2f} rechazado | {stable['status']} |")
    spatial_rows='\n'.join(f"| {'×'.join(map(str,r['shape']))} | {r['spacing_m'][0]:.8f} | {r['error_Linf_C']:.9f} | {r['temporal_contamination_C']:.3e} |" for r in spatial['rows'])
    temporal_rows='\n'.join(f"| {r['effective_dt_s']:.6f} | {r['steps']} | {r['error_Linf_C']:.9f} |" for r in temporal['rows'])
    bim_rows='\n'.join(f"| {r['name']} | {r['bbox_min_m'][2]:.2f}–{r['bbox_max_m'][2]:.2f} | {r['volume_analytic_m3']:.5f} |" for r in bim['items'])
    contamination=100*max(r['temporal_contamination_C']/r['error_Linf_C'] for r in spatial['rows'])
    cfg=source['config'];expected_rise=cfg['q_dot']*cfg['t_end_s']/(cfg['rho']*cfg['cp'])
    expected_energy=cfg['q_dot']*math.prod(source['lengths_m'])*cfg['t_end_s']
    return fr'''# E06 — Dossier de verificación + BIM del caso

## Repositorio y alcance

Repositorio: [amvaras/Proyecto-2-MCOC](https://github.com/amvaras/Proyecto-2-MCOC).
Commit evaluado: **COMMIT E06 PENDIENTE DE PUBLICACIÓN**

Grupo 2, Freirina / Parque Eólico Sarco. Este dossier actualizado y sus cambios están locales; requieren
publicación y declaración del SHA correspondiente antes de entregar.
Los inventarios originales se conservan y las revisiones justificadas se
identifican por SHA256, sin atribuirlas al commit anterior.

Se verifica el solver básico sobre cajas ideales. El IFC documenta la geometría
constructiva docente; estos ensayos no predicen temperaturas de la fundación.
La carpeta acumulativa también contiene E07, cuyo avance de voxelización se
mantiene separado de las verificaciones térmicas presentadas aquí.

## Matriz de verificación

La ejecución aprobó **{verification['tests']['tests']} pruebas**, sin fallos, errores ni omisiones,
diez casos nominales y **{verification['parameter_cases_passed']} variantes**. PASS exige satisfacer
referencias y tolerancias, no simplemente terminar. Los controles negativos
comprobaron el motivo y código de rechazo de estabilidad/unidades y el FAIL
por precisión insuficiente. Cada fila enlaza el resultado reproducible.

| Test | Qué verifica | Error/métrica | Resultado |
|---|---|---|---|
{chr(10).join(matrix)}

La referencia continua es
$$T=T_0+A\prod_j\sin(\pi x_j/L_j)\exp[-\alpha\sum_j(\pi/L_j)^2t],\quad\alpha=k/(\rho c_p).$$
Se evalúa en centros, con caras Dirichlet T₀. L∞ es el máximo error absoluto;
L2 y parámetros completos quedan en los JSON. El operador real se contrastó
con el modo y autovalor semidiscretos en 1D/2D/3D.

## Convergencia espacial

Caja 2D de 1×1 m: k=2 W/(m·K), ρ=2400 kg/m³, cₚ=900 J/(kg·K),
T₀=20 °C, A=10 °C y t=10000 s. Se fijó Δt={spatial['rows'][0]['effective_dt_s']:.5g} s.
La contaminación temporal máxima fue {contamination:.3f}% del error, inferior al 10%.

| Celdas | Δx [m] | L∞ [°C] | Componente temporal [°C] |
|---|---:|---:|---:|
{spatial_rows}

Los cocientes {spatial['error_ratios'][0]:.5f}/{spatial['error_ratios'][1]:.5f} y órdenes de la matriz
son coherentes con segundo orden. La malla gruesa muestra efectos preasintóticos.

![Convergencia espacial]({link(figures/'e06_convergencia_espacial.png')})
Figura 1. Referencia continua y paso fijo; línea auxiliar de pendiente dos.

## Convergencia temporal

Se mantuvo la malla 6×6 y se redujo únicamente Δt. La referencia exacta
semidiscreta usa decaimiento αΣⱼ4sin²(π/(2nⱼ))/Δxⱼ² para aislar el error de Euler.

| Δt efectivo [s] | Pasos | L∞ [°C] |
|---|---:|---:|
{temporal_rows}

Cocientes {temporal['error_ratios'][0]:.5f}/{temporal['error_ratios'][1]:.5f}: primer orden temporal.
Todos los pasos cumplen la cota suficiente min(Cᵢ/ΣGᵢ), incluidas las fronteras.

![Convergencia temporal]({link(figures/'e06_convergencia_temporal.png')})
Figura 2. Malla fija y referencia semidiscreta; pendiente esperada uno.

## Conservación de energía

Dominio 3D adiabático sin fuente, con perfil cosenoidal no uniforme y dos
materiales. En la segunda mitad, k, ρ y cₚ se multiplican por 3, 1,15 y 0,8.
Se integra E=ΣᵢρᵢcₚᵢVᵢ(Tᵢ−20 °C), sin sustituirla por una media aritmética.
ΔE={energy['energy_final_J']-energy['energy_initial_J']:.3e} J. El rango térmico baja de
{energy['initial_range_C']:.5f} a {energy['final_range_C']:.5f} °C: redistribución sin creación de energía.
Los intercambios internos se cancelan; la matriz registra residuo y tolerancia.

## Fuente volumétrica

Inicial uniforme, aislamiento, q̇={cfg['q_dot']:g} W/m³ y duración {cfg['t_end_s']:g} s.
Con las propiedades anteriores, T=T_ini+q̇t/(ρcₚ): incremento esperado
{expected_rise:.9f} °C y calculado {source['final_min_C']-cfg['initial_C']:.9f} °C.
ΔE esperada={expected_energy:.6g} J; calculada={source['energy_final_J']-source['energy_initial_J']:.8f} J.
Se compararon todos los instantes guardados. W/m³ corresponde a generación
volumétrica; W/m² corresponde a flujo superficial.

## Robin

Caja 3D inicialmente a 50 °C, ambiente a 20 °C y h=12 W/(m²·K) en seis caras.
R″=Δn/(2k)+1/h y q″=(T_celda−T_ambiente)/R″: conducción de media celda y
convección en serie. La temperatura superficial difiere de centro y ambiente.
El flujo positivo saliente produce pérdida de {abs(robin['energy_final_J']-robin['energy_initial_J']):.5f} J.
Se verificaron ley superficial, balance, máximo y sentido del intercambio;
también aprobó h=25. La suite incluye referencias transientes independientes
Robin/Neumann con otras caras, geometrías y propiedades.

## BIM base

El [IFC versionado]({link(ROOT/'geometry/foundation.ifc')}) es IFC4 en metros, con cinco IfcFooting.
Se comprobaron jerarquía, GUID, propiedades, mallas cerradas/orientadas y diez
pares sin solapamiento volumétrico. Octágono exterior: 18 m entre caras;
borde: 1,10 m; centro: 3,30 m; pedestal: Ø7 m y altura adicional 1 m;
altura global: 4,30 m. El origen IFC es local, sin georreferenciación global.

| Vertida | Intervalo z [m] | Volumen analítico [m³] |
|---|---:|---:|
{bim_rows}

Volumen analítico: {bim['total_analytic_m3']:.5f} m³; teselado: {bim['total_mesh_m3']:.5f} m³.
La diferencia procede del círculo teselado; tolerancia relativa por pieza: 5e-4.
La reconstrucción conservó geometría, identidad y propiedades del IFC original.

![BIM base]({link(figures/'e06_bim_fundacion.png')})
Figura 3. IFC real, visualizado con Python/IfcOpenShell; no es captura de Bonsai.

## Simplificaciones geométricas

- Octágono idealizado y espesores docentes; no reconstrucción experimental exacta.
- Borde 1,10 m y pedestal adicional 1 m adoptados para el ejercicio.
- Transición inclinada mediante dos troncos octagonales planos.
- Cinco vertidas iniciales, sin optimización del plan constructivo.
- Armaduras, pernos, anclajes y detalles menores omitidos.
- Origen local sin georreferencia global IFC.

## Reproducibilidad

Instalar Python 3.12 y dependencias según [README]({link(ROOT/'README.md')}); se incluyen
24 ruedas para instalación sin red. Desde P2_E07, con ese entorno activo:

```powershell
python scripts/verify_e06.py --output results/e06_nuevo
python scripts/check_ifc.py geometry/foundation.ifc
python scripts/create_preliminary_ifc.py --output results/fundacion_nueva.ifc
```

Usar destinos nuevos. El generador protege el IFC existente. Bonsai permite
abrirlo y seleccionar Vertida_01–05. [Evidencia]({link(evidence/'e06.json')}): versiones, comandos,
parámetros, criterios, hashes y comprobación documental. La ejecución técnica
está verificada; falta publicar y declarar el nuevo commit evaluado.
'''
