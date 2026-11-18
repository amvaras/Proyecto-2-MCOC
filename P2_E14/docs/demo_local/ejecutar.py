"""Demo local E14: usa el workflow y el solver existentes, sin Slurm."""
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import argparse
import html
import json
import os
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'src'))

from mcoc_p2.e14.io import read, write, inside, fingerprint
from mcoc_p2.e14.workflow import prepare, run_local, aggregate, load_manifest, validate_chunk
from mcoc_p2.e14.model import Model, catalog
from mcoc_p2.e14.sampling import sample_bank
from mcoc_p2.e14.store import Store
from mcoc_p2.housekeeping import configure_runtime


def configuration(args):
    parameters = read(ROOT / 'docs/demo_local/parametros.json')
    if args.N is not None:
        parameters['N'] = args.N
    if args.seed is not None:
        parameters['master_seed'] = args.seed
    if args.workers is not None:
        parameters['workers'] = args.workers
    if type(parameters['workers']) is not int or not 1 <= parameters['workers'] <= 4:
        raise ValueError('Usar entre uno y cuatro procesos locales')
    config = read(ROOT / 'configs/e14/study.json')
    known = {p['id']: p for p in config['plans']}
    ids = parameters['plan_ids']
    if not ids or len(ids) != len(set(ids)) or set(ids) - known.keys():
        raise ValueError('Elegir planes del estudio E14, sin repetirlos')
    config.update({k: parameters[k] for k in ('N', 'master_seed', 'spacing_m', 'step_s')})
    config['plans'] = [known[k] for k in ids]
    return config, parameters['workers']


def checked_results(folder, manifest, result):
    """Conteo OR independiente y comparación con casos originales del mismo input."""
    entries = {}
    pids = set()
    for i in range(len(manifest['chunks'])):
        chunk = validate_chunk(read(folder / 'chunks' / f'chunk-{i:04d}.json'), manifest, i)
        if chunk['status'] != 'passed':
            raise ValueError('Existe un input fallido; no presentar una probabilidad incompleta')
        pids.add(chunk['pid'])
        for entry in chunk['entries']:
            if entry['physics_key'] in entries:
                raise ValueError('Input duplicado')
            entries[entry['physics_key']] = entry['row']
    previous = {}
    for path in (ROOT / 'results/e14/enumeration/chunks').glob('*.json'):
        previous.update({e['physics_key']: e['row'] for e in read(path)['entries']})
    matching = 0
    field_hashes = 0
    for key, row in entries.items():
        if key not in previous:
            continue
        original = previous[key]
        for field in ('Tmax_C', 'delta_C', 'peak', 'delta_peak', 'energy'):
            if row[field] != original[field]:
                raise ValueError('Diferencia frente al caso original: ' + field)
        matching += 1
        if 'saved_fields_sha256' in original:
            if row['saved_fields_sha256'] != original['saved_fields_sha256']:
                raise ValueError('Los campos difieren del caso original')
            field_hashes += 1
    for pi, plan in enumerate(result['plans']):
        rows = [entries[manifest['tasks'][j]['physics_key']] for j in manifest['mapping'][pi]]
        flags = [r['Tmax_C'] > 70 or r['delta_C'] > 20 for r in rows]
        if plan['failures'] != sum(flags) or plan['P_joint'] != sum(flags) / len(flags):
            raise ValueError('La agregación no coincide con el conteo independiente')
        for point in plan['Pf_N']:
            if point['failures'] != sum(flags[:point['N']]):
                raise ValueError('Pf(N) inconsistente')
    recomputed = aggregate(folder / 'manifest.json')
    if recomputed['plans'] != result['plans']:
        raise ValueError('La agregación separada cambió los resultados')
    return dict(status='PASS', unique_inputs=len(entries), worker_pids=sorted(pids),
                observed_processes=len(pids), original_metrics_exact=matching,
                original_field_hashes_exact=field_hashes, independent_OR=True,
                separate_aggregation=True)


def reuse_known_inputs(config, cache):
    """Sembrar la caché de esta corrida, consultando la biblioteca original solo en lectura."""
    source = Store()
    model = Model()
    scenarios = catalog()
    bank = sample_bank(config['master_seed'], config['N'], scenarios)
    selected = sorted({draw['scenario_index'] for draw in bank['samples']})
    for plan in config['plans']:
        for i in selected:
            effective, _ = model.configuration(plan, scenarios[i], config['spacing_m'], config['step_s'])
            key = model.key(effective)
            row = source.get(key)
            if row is not None:
                write(cache / (key + '.json'), dict(physics_key=key, row=row, row_sha256=fingerprint(row)))


def render(folder, manifest, result, evidence):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 5), layout='constrained')
    for plan in result['plans']:
        points = plan['Pf_N']
        x = [p['N'] for p in points]
        ax.plot(x, [100*p['Pf'] for p in points], marker='o', label=plan['plan'])
        ax.fill_between(x, [100*p['CI'][0] for p in points],
                        [100*p['CI'][1] for p in points], alpha=.14)
    ax.axhline(5, color='#b63232', linestyle='--', label='Criterio 5 %')
    ax.set(xscale='log', xlabel='Número de realizaciones N', ylabel='Probabilidad conjunta [%]',
           ylim=(0, 101), title='Monte Carlo local · IC95 % puntual')
    ax.grid(alpha=.2)
    ax.legend(loc='best')
    fig.savefig(folder / 'pf_N.png', dpi=150)
    plt.close(fig)
    escape = lambda value: html.escape(str(value), quote=True)
    def pct(value):
        return f'{100*value:.2f} %'
    rows = ''.join('<tr>' + ''.join(f'<td>{escape(cell)}</td>' for cell in [
        p['plan'], p['N'], p['failures'], pct(p['P_joint']),
        f"[{pct(p['CI'][0])}; {pct(p['CI'][1])}]", f"{p['Tmax_C']:.3f}",
        f"{p['delta_C']:.3f}"]) + '</tr>' for p in result['plans'])
    seeds = ''.join('<tr>' + ''.join(f'<td>{escape(cell)}</td>' for cell in [
        p['realization'], p['scenario'], ', '.join(map(str, p['seed_words']))]) + '</tr>'
        for p in manifest['bank']['samples'][:8])
    cfg = manifest['configuration']
    document = f'''<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>E14 · Resultado local</title>
<style>body{{font:16px/1.6 system-ui,sans-serif;background:#eef4f4;color:#193638;margin:0}}
main{{max-width:1100px;margin:auto;padding:28px}}header,section{{background:white;border-radius:16px;padding:24px;margin:18px 0}}
h1,h2{{line-height:1.2}}.tag{{color:#0b7273;font-weight:700}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}}
.card{{background:#eef7f6;padding:16px;border-radius:12px}}strong.big{{display:block;font-size:26px}}
.table{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{padding:12px;text-align:left;border-bottom:1px solid #dae5e5}}
img{{width:100%;height:auto}}a{{color:#087375}}code{{word-break:break-all}}small{{color:#536c6f}}</style><main>
<header><span class="tag">E14 · Cálculo paralelo en este computador</span><h1>Demostración local terminada</h1>
<p>{escape(evidence['finished_at_chile'])} · Ejecución <code>{escape(folder.name)}</code></p>
<div class="cards"><div class="card">Muestras por plan<strong class="big">{cfg['N']}</strong></div>
<div class="card">Procesos observados<strong class="big">{evidence['checks']['observed_processes']}</strong></div>
<div class="card">Simulaciones nuevas<strong class="big">{evidence['new_thermal_solves']}</strong></div>
<div class="card">Tiempo de ejecución<strong class="big">{result['execution']['elapsed_s']:.1f} s</strong></div></div>
<p>Semilla maestra: <strong>{cfg['master_seed']}</strong>. Inputs físicos únicos: {result['unique_physics']}.
 Reutilizados: {result['cache_hits']}. Estado de verificaciones: <strong>PASS</strong>.</p>
<p>Se ejecutó con procesos locales. No se utilizó un cluster ni se asignó un JobID Slurm.</p></header>
<section><h2>Probabilidad y temperaturas</h2><div class="table"><table><tr><th>Plan</th><th>N</th><th>Fallas</th><th>Pf conjunta</th><th>IC95 %</th><th>Tmáx [°C]</th><th>ΔTmáx [°C]</th></tr>{rows}</table></div>
<p>Falla: Tmáx &gt; 70 °C <strong>o</strong> ΔTmáx &gt; 20 °C. Pf debe ser ≤ 5 %.
 El resultado depende del modelo y sus pesos declarados; no certifica seguridad de obra.</p></section>
<section><h2>Cómo cambia Pf al aumentar N</h2><img src="pf_N.png" alt="Estimación de probabilidad frente a N con intervalos de confianza">
<p>Las franjas muestran IC95 % puntuales. No incluyen incertidumbre de calibración ni error de malla.
 Las realizaciones remuestrean curvas e historias completas; N no equivale al número de ensayos experimentales o de simulaciones nuevas.</p></section>
<section><h2>Primeras semillas y escenarios</h2><div class="table"><table><tr><th>Realización</th><th>Escenario</th><th>Semilla derivada</th></tr>{seeds}</table></div>
<p>Cada ID deriva su generador desde la semilla maestra. Los planes comparten el banco de muestras para compararse.</p></section>
<section><h2>Evidencia guardada</h2><ul><li><a href="manifest.json">Inputs y todas las semillas</a></li>
<li><a href="summary.json">Métricas, probabilidades e intervalos</a></li><li><a href="verificacion_local.json">Verificación y procesos observados</a></li>
<li><a href="chunks/">Resultados separados por tarea</a></li></ul>
<small>Campos idénticos a referencias guardadas: {evidence['checks']['original_field_hashes_exact']} inputs.
 Métricas y balance idénticos: {evidence['checks']['original_metrics_exact']} inputs.
 La aceptación de esta demostración local en lugar del cluster corresponde al curso.</small></section></main></html>'''
    (folder / 'resumen.html').write_text(document, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--N', type=int)
    parser.add_argument('--seed', type=int)
    parser.add_argument('--workers', type=int)
    parser.add_argument('--reutilizar-oficial', action='store_true', help='Usar resultados conocidos para una demo rápida')
    parser.add_argument('--resume', type=Path, help='Manifest de una ejecución local interrumpida')
    parser.add_argument('--retry-failed', action='store_true')
    parser.add_argument('--abrir', action='store_true')
    args = parser.parse_args()
    os.chdir(ROOT)
    configure_runtime(ROOT)
    if args.resume:
        if args.reutilizar_oficial or any(x is not None for x in (args.N, args.seed, args.workers)):
            raise ValueError('Reanudar usa la configuración guardada, sin mezclar parámetros nuevos')
        path = inside(args.resume)
        folder = path.parent
        if not folder.is_relative_to(ROOT / 'results/verification/demo_local_e14'):
            raise ValueError('Seleccionar un manifest de esta demostración local')
        manifest = load_manifest(path)
        workers = 2
        if (folder / 'verificacion_local.json').exists():
            raise ValueError('Esta ejecución ya está verificada; abrir resumen.html o iniciar otra')
    else:
        config, workers = configuration(args)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        folder = ROOT / 'results/verification/demo_local_e14' / (stamp + '-' + uuid.uuid4().hex[:8])
        cache = folder.parent / 'cache' / folder.name
        if args.reutilizar_oficial:
            reuse_known_inputs(config, cache)
        manifest = prepare(config, folder, kind='mc', chunk_size=1, cache=cache)
    print(f"N={manifest['bank']['N']} · semilla={manifest['configuration']['master_seed']} · procesos={workers}", flush=True)
    print(f"{len(manifest['chunks'])} tareas · {manifest['estimate']['new']} simulaciones nuevas · {manifest['estimate']['reused']} reutilizadas", flush=True)
    print(f"Inputs guardados en {folder.relative_to(ROOT)}", flush=True)
    def progress(state):
        print(f"{state['completed_chunks']}/{state['total_chunks']} tareas · {state['last_status']} · {state['elapsed_s']:.1f} s", flush=True)
    result = run_local(folder / 'manifest.json', workers, retry_failed=args.retry_failed, progress=progress)
    checks = checked_results(folder, manifest, result)
    evidence = dict(status='PASS', mode='local_parallel', real_cluster_verified=False,
                    slurm_job_id=None, finished_at_chile=datetime.now(ZoneInfo('America/Santiago')).isoformat(),
                    manifest_fingerprint=manifest['fingerprint'], workers_requested=workers,
                    new_thermal_solves=result['unique_physics'] - result['cache_hits'],
                    reused_thermal_inputs=result['cache_hits'], execution=result['execution'], checks=checks)
    render(folder, manifest, result, evidence)
    write(folder / 'verificacion_local.json', evidence)
    print(f"PASS · Resumen: {folder / 'resumen.html'}", flush=True)
    for plan in result['plans']:
        print(f"{plan['plan']}: Pf={plan['P_joint']:.2%}, IC95%={plan['CI']}, N={plan['N']}", flush=True)
    if args.abrir:
        import webbrowser
        webbrowser.open((folder / 'resumen.html').as_uri())


if __name__ == '__main__':
    main()
