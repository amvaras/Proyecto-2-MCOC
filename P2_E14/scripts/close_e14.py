"""Auditoría reproducible del conjunto oficial, sin integrar de nuevo temperatura."""
from pathlib import Path
import importlib.util,hashlib,math,json,sys,subprocess,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from mcoc_p2.e11.pipeline import ROOT
from mcoc_p2.e14.io import read,write,fingerprint,source_hashes
from mcoc_p2.e14.workflow import load_manifest,validate_chunk,aggregate
from mcoc_p2.e14.sampling import sample_bank
from mcoc_p2.housekeeping import configure_runtime

def main():
    reports={};all_rows={}
    for kind in ('enumeration','monte_carlo'):
        folder=ROOT/'results/e14'/kind;m=load_manifest(folder/'manifest.json');a=aggregate(folder/'manifest.json');saved=read(folder/'summary.json')
        assert a['plans']==saved['plans'] and a['manifest_fingerprint']==saved['manifest_fingerprint']
        rows={}
        for i in range(len(m['chunks'])):
            ch=validate_chunk(read(folder/'chunks'/f'chunk-{i:04d}.json'),m,i)
            assert ch['status']=='passed'
            for e in ch['entries']:
                r=e['row'];assert r['fail_joint']==(r['Tmax_C']>70 or r['delta_C']>20)
                assert r['g_T']==70-r['Tmax_C'] and r['g_Delta']==20-r['delta_C']
                assert all(r['checks'].values()) and all(math.isfinite(r[k]) for k in ('Tmax_C','delta_C','g_T','g_Delta'))
                rows[e['physics_key']]=r
        if kind=='monte_carlo':assert m['bank']==sample_bank(m['configuration']['master_seed'],m['configuration']['N'],m['scenarios'])
        # Referencia OR independiente de las funciones de riesgo del paquete.
        for pi,p in enumerate(m['configuration']['plans']):
            rr=[rows[m['tasks'][j]['physics_key']] for j in m['mapping'][pi]];flags=[r['Tmax_C']>70 or r['delta_C']>20 for r in rr]
            truth=sum(s['weight']*f for s,f in zip(m['scenarios'],flags)) if kind=='enumeration' else sum(flags)/len(flags)
            assert abs(truth-a['plans'][pi]['P_joint'])<2e-15
        reports[kind]=dict(status='PASS',draws_per_plan=m['bank']['N'],plans=len(a['plans']),unique_physics=len(rows),cache_hits=a['cache_hits'],manifest_fingerprint=m['fingerprint'])
        all_rows[kind]=rows
    assert set(all_rows['monte_carlo'])==set(all_rows['enumeration'])
    # Inversión binomial independiente también a N=10000, sin usar beta_cdf.
    def cdf(k,n,p):
        if p==0:return 1.
        if p==1:return float(k>=n)
        terms=[math.lgamma(n+1)-math.lgamma(i+1)-math.lgamma(n-i+1)+i*math.log(p)+(n-i)*math.log1p(-p) for i in range(k+1)]
        peak=max(terms);return math.exp(peak)*math.fsum(math.exp(x-peak) for x in terms)
    ci_checks=[];misses=[]
    en=read(ROOT/'results/e14/enumeration/summary.json');mc=read(ROOT/'results/e14/monte_carlo/summary.json')
    for p,q in zip(en['plans'],mc['plans']):
        k,n=q['failures'],q['N'];lo,hi=q['CI'];tails=[]
        if k>0:tails.append(1-cdf(k-1,n,lo))
        if k<n:tails.append(cdf(k,n,hi))
        assert all(abs(t-.025)<1e-9 for t in tails)
        ci_checks.append(dict(plan=p['plan'],binomial_tails=tails,target=.025))
        if not lo<=p['P_joint']<=hi:misses.append(dict(plan=p['plan'],enumeration=p['P_joint'],MC=q['P_joint'],CI=q['CI']))
    # Copia autónoma: import y todos los inputs de los casos viven aquí.
    import mcoc_p2
    assert Path(mcoc_p2.__file__).resolve().is_relative_to(ROOT/'src')
    for r in all_rows['enumeration'].values():
        for key in ('ifc','snapshot'):assert (ROOT/r['configuration'][key]).resolve().is_relative_to(ROOT)
    # E13 original: comparar inventario científico/fuente antes y después.
    spec=importlib.util.spec_from_file_location('delivery_builder',ROOT/'scripts/create_delivery.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    integrity=read(ROOT/'results/verification/E13_integrity.json');after=builder.inventory(ROOT.parent/'P2_E13')
    assert integrity['before']==after,'E13 cambió; auditar antes de declarar integridad'
    integrity.update(after=after,status='PASS',files=len(after),scope='Código/datos/resultados; excluye entornos y caches recreables')
    write(ROOT/'results/verification/E13_integrity.json',integrity,replace=True)
    pictures=read(ROOT/'results/e14/figures.json')
    for row in pictures['figures']:
        p=ROOT/row['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
        with Image.open(p) as im:assert 'provenance' in im.info;im.verify()
    num=read(ROOT/'results/verification/numerics_e14.json');fields=read(ROOT/'results/verification/fields_e14.json');par=read(ROOT/'results/verification/parallel.json');hpc=read(ROOT/'results/verification/hpc.json')
    assert num['status']==fields['status']==par['status']==hpc['status']=='PASS' and num['all_checks']
    assert par['actual_solver_runs']==6 and par['exact_metrics'] and not par['real_cluster']
    # Clasificaciones con cara 0 mm, S25 y centro del borde: no son métricas equivalentes.
    definition_flips=[]
    for r in num['controls']:
        for key in ('delta_face0_C','delta_boundary_centers_C'):
            if (r[key]>20)!=(r['delta_C']>20):definition_flips.append(dict(plan=r['plan'],scenario=r['scenario'],control=r['control'],alternative=key,delta_C=r['delta_C'],alternative_C=r[key]))
    pip=subprocess.run([sys.executable,'-m','pip','check'],capture_output=True,text=True);assert pip.returncode==0,pip.stdout+pip.stderr
    tree=ET.parse(ROOT/'results/verification/junit.xml');suites=list(tree.getroot().iter('testsuite'))
    tests=sum(int(s.get('tests',0)) for s in suites);failures=sum(int(s.get('failures',0)) for s in suites);errors=sum(int(s.get('errors',0)) for s in suites);skipped=sum(int(s.get('skipped',0)) for s in suites)
    assert tests>=441 and failures==errors==skipped==0
    baseline=read(ROOT/'results/verification/base.json')['files'];changed=[r['path'] for r in baseline if (ROOT/r['path']).is_file() and hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()!=r['sha256']]
    added=[p for p in builder.inventory(ROOT) if p not in {r['path'] for r in baseline}]
    code={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for top in ('src','examples','scripts','web','tests') for p in (ROOT/top).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.js','.mjs','.sbatch','.sh','.ps1'}}
    physical_time=read(ROOT/'results/verification/aggregation_fix.json')['original_physical_stage_elapsed_s']
    report=dict(status='PASS',reports=reports,tests=dict(total=tests,passed=tests,failed=failures,errors=errors,skipped=skipped,time_s=sum(float(s.get('time',0)) for s in suites)),
        pip_check=pip.stdout.strip(),import_path=str(Path(mcoc_p2.__file__).resolve()),E13_intact=True,previous_deliveries_written=False,
        browser_verification=read(ROOT/'results/verification/browser_e14.json')['browsers'],CI_independent_binomial_checks=ci_checks,reference_outside_MC_CI=misses,
        resolved_incidents=['Agregación duplicaba kwargs de extremos: corregida sin repetir solves','Lectores Windows/OneDrive bloquearon replace: reintento atómico acotado probado','Carpeta vacía readonly OneDrive bloqueó limpieza QA: corregida sin retirar archivos desconocidos','Una regresión intermedia registró WinError 10053 al rechazar POST con cuerpo sin consumir; cuerpo acotado se consume antes de guard, sin interpretar inputs o ejecutar acciones antes de autorización'],
        dependency_warnings='VTK numpy_support usa asignación shape deprecada por NumPy 2.5; 305 avisos en la regresión observada, sin fallos físicos',
        figures=pictures['count'],new_full_cases=72,reused_base_cases=120,directed_screen_cases=6,numerical_controls=len(num['controls']),parallel_forced_solves=6,
        representative_solutions=2,representative_role='Clima variable + control constante; un caso crítico E14; no muestra Monte Carlo nueva',
        physical_stage_s=physical_time,monte_carlo_stage_s=read(ROOT/'results/e14/monte_carlo/summary.json')['execution']['elapsed_s'],
        classification_flips_mesh_area=num['observed_classification_changes'],classification_flips_alternative_surface_definitions=definition_flips,
        changed_inherited_files=changed,added_files=added,code_sha256=code,kernel_sha256=source_hashes(),real_cluster='NO VERIFICADO',publication='PENDIENTE')
    write(ROOT/'results/verification/closure_e14.json',report,replace=True)
    env=read(ROOT/'results/verification/environment.json');env['final_regression']=dict(tests=tests,passed=tests,failed=0,failures=0,errors=0,skipped=0,status='PASS',junit='results/verification/junit.xml');write(ROOT/'results/verification/environment.json',env,replace=True)
    en=read(ROOT/'results/e14/enumeration/summary.json');mc=read(ROOT/'results/e14/monte_carlo/summary.json')
    lines=['# E14 · Estado técnico comprobado','',
        'Infraestructura local implementada y verificada. No existe un plan factible entre los ocho evaluados. Clúster real NO VERIFICADO. Publicación PENDIENTE. Chrome y el navegador integrado fueron comprobados manualmente; evidencia en `results/verification/browser_e14.json`.','',
        '| Plan | D [h] | H [h] | Tmax envolvente [°C] | ΔTmax [°C] | Pf exacta | MC / IC95% |', '|---|---:|---:|---:|---:|---:|---|']
    cfg=read(ROOT/'configs/e14/study.json')
    for p,q,item in zip(en['plans'],mc['plans'],cfg['plans']):lines.append(f"| {p['plan']} | {p['D_h']:.3f} | {item['horizon_h']:g} | {p['Tmax_C']:.4f} | {p['delta_C']:.4f} | {100*p['P_joint']:.1f}% | {100*q['P_joint']:.2f}% / [{100*q['CI'][0]:.3f}; {100*q['CI'][1]:.3f}]% |")
    lines+=['','P(Tmax>70)=0 en los 24 átomos de todos los planes; la falla conjunta coincide aquí con exceder ΔT. No se modificaron umbrales, pesos, fuentes, suelo o conductividad para forzar cumplimiento.', '',
        'El IC95% de curado_rapido [94,025%; 94,929%] no contiene su enumeración 95%. Es una realización posible con cobertura nominal del 95%, no una garantía para cada muestra; tampoco son intervalos simultáneos entre planes. Se mantuvieron N y semilla declarados. La inversión se comprobó además mediante sumas binomiales independientes a N=10000, sin reutilizar beta_cdf. La decisión usa la enumeración exacta del modelo de 24 átomos.', '',
        f"Ejecución: 120 casos base reutilizados, 72 nuevos a malla final en {physical_time:.3f} s con dos procesos. Seis exploraciones previas dirigidas; 13 controles numéricos; seis solves de equivalencia secuencial/paralela; dos soluciones del caso ilustrativo (clima variable/control constante). MC: 10000 draws/plan, 80000 evaluaciones de indicadores, 192 inputs únicos reutilizados, cero solves térmicos adicionales en esa fase. No confundir draws con ensayos o solves nuevos.", '',
        f"Regresión integrada: **{tests} aprobadas, 0 fallidas, 0 errores, 0 omitidas**; {report['tests']['time_s']:.2f} s. Se conservan las 428 pruebas heredadas y se añaden {tests-428}. pip check correcto. VTK genera 305 avisos de deprecación por asignación shape con NumPy 2.5; se documentan sin relajar pruebas o modificar dependencias instaladas. Campos del caso crítico: {fields['all_time_fields']} estados de integración y eventos, máximos y S25 recalculados desde arrays; fuente integrada independientemente y VTK verificados.", '',
        'Malla final: 28652 celdas ocupadas, volumen 638,2233 m³. IFC 636,877718 m³; analítico 636,885036 m³. Área staircase 758,88 m² frente a 641,971763 m² IFC (+18,2108%). Refinamiento .30/.30/.055 m y dt 450 s dirigidos; reescala global de área separando aire/suelo. No se observó cambio de clase en los 13 controles, incluidos los tres más próximos al límite. Las definiciones cara 0 mm/centro de borde se guardan como diagnóstico, no sustituyen S25. No se demuestra convergencia global ni se obtiene una cota completa del error.', '',
        'Caso crítico ilustrativo: curado_frio5/M4_SS_m00, H=744 h, retiro=600 h, máximo 51,4824°C a 213,5 h y ΔT=28,8110°C a 642,25 h (interior caliente frente a lateral frío). El balance global weather tiene residuo −4,20e−5 J frente a tolerancia 0,6393 J. Máximos globales del plan y de un escenario se distinguen en la tabla y el visor.', '',
        f"Figuras: {pictures['count']} PNG, todas regeneradas desde datos locales, con pies y metadata de procedencia; `results/e14/figures.json` registra SHA. Campos completos solo para un caso E14 y la base E13 vigente. No cientos de exportaciones repetidas.", '',
        'Mecanismo y decisiones: prolongar esperas con vertidas frías puede elevar el criterio global al añadir hormigón nuevo a 8°C frente al ya caliente. Curado prolongado y más aislación mejoran el diferencial antes del retiro, pero el enfriamiento exterior posterior sigue dominando. Se exploró suministro acotado 5–22°C, aislante existente 25–100 mm, esperas y retiro; sin recursos ilimitados. La literatura técnica [USBR](https://www.usbr.gov/damsafety/TechDev/DSOTechDev/DSO-12-02.pdf) describe control térmico mediante protección/enfriamiento; no calibra los espesores ni acredita la capacidad frigorífica usada en estos escenarios.', '',
        'La búsqueda fue dirigida, no exhaustiva: ocho planes no prueban imposibilidad global. Quedan por contrastar con el profesor: significado global de S25/umbral, comparabilidad y pesos de SS/22A, mezcla real, dependencia térmica de hidratación, clima y capacidad de enfriamiento, juntas y contacto con suelo. No se recomienda un plan de obra sobre estas hipótesis.', '',
        'Slurm: Bash -n y wrapper array real emulado localmente pasan; campos/semillas/métricas secuenciales y paralelos son exactamente iguales en tres inputs, seis solves sin cache. No hay host/cuenta/job/sacct remoto ni instalación Linux verificados. Esa ejecución requiere acceso al centro.', '',
        f"Integridad: {len(after)} archivos de E13 comparados SHA256 antes/después, sin cambios; E01–E12 no recibieron escrituras. E14 importa su propio src y contiene físicamente datos/IFC/código, sin enlaces o rutas obligatorias a otra entrega. No se hicieron ramas, commits ni publicaciones. No se crearon ZIP o respaldos. Se copió selectivamente la base científica vigente autorizada.", '',
        'Incidencias resueltas: agregación inicial duplicaba claves de extremos y falló después de completar los 192 inputs. Se corrigió el merge y se reagregaron filas verificadas sin repetir térmica; migración de huellas documentada en `aggregation_fix.json`. Un lector concurrente de progreso en Windows/OneDrive produjo WinError 5: se añadió reintento atómico acotado. La limpieza de un job QA encontró una carpeta vacía readonly de OneDrive: se corrigió el retiro individual con preflight y se completó el inventario. Una regresión intermedia tuvo 1 fallo/442 aprobadas por WinError 10053 en un rechazo HTTP: se consume el cuerpo acotado antes de validar origen/sesión, sin interpretar ni ejecutar inputs; los controles se conservan y la regresión final se repite. No se trataron estos fallos como casos térmicos seguros.', '',
        'HTML: un lote real de 200 draws desde la interfaz obtuvo Pf=83%, 23 inputs únicos todos reutilizados. Un diagnóstico nuevo a .9/.9/.275 m y 744 h produjo dos soluciones en 17,985 s y pasó balance/VTK. Se observaron tabla exacta, advertencias de inputs, semillas, curvas, activación a t=0, slice y clipping; Chrome mostró WebGL sin error en el instante crítico 642,25 h. Los dos jobs propios se retiraron tras conservar inputs, métricas, checks y SHA en browser_e14/browser_cleanup; no se versionan variantes gráficas duplicadas. El conjunto oficial no se alteró.', '',
        'Documentación técnica de continuidad: `E14_FORMULACION.md` y `E14_OPERACION.md`. Sin diapositivas, informe final ni dossier definitivo E15. Evidencia íntegra: `results/verification/closure_e14.json`, JUnit, fields_e14, numerics_e14, parallel, hpc y E13_integrity.', '']
    (ROOT/'docs/E14_ESTADO.md').write_text('\n'.join(lines),encoding='utf8')
    print(json.dumps({k:report[k] for k in ('status','tests','figures','E13_intact')},ensure_ascii=False,indent=2))
if __name__=='__main__':configure_runtime(ROOT);main()
