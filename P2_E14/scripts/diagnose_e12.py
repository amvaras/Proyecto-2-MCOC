"""Separar energía neta al aire/suelo usando estados iniciales de cada paso."""
import json
import numpy as np
from mcoc_p2.e11.pipeline import ROOT,write_json
from mcoc_p2.e12.pipeline import arrays
def main():
    s=json.loads((ROOT/'results/e13/representative/summary.json').read_text(encoding='utf8'))
    a=arrays(ROOT/'results/e13/representative/statistics.npz');steps=arrays(ROOT/'results/e13/representative/weather_steps.npz')
    i=np.searchsorted(a['weather_time_s'],steps['start_s']);np.testing.assert_array_equal(a['weather_time_s'][i],steps['start_s'])
    air=float(np.sum(a['weather_air_power_out_W'][i]*steps['dt_s']));soil=float(np.sum(a['weather_soil_power_out_W'][i]*steps['dt_s']));total=float(steps['outward_energy_J'].sum())
    assert abs(air+soil-total)<=s['energy']['weather']['tolerance_J']
    report=dict(status='PASS',method='Potencia al inicio exacto de cada paso tras activaciones/desmolde; consistente con Euler, sin integrar límites izquierdos como pasos',
                air_net_out_J=air,soil_net_out_J=soil,total_net_out_J=total,split_residual_J=air+soil-total,air_fraction_of_net_out=air/total,
                interpretation='El calor se acumula en el interior y el punto frío del máximo diferencial es lateral. Aire y suelo extraen energía; h y moldaje respaldan el diagnóstico, sin causalidad exclusiva.')
    write_json(ROOT/'results/verification/mechanism.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

