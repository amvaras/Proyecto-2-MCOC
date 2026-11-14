"""Simulación de 336 h y criterios térmicos del curso para E12."""

import argparse
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from mcoc_p2.e07.coupling import MaskedAssembly
from mcoc_p2.e07.ifc import read_pours
from mcoc_p2.e07.voxel import voxelize
from mcoc_p2.e08.inputs import events_from_config, validate_config
from mcoc_p2.e08.solver import simulate
from mcoc_p2.e09.analysis import select_probes
from mcoc_p2.e10.boundaries import Air, Environment, Formwork, Layer, Soil
from mcoc_p2.e10.weather import Snapshot, iso_utc
from mcoc_p2.e11.pipeline import write_json

from hydration import read_curve
from weather_case import WeatherCase, load_forecast


ROOT = Path(__file__).resolve().parent
IFC = ROOT.parent / "P2_E11/geometry/foundation.ifc"


class ThermalRecord:
    """Reduce el campo a máximos y temperaturas a 25 mm en cada paso."""

    def __init__(self, voxels, events, environment, depth):
        if not 0 < depth <= min(voxels.grid.spacing) / 2:
            raise ValueError("La profundidad debe quedar entre la cara y el centro de la celda")
        self.voxels = voxels
        self.environment = environment
        self.materials = {event.pour_id: event.material for event in events}
        self.depth = depth
        self.probes = select_probes(voxels)
        self.core_index = tuple(self.probes[0]["index"])
        self.assembly = None
        self.rows = []
        self.peak = self.differential = None
        self.peak_field = self.differential_field = None
        self.origin = np.array(voxels.grid.origin)
        self.spacing = np.array(voxels.grid.spacing)

    def point(self, index):
        return {
            "xyz_m": (self.origin + (np.array(index) + .5) * self.spacing).tolist(),
            "pour_id": int(self.voxels.vertida_id[index]),
        }

    def __call__(self, t, temperature, active):
        if not active.any():
            return
        if self.assembly is None or not np.array_equal(active, self.assembly.active):
            self.assembly = MaskedAssembly(self.voxels, active, self.materials)
            faces = self.assembly.faces
            self.offset = self.spacing[faces.axis] / 2 - self.depth
            self.surface_resistance = self.offset / self.assembly.k[self.assembly.face_indices]
        a = self.assembly
        self.environment(a, t)
        centers = temperature[a.face_indices]
        outward = (a.face_g * (centers - a.reservoir) + a.prescribed) / a.faces.areas
        surface = centers - outward * self.surface_resistance
        cold = int(np.argmin(surface))
        hot = np.unravel_index(np.nanargmax(temperature), temperature.shape)
        maximum = float(temperature[hot])
        delta = maximum - float(surface[cold])
        if self.peak is None or maximum > self.peak["temperature_C"]:
            self.peak = {"temperature_C": maximum, "time_s": t, **self.point(hot)}
            self.peak_field = temperature.copy()
        if self.differential is None or delta > self.differential["difference_C"]:
            index = tuple(a.faces.indices[cold])
            point = self.point(index)
            point["xyz_m"] = (np.asarray(point["xyz_m"]) + self.offset[cold] * a.faces.normals[cold]).tolist()
            face = "xyz"[a.faces.axis[cold]] + ("+" if a.faces.sign[cold] > 0 else "-")
            self.differential = {
                "difference_C": delta, "time_s": t,
                "hot": {"temperature_C": maximum, **self.point(hot)},
                "cold": {"temperature_C": float(surface[cold]), "face": face,
                         "classification": str(a.faces.classification[cold]), **point},
            }
            self.differential_field = temperature.copy()
        top = self.probes[1]
        top_mask = np.all(a.faces.indices == top["index"], axis=1) & (a.faces.axis == 2) & (a.faces.sign == 1)
        top_values = surface[top_mask]
        sample = self.environment.weather.at(t)
        self.rows.append([t, maximum, surface[cold], delta, temperature[self.core_index],
                          top_values[0] if len(top_values) else np.nan, sample.air_C, sample.wind_m_s,
                          sample.ghi_W_m2])


def run(config, output):
    source = ROOT / "data/source_terms.txt"
    curve = read_curve(source, config["curve"])
    solids, ifc_metadata = read_pours(IFC)
    physics = validate_config({**config["physics"], "hydration": {"H_vol_J_m3": 0, "duration_s": 1}}, solids)
    events = [replace(event, hydration=curve) for event in events_from_config(physics)]
    if physics["t_end_s"] != 336 * 3600 or min(event.activation_s for event in events) != 0:
        raise ValueError("E12 requiere 336 h desde la primera vertida")
    weather = WeatherCase(
        load_forecast(ROOT / "data/weather/forecast"),
        Snapshot.load(ROOT / "data/weather/era5-2025"),
        config["start"], config["analog_start"], physics["t_end_s"],
    )
    voxels = voxelize(solids, physics["spacing_m"], margin=physics["margin_m"])
    mold = config["environment"]["formwork"]
    environment = Environment(
        voxels, weather, Air(**config["environment"]["air"]), Soil(**config["environment"]["soil"]),
        Formwork(tuple(mold["orientations"]), mold["remove_at_s"], tuple(Layer(**layer) for layer in mold["layers"])),
    )
    record = ThermalRecord(voxels, events, environment, config["sensor_depth_m"])
    result = simulate(
        voxels, events, t_end_s=physics["t_end_s"], max_step_s=physics["max_step_s"],
        save_interval_s=physics["save_interval_s"], safety=physics["safety"],
        energy_reference_C=physics["energy_reference_C"], observer=record,
        boundary_update=environment, boundary_change_times_s=environment.change_times_s,
    )
    rows = np.asarray(record.rows)
    if not np.array_equal(rows[:, 0], [0., *(step["end_s"] for step in result.steps)]):
        raise RuntimeError("Las métricas deben cubrir todos los pasos y la colocación inicial")
    peak, difference = record.peak, record.differential
    for metric in (peak, difference):
        metric["utc"] = iso_utc(weather.start + metric["time_s"])
        metric["hour"] = metric["time_s"] / 3600
    report = {
        "status": "PASS", "configuration": config, "weather": weather.report(), "ifc": ifc_metadata,
        "hydration": {"column": config["curve"], "source_sha256": sha256(source.read_bytes()).hexdigest(),
                      "end_age_h": curve.duration_s / 3600, "potential_MJ_m3": curve.H_vol_J_m3 / 1e6,
                      "extension": "zero after last valid record", "origin": "retained window mapped to placement"},
        "grid": voxels.report(), "peak": peak, "differential": difference, "probes": record.probes[:2],
        "temperature_pass": peak["temperature_C"] <= 70,
        "difference_pass": difference["difference_C"] <= 20,
        "energy": result.energy, "checks": result.checks, "steps": len(result.steps),
        "max_step_ratio": max(step["dt_over_limit"] for step in result.steps),
    }
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "summary.json", report)
    np.savetxt(output / "series.csv", rows, delimiter=",", comments="",
               header="time_s,Tmax_C,S25min_C,delta_C,core_C,top25_C,air_C,wind_m_s,ghi_W_m2", fmt="%.12g")
    np.savez_compressed(output / "fields.npz", vertida_id=voxels.vertida_id,
                        origin_m=record.origin, spacing_m=record.spacing, times_s=result.times_s,
                        temperature_C=result.temperature_C.astype("float32"),
                        peak=record.peak_field, differential=record.differential_field)
    print(json.dumps({k: report[k] for k in ("peak", "differential", "steps", "checks")}, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Indique una carpeta nueva")
    run(json.loads(args.config.read_text(encoding="utf-8")), args.output)


if __name__ == "__main__":
    main()
