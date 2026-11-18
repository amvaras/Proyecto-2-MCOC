"""Read-only F02 results and the recorded thermal timeline for the local viewer."""
from functools import lru_cache
import hashlib

import numpy as np

from ..e14.io import ROOT, read
from ..e11.webdata import arrays

FOLDER = ROOT / 'results/f02'

@lru_cache(maxsize=1)
def model_data():
    path = FOLDER/'fields.npz'
    result = read(FOLDER/'enumeration.json')
    if hashlib.sha256(path.read_bytes()).hexdigest() != result['fields_sha256']:
        raise ValueError('Los campos F02 no coinciden con el manifiesto')
    return arrays(path)

def bootstrap():
    result = read(FOLDER/'enumeration.json')
    path = FOLDER/'controls.json'
    controls = read(path) if path.is_file() else None
    if controls is not None and result['kernel_sha256'] != controls['kernel_sha256']:
        raise ValueError('Enumeración y controles corresponden a versiones distintas')
    saved = result['configuration']
    representative = next(r for r in result['rows'] if r['scenario'] == saved['scenario_3d'])
    older = read(ROOT/'results/e14/enumeration/summary.json')
    data = model_data()
    t, labels, births = (data[k] for k in ('times_s','labels','births_s'))
    active = [np.unique(labels[births <= value]).tolist() for value in t]
    origin, spacing, shape = (data[k] for k in ('origins_m','spacing_m','shape'))
    temps = data['temperature_C'][births[None,:] <= t[:,None]]
    return dict(plans=[*older['plans'],result['summary']], generated_at_utc=result['generated_at_utc'],
        kernel_sha256=result['kernel_sha256'], e14_base=result['e14_base'], configuration=saved,
        scenarios=[dict(id=r['scenario'],weight=r['weight']) for r in result['rows']],
        controls=[dict(scenario=r['scenario'],delta_C=r['delta_C'],
                      spacing_m=r['configuration']['physics']['spacing_m'],
                      max_step_s=r['configuration']['physics']['max_step_s']) for r in (controls['rows'] if controls else [])],
        representative=representative['scenario'], water=representative['water'],
        peak=representative['peak'], delta_peak=representative['delta_peak'],
        max_power_kW=max(r['water']['max_kW'] for r in result['rows']),
        max_energy_GJ=max(r['energy']['cooling_J'] for r in result['rows'])/1e9,
        geometry=dict(bounds_m=[origin.tolist(),(origin+spacing*shape).tolist()],
                      spacing_m=spacing.tolist(),shape=shape.tolist(),origin_m=origin.tolist(),indices=data['indices'].tolist(),
                      centers_m=data['centers_m'].tolist(),labels=labels.tolist()),
        times_h=(t/3600).tolist(), active=active, range_C=[float(temps.min()),float(temps.max())],
        statistics={k:data[k].tolist() for k in ('stats_time_s','stats_Tmax_C','stats_S25_C','stats_delta_C')})

def frame(index):
    fields = model_data()['temperature_C']
    if not 0 <= index < len(fields):
        raise ValueError('Instante F02 fuera de rango')
    return fields[index].astype('<f4').tobytes()
