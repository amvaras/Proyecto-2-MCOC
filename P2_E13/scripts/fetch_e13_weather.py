"""Adquisición separada del cálculo: ensemble GFS 0.5°, respuesta original intacta."""
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlencode
from urllib.request import urlopen
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def main():
    folder=ROOT/'data/ensemble';folder.mkdir(exist_ok=True)
    if (folder/'raw.json').exists():raise ValueError('Preservar snapshot; no descargar nuevamente')
    params=dict(latitude=-28.856102,longitude=-71.421831,models='gfs05',hourly='temperature_2m,wind_speed_10m,shortwave_radiation',
                temperature_unit='celsius',wind_speed_unit='ms',timeformat='unixtime',timezone='GMT',forecast_days=35)
    url='https://ensemble-api.open-meteo.com/v1/ensemble?'+urlencode(params)
    with urlopen(url,timeout=45) as response:raw=response.read()
    data=json.loads(raw);assert data['utc_offset_seconds']==0 and len(data['hourly']['time'])>=700
    keys=list(data['hourly']);meta=dict(source='Open-Meteo',kind='forecast ensemble',model_requested='gfs05',
       retrieved_at_utc=datetime.now(timezone.utc).isoformat(),request_url=url,raw_sha256=hashlib.sha256(raw).hexdigest(),
       latitude=params['latitude'],longitude=params['longitude'],grid_latitude=data['latitude'],grid_longitude=data['longitude'],
       provider_run_utc=data.get('run_time'),provider_model_version=data.get('model_version'),elevation_m=data.get('elevation'),
       documentation='https://open-meteo.com/en/docs/ensemble-api',license='https://open-meteo.com/en/licence',
       caveat='GFS 0.5° ~50 km, nativo 3 h o 6 h en horizonte largo; API interpola a 1 h. No es estación local ni ensemble calibrado al sitio.')
    (folder/'raw.json').write_bytes(raw);(folder/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(meta,ensure_ascii=False,indent=2));print('hours',len(data['hourly']['time']),'keys',keys[:8],len(keys))
if __name__=='__main__':main()
