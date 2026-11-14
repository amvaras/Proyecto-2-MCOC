"""Pronóstico archivado y continuación explícita con un análogo ERA5."""

from hashlib import sha256
import json
from math import isfinite

from mcoc_p2.e10.weather import Snapshot, VARIABLES, iso_utc, parse_hourly, utc_time


def load_forecast(folder):
    raw = (folder / "weather.json").read_bytes()
    metadata = json.loads((folder / "request.json").read_text(encoding="utf-8"))
    if sha256(raw).hexdigest() != metadata["raw_sha256"]:
        raise ValueError("El pronóstico original cambió")
    payload = json.loads(raw)
    hourly = payload["hourly"]
    count = len(hourly["time"])
    if any(len(hourly[key]) != count for key in VARIABLES):
        raise ValueError("Longitud de pronóstico incorrecta")
    valid = [
        all(type(hourly[key][i]) in (int, float) and isfinite(hourly[key][i]) for key in VARIABLES)
        for i in range(count)
    ]
    end = valid.index(False) if False in valid else count
    if end < 2 or any(valid[end:]):
        raise ValueError("Se requiere un prefijo horario completo sin huecos")
    payload["hourly"] = {key: hourly[key][:end] for key in ("time", *VARIABLES)}
    payload, seconds, values = parse_hourly(json.dumps(payload))
    metadata.update(grid_latitude=payload["latitude"], grid_longitude=payload["longitude"],
                    valid_from_utc=iso_utc(seconds[0]), valid_until_utc=iso_utc(seconds[-1]),
                    incomplete_trailing_rows=count - end, units=VARIABLES)
    return Snapshot(metadata, seconds, *values)


class WeatherCase:
    def __init__(self, forecast, analog, start, analog_start, duration_s):
        self.forecast = forecast
        self.analog = analog
        self.start = utc_time(start).timestamp()
        self.analog_start = utc_time(analog_start).timestamp()
        self.duration_s = duration_s
        if self.start < forecast.seconds[0]:
            raise ValueError("El forecast debe empezar antes de la primera vertida")
        self.covered_s = max(0., min(duration_s, forecast.seconds[-1] - self.start))
        if self.covered_s < duration_s and not (
            analog.seconds[0] <= self.analog_start + self.covered_s
            and self.analog_start + duration_s <= analog.seconds[-1]
        ):
            raise ValueError("ERA5 no cubre el tramo faltante")
        changes = {t - self.start for t in forecast.seconds if 0 < t - self.start <= self.covered_s}
        changes.update(t - self.analog_start for t in analog.seconds
                       if self.covered_s < t - self.analog_start < duration_s)
        self.change_times_s = tuple(sorted(changes))

    def at(self, time_s):
        if not 0 <= time_s <= self.duration_s:
            raise ValueError("Instante fuera de la simulación")
        if time_s < self.covered_s or (self.covered_s == self.duration_s and time_s == self.covered_s):
            return self.forecast.sample(self.start + time_s)
        return self.analog.sample(self.analog_start + time_s)

    def report(self):
        return {
            "start_utc": iso_utc(self.start), "end_utc": iso_utc(self.start + self.duration_s),
            "forecast": self.forecast.metadata, "reanalysis": self.analog.metadata,
            "forecast_hours": self.covered_s / 3600,
            "analog_hours": (self.duration_s - self.covered_s) / 3600,
            "transition_utc": iso_utc(self.start + self.covered_s),
            "analog_data_from_utc": iso_utc(self.analog_start + self.covered_s),
            "analog_data_until_utc": iso_utc(self.analog_start + self.duration_s),
        }
