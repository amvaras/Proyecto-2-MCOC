"""Un resultado por input físico; E13 se referencia localmente sin duplicar sus filas."""
from pathlib import Path
from contextlib import contextmanager
import os,socket,time,uuid
import numpy as np
from ..e11.pipeline import ROOT
from .io import read,write,fingerprint,inside,encoded
from .model import Model
from .statistics import limit_states
def validate_record(row):
    for k in ('Tmax_C','delta_C','horizon_h','D_h'):
        if not isinstance(row[k],(int,float)) or not np.isfinite(row[k]):raise ValueError('Métrica no finita: '+k)
    if not all(row['checks'].values()) or row['coverage']['tail_hours']!=0:raise ValueError('Resultado térmico sin verificaciones/cobertura')
    e=row['energy']
    if abs(e['residual_J'])>e['tolerance_J']:raise ValueError('Balance fuera de tolerancia')
    if abs(row['delta_C']-(row['delta_peak']['hot_temperature_C']-row['delta_peak']['cold']['temperature_C']))>1e-10:raise ValueError('Diferencial inconsistente')
    return row
@contextmanager
def claim(path,timeout_s=180):
    p=inside(path);p.parent.mkdir(parents=True,exist_ok=True);token=dict(pid=os.getpid(),host=socket.gethostname(),token=uuid.uuid4().hex);raw=encoded(token);start=time.monotonic()
    while True:
        try:
            with p.open('xb') as f:f.write(raw)
            break
        except FileExistsError:
            if time.monotonic()-start>timeout_s:raise TimeoutError('Lock conservado; comprobar job/PID antes de recuperación: '+p.name)
            time.sleep(.05)
    try:yield
    finally:
        if p.is_file() and p.read_bytes()==raw:p.unlink()
def prepare_reuse(root=None):
    folder=inside(root or ROOT/'results/e14/cache');folder.mkdir(parents=True,exist_ok=True);model=Model();entries={};duplicate=0
    paths=[('results/e13/cases.json',None),('results/verification/controls.json','cases')]
    for name,part in paths:
        payload=read(ROOT/name);rows=payload[part] if part else payload
        for i,r in enumerate(rows):
            validate_record(r);key=model.key(r['configuration'],r.get('area_sensitivity'))
            if key in entries:
                old=entries[key];old_payload=read(ROOT/old['file']);a=(old_payload[old['part']] if old['part'] else old_payload)[old['index']]
                if a['Tmax_C']!=r['Tmax_C'] or a['delta_C']!=r['delta_C']:raise ValueError('Inputs duplicados con métricas distintas')
                duplicate+=1;continue
            entries[key]=dict(file=name,part=part,index=i,row_sha256=fingerprint(r))
    data=dict(schema=1,kernel=model.hashes,entries=entries,duplicate_inputs=duplicate,meaning='Resultados vigentes E13 copiados selectivamente a E14; índice local, no duplicación por realización')
    index=folder/'reused.json'
    if index.exists():
        old=read(index)
        if old.get('schema')!=1 or any(e.get('file') not in {'results/e13/cases.json','results/verification/controls.json'} for e in old.get('entries',{}).values()):raise ValueError('Índice desconocido: conservar')
    write(index,data,replace=index.exists());return data
class Store:
    def __init__(self,root=None):
        self.root=inside(root or ROOT/'results/e14/cache');self.root.mkdir(parents=True,exist_ok=True);self.index=read(self.root/'reused.json') if (self.root/'reused.json').exists() else dict(entries={});self.loaded={}
    def get(self,key):
        if not isinstance(key,str) or len(key)!=64 or any(c not in '0123456789abcdef' for c in key):raise ValueError('Clave SHA256')
        p=self.root/(key+'.json')
        if p.exists():
            entry=read(p)
            if entry['physics_key']!=key or entry['row_sha256']!=fingerprint(entry['row']):raise ValueError('Resultado cache alterado')
            return validate_record(entry['row'])
        if key in self.index['entries']:
            e=self.index['entries'][key]
            if e['file'] not in self.loaded:self.loaded[e['file']]=read(ROOT/e['file'])
            rows=self.loaded[e['file']];row=(rows[e['part']] if e['part'] else rows)[e['index']]
            if fingerprint(row)!=e['row_sha256']:raise ValueError('Fila reutilizada cambió')
            return validate_record(row)
        return None
    def evaluate(self,model,item,scenario,*,spacing=(.45,.45,.11),step_s=900,area_factors=None,force=False):
        cfg,_=model.configuration(item,scenario,spacing,step_s);key=model.key(cfg,area_factors);row=None if force else self.get(key);hit=row is not None
        if row is None:
            with claim(self.root/(key+'.lock')):
                row=None if force else self.get(key)
                if row is None:
                    row,_,_,_=model.evaluate(item,scenario,spacing=spacing,step_s=step_s,area_factors=area_factors);validate_record(row)
                    if not force:write(self.root/(key+'.json'),dict(physics_key=key,row=row,row_sha256=fingerprint(row)))
                else:hit=True
        # D y pesos corresponden al plan/distribución actual; la temperatura
        # reutilizada depende solo de los inputs físicos de la clave.
        row={**row,'plan':item['id'],'scenario':scenario['id'],'D_h':item['construction']['D_h'],'weight':scenario['weight'],
             'material_weight':scenario['material_weight'],'climate_weight':scenario['climate_weight'],'physics_key':key,'cache_hit':hit,'design':item['design'],'construction':item['construction']}
        g=limit_states(row['Tmax_C'],row['delta_C']);row.update(g_T=float(g['g_T']),g_Delta=float(g['g_Delta']),fail_joint=bool(g['fail_joint']))
        return row
