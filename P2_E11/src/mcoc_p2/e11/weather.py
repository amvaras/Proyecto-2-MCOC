"""Adquisición explícita y normalización verificable; la simulación nunca descarga."""
import csv,hashlib,io,json
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlparse,parse_qs
from zoneinfo import ZoneInfo
from ..e10.weather import Snapshot,WeatherWindow,fetch_forecast,iso_utc

ROOT=Path(__file__).resolve().parents[3]


def normalized_bytes(snapshot):
    stream=io.StringIO(newline='')
    writer=csv.writer(stream,lineterminator='\n')
    writer.writerow(['time_utc','time_America_Santiago','temperature_C'])
    for t,value in zip(snapshot.seconds,snapshot.air):
        local=datetime.fromtimestamp(t,timezone.utc).astimezone(ZoneInfo('America/Santiago'))
        writer.writerow([iso_utc(t),local.isoformat(),format(value,'.17g')])
    return stream.getvalue().encode('utf-8')


def acquire(root=ROOT/'data/weather',days=3):
    root=Path(root).resolve()
    if not root.is_relative_to(ROOT):raise ValueError('Snapshot dentro de E11')
    folder=fetch_forecast(root,-28.856102,-71.421831,days=days)
    snapshot=Snapshot.load(folder);raw=json.loads((folder/'weather.json').read_bytes())
    csv_bytes=normalized_bytes(snapshot);(folder/'temperature.csv').write_bytes(csv_bytes)
    meta=snapshot.metadata
    meta.update(e11_schema=1,endpoint='https://api.open-meteo.com/v1/forecast',
        query_parameters=parse_qs(urlparse(meta['request_url']).query),
        normalized_sha256=hashlib.sha256(csv_bytes).hexdigest(),
        interval_s=3600,provider_elevation_m=raw.get('elevation'),
        provider_timezone=raw.get('timezone'),provider_model_version=raw.get('model_version'),
        interpolation='linear; reject outside interval; no extrapolation or scenario tail',
        license_url='https://open-meteo.com/en/licence',
        representativeness='Forecast de grilla, no medición de estación ni punto exacto de construcción. Elevación reportada por proveedor, no levantamiento de obra.',
        unused_variables='Viento y GHI se preservan en respuesta original; no entran en el baseline E11.')
    (folder/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    validate(folder)
    return folder


def validate(folder):
    folder=Path(folder);snap=Snapshot.load(folder);meta=snap.metadata
    payload=json.loads((folder/'weather.json').read_bytes())
    if payload['hourly_units'].get('time')!='unixtime':raise ValueError('Unidad temporal debe ser unixtime')
    expected=normalized_bytes(snap);actual=(folder/'temperature.csv').read_bytes()
    required={'retrieved_at_utc','source','kind','request_url','latitude','longitude','grid_latitude','grid_longitude','valid_from_utc','valid_until_utc','normalized_sha256','interval_s','provider_elevation_m','provider_model_version','representativeness','license_url'}
    if not required<=meta.keys() or meta.get('e11_schema')!=1 or meta['interval_s']!=3600:raise ValueError('Metadata E11 incompleta')
    if meta['kind']!='forecast' or meta['source']!='Open-Meteo':raise ValueError('Snapshot oficial debe ser forecast Open-Meteo auténtico')
    if urlparse(meta['request_url']).hostname!='api.open-meteo.com':raise ValueError('Origen del snapshot inesperado')
    if actual!=expected or hashlib.sha256(actual).hexdigest()!=meta['normalized_sha256']:raise ValueError('CSV normalizado no corresponde al original o SHA incorrecto')
    return snap


def window(folder,start_utc,duration_s):
    return WeatherWindow(validate(folder),start_utc,duration_s,tail=None)
