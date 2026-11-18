"""Inputs SI compartidos por consola e interfaz. Sin secuencias dentro del solver."""
from copy import deepcopy
import math
import numpy as np
from .. import Material, Dirichlet, Neumann, Robin
from ..e07.construction import PourEvent
from ..e07.hydration import AdiabaticCurve


def number(value, name, minimum=None, strict=False):
    if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value):
        raise ValueError(name+': se requiere un número real finito')
    if minimum is not None and (value<=minimum if strict else value<minimum):
        raise ValueError(name+': valor fuera de rango')
    return float(value)


def boundaries(cfg):
    result={axis+side:Robin(cfg['h_W_m2K'],cfg['ambient_C']) for axis in 'xyz' for side in '-+'}
    for face,spec in cfg.get('boundaries',{}).items():
        if face not in result or not isinstance(spec,dict):raise ValueError('Cara o condición de borde desconocida')
        kind=spec.get('type')
        if kind=='adiabatic' and spec.keys()=={'type'}:result[face]=Neumann()
        elif kind=='Neumann' and spec.keys()=={'type','outward_flux_W_m2'}:
            result[face]=Neumann(number(spec['outward_flux_W_m2'],'flujo'))
        elif kind=='Dirichlet' and spec.keys()=={'type','temperature_C'}:
            result[face]=Dirichlet(number(spec['temperature_C'],'temperatura de borde',-273.15,True))
        elif kind=='Robin' and spec.keys()=={'type','h_W_m2K','ambient_C'}:
            result[face]=Robin(number(spec['h_W_m2K'],'h',0),number(spec['ambient_C'],'ambiente',-273.15,True))
        else:raise ValueError('Condición de borde incompleta o con claves desconocidas')
    return result


def events_from_config(cfg):
    result=[]
    for supplied in cfg['events']:
        if not isinstance(supplied,dict) or supplied.keys()-{'pour_id','activation_s','initial_C','material','hydration'}:
            raise ValueError('Evento con claves desconocidas')
        item=dict(supplied)
        mat={**cfg['material'],**item.pop('material',{})}
        heat={**cfg['hydration'],**item.pop('hydration',{})}
        for name,value in mat.items():number(value,'material.'+name,0,True)
        for name,value in heat.items():number(value,'hydration.'+name,0,name=='duration_s')
        number(item['activation_s'],'inicio',0);number(item['initial_C'],'colocación',-273.15,True)
        result.append(PourEvent(**item,material=Material(**mat),hydration=AdiabaticCurve(**heat)))
    return result


def validate_config(data, solids):
    required={'spacing_m','resolutions_m','margin_m','t_end_s','max_step_s','save_interval_s',
              'safety','energy_reference_C','h_W_m2K','ambient_C','material','hydration','events'}
    if not isinstance(data,dict) or not required<=data.keys() or data.keys()-required-{'description','boundaries'}:
        raise ValueError('Configuración E08 incompleta o con claves desconocidas')
    cfg=deepcopy(data)
    ds=cfg['spacing_m']
    if isinstance(ds,(int,float)) and not isinstance(ds,bool):ds=[ds]*3
    if not isinstance(ds,list) or len(ds)!=3:raise ValueError('Resolución: un número o tres pasos XYZ')
    cfg['spacing_m']=[number(d,'Resolución',0,True) for d in ds]
    resolutions=cfg['resolutions_m']
    if not isinstance(resolutions,list) or not 3<=len(resolutions)<=6:raise ValueError('Usar tres a seis resoluciones para el estudio')
    for h in resolutions:number(h,'Resolución del estudio',0,True)
    if len(set(resolutions))!=len(resolutions):raise ValueError('Resoluciones del estudio distintas')
    for key in ('margin_m','t_end_s','h_W_m2K'):number(cfg[key],key,0)
    for key in ('max_step_s','save_interval_s','safety'):number(cfg[key],key,0,True)
    if cfg['safety']>1:raise ValueError('safety debe estar en (0,1]')
    number(cfg['ambient_C'],'ambiente',-273.15,True)
    number(cfg['energy_reference_C'],'referencia energética')
    if not isinstance(cfg['events'],list) or not cfg['events']:raise ValueError('Agregar eventos de vertida')
    for key in ('material','hydration'):
        if not isinstance(cfg[key],dict):raise ValueError(key+' debe ser un objeto')
    for name,value in cfg['material'].items():number(value,'material.'+name,0,True)
    for name,value in cfg['hydration'].items():number(value,'hydration.'+name,0,name=='duration_s')
    Material(**cfg['material']);AdiabaticCurve(**cfg['hydration'])
    events=events_from_config(cfg);ids=[e.pour_id for e in events]
    if len(ids)!=len(set(ids)) or set(ids)!={s.pour_id for s in solids}:
        raise ValueError('Debe haber exactamente un evento por VertidaID del IFC')
    if not isinstance(cfg.get('boundaries',{}),dict):raise ValueError('boundaries debe ser un objeto')
    boundaries(cfg)
    frames=math.ceil(cfg['t_end_s']/cfg['save_interval_s'])+len(events)+1
    if frames>401:raise ValueError('Más de 401 fotogramas: aumentar intervalo de guardado')
    low=np.min([s.mesh.low for s in solids],axis=0);high=np.max([s.mesh.high for s in solids],axis=0)
    for spacing in [cfg['spacing_m'],*[ [h]*3 for h in resolutions]]:
        cells=math.prod(math.ceil(float((b-a+2*cfg['margin_m'])/d)) for a,b,d in zip(low,high,spacing))
        if cells>2_000_000:raise ValueError('Resolución excede presupuesto de 2 millones de celdas')
        if spacing is cfg['spacing_m'] and cells*frames>30_000_000:
            raise ValueError('Historial demasiado grande: aumentar intervalo de guardado o paso espacial')
    return cfg
