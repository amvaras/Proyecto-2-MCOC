"""I/O atómico dentro de la entrega; nunca reemplazar un resultado desconocido."""
from pathlib import Path
import hashlib,json,os,time,uuid
import numpy as np
from ..e11.pipeline import ROOT
def inside(path):
    p=Path(path).absolute()
    if not p.is_relative_to(ROOT):raise ValueError('Ruta fuera de E14')
    for q in (p,*p.parents):
        if q==ROOT:break
        if q.is_symlink() or q.is_junction():raise ValueError('No seguir enlaces')
    if not p.resolve().is_relative_to(ROOT):raise ValueError('Ruta resuelta fuera de E14')
    return p
def native(value):
    if isinstance(value,np.generic):return value.item()
    raise TypeError(type(value).__name__)
def encoded(data):return (json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False,default=native)+'\n').encode('utf8')
def fingerprint(data):return hashlib.sha256(encoded(data)).hexdigest()
def read(p):return json.loads(inside(p).read_text(encoding='utf8'))
def write(path,data,*,replace=False):
    p=inside(path);p.parent.mkdir(parents=True,exist_ok=True);raw=encoded(data)
    if p.exists() and not replace:
        if p.read_bytes()!=raw:raise ValueError('Preservar resultado existente: '+str(p.relative_to(ROOT)))
        return p
    tmp=p.with_name(p.name+'.tmp-'+uuid.uuid4().hex)
    with tmp.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    if p.exists() and not replace:
        tmp.unlink();raise ValueError('Resultado creado concurrentemente; revalidar')
    # Windows/OneDrive puede mantener un lector abierto brevemente mientras
    # la interfaz consulta progreso. Reintentar el reemplazo atómico; nunca
    # truncar el destino ni ocultar un bloqueo persistente.
    try:
        for attempt in range(21):
            try:os.replace(tmp,p);return p
            except PermissionError:
                if attempt==20:raise
                time.sleep(.025*(1+min(attempt,3)))
    finally:
        if tmp.exists():tmp.unlink()
def source_hashes():
    names=['src/mcoc_p2/e08/solver.py','src/mcoc_p2/e07/coupling.py','src/mcoc_p2/e07/faces.py','src/mcoc_p2/e08/inputs.py','src/mcoc_p2/e10/boundaries.py','src/mcoc_p2/e10/weather.py','src/mcoc_p2/e11/pipeline.py','src/mcoc_p2/e11/weather.py','src/mcoc_p2/e12/metrics.py','src/mcoc_p2/e12/source.py','src/mcoc_p2/e13/evaluator.py','src/mcoc_p2/e13/plans.py','geometry/foundation.ifc','data/hydration/source_terms.txt','data/ensemble/raw.json','data/ensemble/reduction.json']
    return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}
