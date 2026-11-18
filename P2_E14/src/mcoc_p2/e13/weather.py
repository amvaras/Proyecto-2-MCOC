"""Tres historias completas: medoides de los 31 miembros auténticos GFS."""
from itertools import combinations
from pathlib import Path
import hashlib,json
import numpy as np
from ..e10.weather import Snapshot,VARIABLES,iso_utc,save_snapshot
from ..e11.weather import normalized_bytes
ROOT=Path(__file__).resolve().parents[3]
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def write(p,d):Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
def member_payload(raw,member):
    suffix='' if member==0 else f'_member{member:02d}'
    result={k:v for k,v in raw.items() if k not in ('hourly','hourly_units')}
    result['hourly']={'time':raw['hourly']['time']}
    result['hourly_units']={'time':raw['hourly_units']['time']}
    for name in VARIABLES:
        result['hourly'][name]=raw['hourly'][name+suffix];result['hourly_units'][name]=raw['hourly_units'][name+suffix]
    valid=np.all([np.isfinite(np.asarray(result['hourly'][n],float)) for n in VARIABLES],axis=0)
    count=int(valid.sum())
    if not valid[:count].all() or valid[count:].any():raise ValueError('Hueco interior en miembro ensemble')
    # El proveedor devuelve null al final del horizonte nominal. Recortar el
    # prefijo común válido; nunca convertirlo en cero ni extenderlo.
    for name in result['hourly']:result['hourly'][name]=result['hourly'][name][:count]
    return result
def reduce_members(series,k=3):
    a=np.asarray(series,float)
    if a.ndim!=2 or len(a)<k or not np.isfinite(a).all():raise ValueError('Historias completas finitas')
    if k!=3:raise ValueError('Reducción oficial: exactamente tres medoides')
    distance=np.mean((a[:,None,:]-a[None,:,:])**2,axis=2)
    medoids=min(combinations(range(len(a)),k),key=lambda ids:(float(distance[:,ids].min(axis=1).sum()),ids))
    assignment=np.argmin(distance[:,medoids],axis=1)
    # Medoides únicos; cada uno se representa a sí mismo incluso con empate.
    for j,m in enumerate(medoids):assignment[m]=j
    counts=np.bincount(assignment,minlength=k)
    return dict(medoids=list(medoids),assignment=assignment.tolist(),counts=counts.tolist(),weights=(counts/len(a)).tolist(),
                distortion_C2=float(distance[:,medoids].min(axis=1).mean()),max_RMS_C=float(np.sqrt(distance[:,medoids].min(axis=1)).max()))
def build_snapshots(start_utc='2026-11-19T11:00:00Z',duration_h=600):
    from ..e10.weather import utc_time
    folder=ROOT/'data/ensemble';raw=read(folder/'raw.json');meta=read(folder/'metadata.json')
    assert hashlib.sha256((folder/'raw.json').read_bytes()).hexdigest()==meta['raw_sha256']
    seconds=np.array(raw['hourly']['time']);start=utc_time(start_utc).timestamp();mask=(seconds>=start)&(seconds<=start+duration_h*3600)
    if seconds[0]>start or seconds[-1]<start+duration_h*3600:raise ValueError('Ensemble no cubre el horizonte de reducción')
    payloads=[member_payload(raw,i) for i in range(31)]
    seconds=np.array(payloads[0]['hourly']['time']);mask=(seconds>=start)&(seconds<=start+duration_h*3600)
    if any(p['hourly']['time']!=seconds.tolist() for p in payloads):raise ValueError('Coberturas ensemble diferentes')
    arrays=np.array([p['hourly']['temperature_2m'] for p in payloads],float)
    reduced=reduce_members(arrays[:,mask]);reduced.update(start_utc=start_utc,reduction_h=duration_h,method='Mínimo global de suma L2 de temperatura para 3 medoides de 31; historias completas, selección anterior a temperaturas del hormigón',
        weights_meaning='Conteos/31 de clusters de miembros inicialmente uniformes; aproximación discreta del ensemble, sin calibración local',raw_sha256=meta['raw_sha256'])
    snapshots=[]
    from datetime import datetime
    for member in reduced['medoids']:
        payload=member_payload(raw,member);b=(json.dumps(payload,separators=(',',':'),ensure_ascii=False)+'\n').encode()
        target=save_snapshot(ROOT/'data/weather',b,source='Open-Meteo',kind='forecast',model='gfs05',latitude=meta['latitude'],longitude=meta['longitude'],url=meta['request_url'],retrieved_at=datetime.fromisoformat(meta['retrieved_at_utc']))
        s=Snapshot.load(target);csv=normalized_bytes(s);(target/'temperature.csv').write_bytes(csv)
        m=s.metadata;m.update(e11_schema=1,e13_ensemble_member=member,ensemble_parent='data/ensemble/raw.json',ensemble_parent_sha256=meta['raw_sha256'],
            normalized_sha256=hashlib.sha256(csv).hexdigest(),interval_s=3600,provider_elevation_m=payload.get('elevation'),provider_model_version=meta['provider_model_version'],
            representativeness=meta['caveat'],license_url=meta['license'],derivation='Extracción exacta de las tres variables del mismo miembro; weather.json derivado, original completo en data/ensemble/raw.json')
        write(target/'metadata.json',m);snapshots.append(target.relative_to(ROOT).as_posix())
    reduced['snapshots']=snapshots;write(folder/'reduction.json',reduced);return reduced
def validate_snapshot(folder):
    folder=Path(folder);snap=Snapshot.load(folder);m=snap.metadata
    if m.get('ensemble_parent')!='data/ensemble/raw.json':raise ValueError('Origen ensemble local reconocido')
    parent=ROOT/m['ensemble_parent'];raw=parent.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=m['ensemble_parent_sha256']:raise ValueError('SHA ensemble incorrecto')
    meta=read(parent.parent/'metadata.json')
    if m['request_url']!=meta['request_url'] or m['retrieved_at_utc']!=meta['retrieved_at_utc']:raise ValueError('Trazabilidad inconsistente')
    member=m['e13_ensemble_member']
    if type(member)is not int or not 0<=member<31:raise ValueError('Miembro desconocido')
    if read(folder/'weather.json')!=member_payload(json.loads(raw),member):raise ValueError('Miembro derivado no coincide con original')
    csv=(folder/'temperature.csv').read_bytes()
    if csv!=normalized_bytes(snap) or hashlib.sha256(csv).hexdigest()!=m['normalized_sha256']:raise ValueError('CSV incorrecto')
    return snap
