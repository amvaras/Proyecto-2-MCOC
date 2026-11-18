"""Snapshots horarios de Open-Meteo y cobertura explícita de la simulación."""

from bisect import bisect_right
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen


VARIABLES = {
    "temperature_2m": "°C",
    "wind_speed_10m": "m/s",
    "shortwave_radiation": "W/m²",
}
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def utc_time(value):
    """Parse an ISO timestamp with an explicit offset."""
    result = datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError("Indique el offset UTC del instante")
    return result.astimezone(timezone.utc)


def iso_utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat().replace("+00:00", "Z")


def finite_number(value, name, minimum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError(f"{name} debe ser un número finito")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} debe ser mayor o igual a {minimum}")
    return float(value)


@dataclass(frozen=True)
class WeatherSample:
    air_C: float
    wind_m_s: float
    ghi_W_m2: float
    source_kind: str

    def __post_init__(self):
        finite_number(self.air_C, "Temperatura del aire", -273.15)
        finite_number(self.wind_m_s, "Viento", 0)
        finite_number(self.ghi_W_m2, "GHI", 0)


def parse_hourly(raw):
    payload = json.loads(raw)
    try:
        if payload["utc_offset_seconds"] != 0:
            raise ValueError("Se requieren timestamps en UTC")
        hourly = payload["hourly"]
        seconds = tuple(hourly["time"])
        if (len(seconds) < 2 or any(type(t) is not int or t % 3600 for t in seconds)
                or any(b - a != 3600 for a, b in zip(seconds, seconds[1:]))):
            raise ValueError("Se requieren horas UTC consecutivas sin huecos")
        values = []
        for key, unit in VARIABLES.items():
            if payload["hourly_units"][key] != unit or len(hourly[key]) != len(seconds):
                raise ValueError(f"Unidad o longitud incorrecta en {key}")
            minimum = -273.15 if key == "temperature_2m" else 0
            values.append(tuple(finite_number(item, key, minimum) for item in hourly[key]))
    except (KeyError, TypeError) as exc:
        raise ValueError("Formato meteorológico horario incompleto") from exc
    return payload, seconds, values


@dataclass(frozen=True)
class Snapshot:
    metadata: dict
    seconds: tuple
    air: tuple
    wind: tuple
    ghi: tuple

    @classmethod
    def load(cls, folder):
        folder = Path(folder)
        metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
        raw = (folder / "weather.json").read_bytes()
        if metadata.get("schema_version") != 1 or metadata.get("raw_sha256") != sha256(raw).hexdigest():
            raise ValueError("Esquema o SHA-256 del snapshot incorrecto")
        payload, seconds, values = parse_hourly(raw)
        if (metadata.get("timezone") != "UTC" or metadata.get("units") != VARIABLES
                or set(metadata.get("variables", [])) != set(VARIABLES)
                or metadata.get("valid_from_utc") != iso_utc(seconds[0])
                or metadata.get("valid_until_utc") != iso_utc(seconds[-1])
                or any(metadata.get(f"grid_{key}") != payload.get(key) for key in ("latitude", "longitude"))):
            raise ValueError("Metadatos incompatibles con el snapshot")
        if metadata.get("kind") not in {"forecast", "reanalysis", "observation", "synthetic"}:
            raise ValueError("Tipo de serie meteorológica desconocido")
        utc_time(metadata["retrieved_at_utc"])
        return cls(metadata, seconds, *values)

    def sample(self, seconds):
        if not self.seconds[0] <= seconds <= self.seconds[-1]:
            raise ValueError("Instante fuera de la cobertura meteorológica")
        # T y viento son instantáneos; GHI es el promedio de la hora anterior.
        right = min(bisect_right(self.seconds, seconds), len(self.seconds) - 1)
        left = right - 1
        fraction = (seconds - self.seconds[left]) / 3600
        air = self.air[left] + fraction * (self.air[right] - self.air[left])
        wind = self.wind[left] + fraction * (self.wind[right] - self.wind[left])
        return WeatherSample(air, wind, self.ghi[right], self.metadata["kind"])


def save_snapshot(root, raw, *, source, kind, model, latitude, longitude, url=None, retrieved_at=None):
    payload, seconds, _ = parse_hourly(raw)
    retrieved = retrieved_at or datetime.now(timezone.utc)
    if retrieved.utcoffset() is None:
        raise ValueError("La hora de descarga debe incluir zona horaria")
    retrieved = retrieved.astimezone(timezone.utc)
    digest = sha256(raw).hexdigest()
    metadata = {
        "schema_version": 1, "kind": kind, "source": source, "model_requested": model,
        "provider_run_utc": None, "retrieved_at_utc": retrieved.isoformat(),
        "latitude": latitude, "longitude": longitude, "grid_latitude": payload.get("latitude"),
        "grid_longitude": payload.get("longitude"), "timezone": "UTC", "site_timezone": "America/Santiago",
        "variables": list(VARIABLES), "units": VARIABLES, "request_url": url,
        "valid_from_utc": iso_utc(seconds[0]), "valid_until_utc": iso_utc(seconds[-1]),
        "raw_sha256": digest,
    }
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    target = root / f"{kind}-{retrieved:%Y%m%dT%H%M%S%fZ}-{digest[:12]}"
    if target.exists():
        raise FileExistsError(target)
    with TemporaryDirectory(dir=root, prefix=".snapshot-") as tmp:
        staged = Path(tmp) / "snapshot"
        staged.mkdir()
        (staged / "weather.json").write_bytes(raw)
        (staged / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        Snapshot.load(staged)
        staged.rename(target)
    return target


def fetch_forecast(root, latitude, longitude, *, days=16, model="auto"):
    if type(days) is not int or not 1 <= days <= 16:
        raise ValueError("forecast_days debe estar entre 1 y 16")
    latitude = finite_number(latitude, "Latitud")
    longitude = finite_number(longitude, "Longitud")
    if abs(latitude) > 90 or abs(longitude) > 180:
        raise ValueError("Coordenadas fuera de rango")
    parameters = {
        "latitude": latitude, "longitude": longitude, "hourly": ",".join(VARIABLES),
        "temperature_unit": "celsius", "wind_speed_unit": "ms", "timezone": "GMT",
        "timeformat": "unixtime", "forecast_days": days,
    }
    if model != "auto":
        parameters["models"] = model
    url = FORECAST_URL + "?" + urlencode(parameters)
    try:
        with urlopen(url, timeout=20) as response:
            raw = response.read()
    except HTTPError as exc:
        detail = exc.read(4096).decode("utf-8", errors="replace")
        raise ValueError(f"Open-Meteo devolvió HTTP {exc.code}: {detail}") from exc
    return save_snapshot(root, raw, source="Open-Meteo", kind="forecast", model=model,
                         latitude=latitude, longitude=longitude, url=url)


class WeatherWindow:
    """Bind one snapshot to a start time and an explicit optional tail."""

    def __init__(self, snapshot, start_iso, duration_s, tail=None):
        self.snapshot = snapshot
        self.start = utc_time(start_iso).timestamp()
        self.duration_s = finite_number(duration_s, "Duración", 0)
        self.tail = tail
        if self.start < snapshot.seconds[0]:
            raise ValueError("El inicio es anterior al snapshot. Seleccione una serie que cubra el inicio.")
        end_of_data_s = snapshot.seconds[-1] - self.start
        self.covered_s = min(self.duration_s, max(0., end_of_data_s))
        if self.covered_s < self.duration_s and tail is None:
            raise ValueError(f"Faltan {(self.duration_s - self.covered_s) / 3600:g} h. Configure una cola explícita.")
        self.change_times_s = tuple(
            t - self.start for t in snapshot.seconds if self.start < t < self.start + self.duration_s
        )

    def at(self, time_s):
        if not 0 <= time_s <= self.duration_s:
            raise ValueError("Tiempo fuera de la ventana simulada")
        absolute = self.start + time_s
        if absolute < self.snapshot.seconds[-1] or (absolute == self.snapshot.seconds[-1] and self.tail is None):
            return self.snapshot.sample(absolute)
        if self.tail is None:
            raise ValueError("Instante fuera del snapshot")
        return self.tail

    def coverage(self):
        return {
            "start_utc": iso_utc(self.start), "end_utc": iso_utc(self.start + self.duration_s),
            "covered_hours": self.covered_s / 3600,
            "tail_hours": (self.duration_s - self.covered_s) / 3600,
            "tail_from_utc": iso_utc(self.start + self.covered_s) if self.covered_s < self.duration_s else None,
            "tail_assumptions": vars(self.tail) if self.tail is not None and self.covered_s < self.duration_s else None,
        }
