"""Auditar datos E11 y reproducir offline sin conservar otra corrida oficial."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from unittest.mock import patch
import xml.etree.ElementTree as ET

import numpy as np
import pyvista as pv
from PIL import Image
from mcoc_p2.e11.pipeline import ROOT, run, write_json
from mcoc_p2.e11.weather import validate, window
from mcoc_p2.e11.vtkio import check_vtk
from mcoc_p2.housekeeping import configure_runtime


def arrays(path):
    with np.load(path) as data:
        return {k: data[k] for k in data.files}


def audit(result, vtk_folder):
    s=json.loads((result/'summary.json').read_text(encoding='utf-8'))
    c=s['configuration']; p=c['physics']; g=arrays(result/'grid.npz'); f=arrays(result/'fields.npz')
    snapshot=validate(ROOT/c['snapshot'])
    weather=window(ROOT/c['snapshot'],c['simulation_start_utc'],p['t_end_s'])
    assert hashlib.sha256((ROOT/c['ifc']).read_bytes()).hexdigest()==s['ifc_sha256']
    assert np.all(np.diff(f['times_s'])>0) and f['times_s'][-1]==p['t_end_s']
    assert np.array_equal(g['occupation_mask'],g['vertida_id']>0)
    assert np.array_equal(g['occupied_flat_indices'],np.flatnonzero(g['occupation_mask']))
    labels=g['vertida_id'][g['occupation_mask']]
    births=np.array([next(e['activation_s'] for e in p['events'] if e['pour_id']==pid) for pid in labels])
    np.testing.assert_array_equal(f['active'],f['times_s'][:,None]>=births)
    stats=arrays(result/'statistics.npz'); volume=float(np.prod(g['spacing_m']))
    capacity=np.array([volume*{**p['material'],**next(e.get('material',{}) for e in p['events'] if e['pour_id']==pid)}['rho']*
                        {**p['material'],**next(e.get('material',{}) for e in p['events'] if e['pour_id']==pid)}['cp'] for pid in labels])
    balances={}
    for name in ('weather','constant'):
        values=f[name+'_C']; active=f['active']; steps=arrays(result/(name+'_steps.npz'))
        assert np.isfinite(values).all() and np.all(values[~active]==0)
        initial=float(np.sum(capacity[active[0]]*(values[0,active[0]]-p['energy_reference_C'])))
        final=float(np.sum(capacity[active[-1]]*(values[-1,active[-1]]-p['energy_reference_C'])))
        residual=final-initial-steps['hydration_energy_J'].sum()+steps['outward_energy_J'].sum()-steps['placement_energy_J'].sum()
        tolerance=s['energy'][name]['tolerance_J']
        assert abs(residual)<=tolerance and np.max(abs(steps['balance_residual_J']))<=tolerance
        assert all(s['checks'][name].values()) and np.all(steps['dt_over_limit']<=p['safety']*(1+1e-12))
        if name=='weather':
            expected=np.array([weather.at(t).air_C for t in stats['weather_time_s']])
            np.testing.assert_array_equal(expected,stats['weather_ambient_C'])
        for frame,t in enumerate(f['times_s']):
            i=int(np.flatnonzero(stats[name+'_time_s']==t)[0])
            np.testing.assert_allclose(values[frame,active[frame]].max(),stats[name+'_Tmax_C'][i],rtol=0,atol=1e-12)
        balances[name]=dict(residual_reconstructed_J=residual,tolerance_J=tolerance)
    a,b=arrays(result/'weather_steps.npz'),arrays(result/'constant_steps.npz')
    np.testing.assert_array_equal(a['dt_s'],b['dt_s'])
    np.testing.assert_array_equal(a['hydration_energy_J'],b['hydration_energy_J'])
    active=f['active'][-1]; delta=float(np.max(abs(f['weather_C'][-1,active]-f['constant_C'][-1,active])))
    assert delta>0 and delta==s['comparison']['final_field_Linf_C']
    manifest=json.loads((vtk_folder/'manifest.json').read_text(encoding='utf-8')); vtk=[]
    assert len(manifest['states'])>=3
    for row in manifest['states']:
        i=row['frame']; T=np.zeros(g['vertida_id'].size); mask=np.zeros(T.size,dtype=bool)
        T[g['occupied_flat_indices']]=f['weather_C'][i]; mask[g['occupied_flat_indices']]=f['active'][i]
        path=vtk_folder/row['file']; grid=pv.read(path)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
        vtk.append(check_vtk(grid,g['vertida_id'],g['origin_m'],g['spacing_m'],T.reshape(g['vertida_id'].shape),mask.reshape(g['vertida_id'].shape)))
    reader=pv.get_reader(vtk_folder/'e11.pvd')
    assert reader.time_values==[r['time_h']*3600 for r in manifest['states']]
    for time in reader.time_values:
        reader.set_active_time_value(time); assert reader.read().n_blocks==1
    live=grid.threshold(.5,scalars='active')
    assert live.slice(normal='y',origin=(0,0,1.65)).n_cells>0
    assert live.clip(normal='y',origin=(0,0,1.65)).n_cells>0
    figures={}
    for path in sorted((ROOT/'figures').glob('e11_*.png')):
        with Image.open(path) as im:
            im.verify()
        figures[path.name]=path.stat().st_size
    assert {'e11_ambiente.png','e11_tmax.png','e11_comparacion.png','e11_slice.png','e11_clip.png'}<=figures.keys()
    return dict(status='PASS',snapshot_sha256=snapshot.metadata['raw_sha256'],balances=balances,
                vtk_roundtrip=vtk,figures=figures,final_field_difference_C=delta)


def reproduce(result):
    """Red HTTP bloqueada y comparación exacta de todas las matrices guardadas."""
    cfg=json.loads((result/'inputs.json').read_text(encoding='utf-8'))
    parent=ROOT/'.runtime'; parent.mkdir(exist_ok=True)
    temporary=Path(tempfile.mkdtemp(prefix='e11-reproduce-',dir=parent)).resolve()
    (temporary/'.owned').write_text('E11 reproduction',encoding='utf-8')
    compared=[]
    def no_network(*args,**kwargs):
        raise AssertionError('Reproducción intentó acceder a la red')
    try:
        with patch('urllib.request.urlopen',no_network), patch('mcoc_p2.e10.weather.urlopen',no_network):
            report=run(cfg,temporary/'result',plots=False,export=False)
        for name in ('grid.npz','fields.npz','statistics.npz','weather_steps.npz','constant_steps.npz'):
            original=arrays(result/name); repeated=arrays(temporary/'result'/name)
            assert original.keys()==repeated.keys()
            for key in original:
                np.testing.assert_array_equal(original[key],repeated[key])
                compared.append(name+':'+key)
        return dict(status='PASS',network='urlopen prohibited',exact_arrays=compared,elapsed_s=report['elapsed_s'],
                    source_sha256=report['source_sha256'])
    finally:
        if temporary.parent==parent.resolve() and not temporary.is_symlink() and not temporary.is_junction() and (temporary/'.owned').read_text(encoding='utf-8')=='E11 reproduction':
            shutil.rmtree(temporary)
        try: parent.rmdir()
        except OSError: pass


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reproduce',action='store_true'); a=p.parse_args()
    result=ROOT/'results/e11'; report=audit(result,ROOT/'vtk/e11')
    if a.reproduce: report['offline_reproduction']=reproduce(result)
    junit=ROOT/'results/verification/tests.xml'
    if junit.exists():
        suites=ET.parse(junit).getroot().iter('testsuite')
        counts={k:0 for k in ('tests','failures','errors','skipped')}
        for suite in suites:
            for k in counts: counts[k]+=int(suite.get(k,'0'))
        report['regression']=counts
        assert counts['failures']==counts['errors']==counts['skipped']==0
    gui=ROOT/'results/verification/gui_session.json'
    if gui.exists():
        session=json.loads(gui.read_text(encoding='utf-8'))
        actions={r['action'] for r in session['actions']}
        report['native_gui_log_valid']=not session['off_screen'] and {'native_open','slice','clip','toggle','time','capture','native_closed'}<=actions
        assert report['native_gui_log_valid']
    target=ROOT/'results/verification/e11.json'; target.parent.mkdir(parents=True,exist_ok=True)
    write_json(target,report);print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    configure_runtime(ROOT); main()
