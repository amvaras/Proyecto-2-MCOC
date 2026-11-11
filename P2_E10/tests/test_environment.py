"""Verificación de la física por cara y del archivo meteorológico E10."""

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import numpy as np
import pytest

from mcoc_p2 import Material
from mcoc_p2.e07.construction import PourEvent
from mcoc_p2.e07.coupling import MaskedAssembly
from mcoc_p2.e07.hydration import AdiabaticCurve
from mcoc_p2.e07.voxel import VoxelGrid, Voxelization
from mcoc_p2.e08.solver import simulate
from mcoc_p2.e10 import weather
from mcoc_p2.e10.boundaries import Air, Environment, Formwork, Layer, Soil
from mcoc_p2.e10.weather import Snapshot, WeatherSample, WeatherWindow


FIXTURE = Path(__file__).resolve().parents[1] / "data/weather/ejemplo-docente"


def test_weather_window_aligns_solar_hours_and_marks_the_missing_tail():
    snapshot = Snapshot.load(FIXTURE)
    start = "2026-11-27T08:00:00-03:00"
    tail = WeatherSample(19., 3., 0., "scenario_tail")
    window = WeatherWindow(snapshot, start, 336 * 3600, tail)
    assert window.start == snapshot.seconds[0]
    assert window.at(1800).air_C == pytest.approx((snapshot.air[0] + snapshot.air[1]) / 2)
    assert window.at(3599).ghi_W_m2 == snapshot.ghi[1]
    assert window.at(3600).ghi_W_m2 == snapshot.ghi[2]
    assert window.at(24 * 3600) == tail
    assert window.coverage()["covered_hours"] == 24
    assert window.coverage()["tail_hours"] == 312
    with pytest.raises(ValueError, match="312 h"):
        WeatherWindow(snapshot, start, 336 * 3600)
    with pytest.raises(ValueError, match="anterior"):
        WeatherWindow(snapshot, "2026-11-27T07:00:00-03:00", 3600, tail)
    assert WeatherWindow(snapshot, "2026-11-29T08:00:00-03:00", 3600, tail).coverage()["tail_hours"] == 1


def test_forecast_client_archives_original_bytes_and_validates_digest(monkeypatch, tmp_path):
    from io import BytesIO

    raw = (FIXTURE / "weather.json").read_bytes()
    requests = []

    def request(url, timeout):
        requests.append(parse_qs(urlparse(url).query))
        return BytesIO(raw)

    monkeypatch.setattr(weather, "urlopen", request)
    first = weather.fetch_forecast(tmp_path, -28.856102, -71.421831, days=16, model="auto")
    second = weather.save_snapshot(
        tmp_path, raw, source="Open-Meteo", kind="forecast", model="auto",
        latitude=-28.856102, longitude=-71.421831,
        retrieved_at=datetime(2026, 11, 11, 12, tzinfo=timezone.utc),
    )
    assert first != second and (first / "weather.json").read_bytes() == raw
    assert requests[0]["timeformat"] == ["unixtime"]
    assert requests[0]["wind_speed_unit"] == ["ms"]
    assert Snapshot.load(first).metadata["kind"] == "forecast"
    (second / "weather.json").write_bytes(raw + b" ")
    with pytest.raises(ValueError, match="SHA-256"):
        Snapshot.load(second)


def test_air_solar_and_ground_match_independent_face_balances():
    class Conditions:
        change_times_s = ()

        def at(self, time_s):
            return WeatherSample(20, 3, 600, "synthetic")

    grid = VoxelGrid((0., 0., 0.), (1., 1., 1.), (1, 1, 1))
    voxels = Voxelization(grid, np.ones(grid.shape, dtype=np.uint16), {1: "test"}, {1: 1.})
    material = Material(2., 2400., 900.)
    assembly = MaskedAssembly(voxels, voxels.occupation_mask, {1: material})
    mold = Formwork(("x+",), 70., (Layer("tablero", .03, .15),))
    environment = Environment(voxels, Conditions(), Air(5, 4, .5), Soil(15, .3, 1., .05), mold)
    h = 17.
    top = (assembly.faces.axis == 2) & (assembly.faces.sign == 1)
    bottom = (assembly.faces.axis == 2) & (assembly.faces.sign == -1)
    right = (assembly.faces.axis == 0) & (assembly.faces.sign == 1)
    temperature = np.full(voxels.grid.shape, 30.)
    environment(assembly, 69.)
    flux = assembly.face_g * (30. - assembly.reservoir) + assembly.prescribed
    # Exterior surface temperature from a separate steady node balance.
    surface = (30. / .25 + h * 20. + 300.) / (1 / .25 + h)
    assert flux[top][0] == pytest.approx((30. - surface) / .25)
    assert flux[bottom][0] == pytest.approx(15. / (.25 + .3 + .05))
    assert flux[right][0] == pytest.approx(10. / (.25 + .2 + 1 / h))
    assert assembly.power(temperature)[1] == pytest.approx(flux.sum())
    old_limit = assembly.stable_dt
    environment(assembly, 70.)
    assert assembly.face_g[right][0] == pytest.approx(1 / (.25 + 1 / h))
    assert assembly.stable_dt < old_limit

    event = PourEvent(1, 0, 30, material, AdiabaticCurve(0, 1))
    result = simulate(voxels, [event], t_end_s=150, save_interval_s=150,
                      max_step_s=100, boundary_update=environment,
                      boundary_change_times_s=environment.change_times_s)
    assert [step["end_s"] for step in result.steps] == [70, 150]
    assert all(result.checks.values())
