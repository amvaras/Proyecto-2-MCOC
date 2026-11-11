"""Ejecuta la demo oral E10, audita la cobertura o archiva un forecast."""

import argparse
import json
from hashlib import sha256
from pathlib import Path

from mcoc_p2.e07.ifc import read_pours
from mcoc_p2.e07.voxel import voxelize
from mcoc_p2.e08.inputs import events_from_config, validate_config
from mcoc_p2.e08.solver import simulate
from mcoc_p2.e10.boundaries import Air, Environment, Formwork, Layer, Soil
from mcoc_p2.e10.weather import Snapshot, WeatherSample, WeatherWindow, fetch_forecast


HERE = Path(__file__).resolve().parent
E09 = HERE.parent / "P2_E09"
WEATHER = HERE / "data" / "weather"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def run_demo(window, config):
    ifc = E09 / "geometry" / "foundation.ifc"
    solids, ifc_metadata = read_pours(ifc)
    baseline = E09 / "configs" / "e09" / "baseline.json"
    physics = read_json(baseline)["physics"]
    physics["t_end_s"] = window.duration_s
    physics = validate_config(physics, solids)
    voxels = voxelize(solids, physics["spacing_m"], margin=physics["margin_m"])
    air = Air(**config["air"])
    soil = Soil(**config["soil"])
    mold = config["formwork"]
    formwork = Formwork(tuple(mold["orientations"]), mold["remove_at_s"],
                        tuple(Layer(**layer) for layer in mold["layers"]))
    environment = Environment(voxels, window, air, soil, formwork)
    result = simulate(
        voxels, events_from_config(physics), t_end_s=window.duration_s,
        max_step_s=physics["max_step_s"], save_interval_s=physics["save_interval_s"],
        safety=physics["safety"], energy_reference_C=physics["energy_reference_C"],
        boundary_update=environment, boundary_change_times_s=environment.change_times_s,
    )
    ends = {row["end_s"] for row in result.steps}
    boundaries_exact = all(t in ends for t in environment.change_times_s if 0 < t <= window.duration_s)
    if not boundaries_exact:
        raise RuntimeError("Un cambio de borde quedó dentro de un paso")
    # Elegir la mayor temperatura entre fotogramas activos, incluida la primera colocación.
    hottest = max((row for row in result.metrics if row["max_C"] is not None), key=lambda row: row["max_C"])
    samples = []
    times = {0., window.duration_s, window.covered_s}
    if 1 <= formwork.remove_at_s <= window.duration_s:
        times.update({formwork.remove_at_s - 1, formwork.remove_at_s})
    for time_s in sorted(times):
        weather = window.at(time_s)
        h = air.h(weather.wind_m_s)
        layer_r = formwork.resistance if time_s < formwork.remove_at_s else 0.0
        # Ley equivalente para una cara lateral en hormigón a 30 °C.
        resistance = physics["spacing_m"][0] / (2 * physics["material"]["k"]) + layer_r
        samples.append({
            "hour": time_s / 3600, **vars(weather), "h_W_m2K": h,
            "formwork_R_m2K_W": layer_r,
            "lateral_outward_at_30C_W_m2": h * (30 - weather.air_C) / (1 + h * resistance),
        })
    return {
        "status": "PASS", "ifc": ifc_metadata, "physics_config_sha256": sha256(baseline.read_bytes()).hexdigest(),
        "boundary_parameters": {key: config[key] for key in ("air", "soil", "formwork")},
        "weather": window.snapshot.metadata, "coverage": window.coverage(),
        "grid": voxels.report(), "activation_hours": [row["time_s"] / 3600 for row in result.events],
        "boundary_samples": samples, "exact_boundary_changes": boundaries_exact, "steps": len(result.steps),
        "max_dt_over_limit": max((row["dt_over_limit"] for row in result.steps), default=0),
        "maximum_saved_C": hottest["max_C"], "maximum_saved_hour": hottest["time_s"] / 3600,
        "energy": result.energy, "checks": result.checks,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch", help="Guardar una nueva descarga de Open-Meteo")
    fetch.add_argument("--days", type=int, default=16)
    fetch.add_argument("--model", default="auto")
    fetch.add_argument("--output-dir", type=Path, default=WEATHER)
    for name in ("coverage", "demo"):
        command = commands.add_parser(name)
        command.add_argument("--snapshot", type=Path, default=WEATHER / "ejemplo-docente")
        command.add_argument("--config", type=Path, default=HERE / "ambiente.json")
        command.add_argument("--start", help="ISO 8601 con offset")
        command.add_argument("--hours", type=float)
        command.add_argument("--strict", action="store_true", help="Exigir cobertura completa del snapshot")
        command.add_argument("--output", type=Path, help="Guardar un JSON en un archivo nuevo")
    args = parser.parse_args()
    if args.command == "fetch":
        path = fetch_forecast(args.output_dir, -28.856102, -71.421831, days=args.days, model=args.model)
        print(path.resolve())
        print(json.dumps(Snapshot.load(path).metadata, ensure_ascii=False, indent=2))
        return
    config = read_json(args.config)
    tail = None if args.strict else WeatherSample(**config["tail"], source_kind="scenario_tail")
    duration = (config["demo_hours"] if args.hours is None else args.hours) * 3600
    if duration <= 0:
        parser.error("--hours debe ser positivo")
    window = WeatherWindow(Snapshot.load(args.snapshot), args.start or config["start"], duration, tail)
    report = (run_demo(window, config) if args.command == "demo"
              else {"weather": window.snapshot.metadata, "coverage": window.coverage()})
    text = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
    print(text, end="")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        raise SystemExit(f"Error: {exc}") from exc
