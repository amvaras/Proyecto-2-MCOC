"""Regenera figuras de resultados desde la exportación F02 fijada en el anexo."""
import argparse
import csv
import json
from math import fsum
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument("e14", type=Path)
args = parser.parse_args()
root = args.e14
out = Path(__file__).resolve().parent / "figuras"
out.mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.bbox": "tight"})

with (root / "results/f02/planes.csv").open() as stream:
    plans = list(csv.DictReader(stream))
d = np.array([float(row["D_h"]) for row in plans])
p = 100 * np.array([float(row["P_joint"]) for row in plans])
fig, ax = plt.subplots(figsize=(7.2, 3.15))
ax.scatter(d[:-1], p[:-1], c="#a84328")
ax.scatter(d[-1], p[-1], c="#15687c", label="moderate_20")
ax.axhline(5, ls="--", color=".32", label="Umbral docente 5 %")
ax.set(xlabel="Duración de colocación (h)", ylabel="Probabilidad conjunta (%)",
       ylim=(-7, 109))
ax.legend(loc="center right")
fig.savefig(out / "riesgo.pdf")

with np.load(root / "results/f02/fields.npz") as data:
    h = data["stats_time_s"] / 3600
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 4.0), sharex=True)
    axes[0].plot(h, data["stats_Tmax_C"], label="Máximo activo", color="#b4472a")
    axes[0].plot(h, data["stats_S25_C"], label="Mínimo S25", color="#15687c")
    axes[0].axhline(70, ls="--", color=".4", label="70 °C")
    axes[1].plot(h, data["stats_delta_C"], color="#333b74")
    axes[1].axhline(20, ls="--", color=".4", label="20 °C")
    for ax in axes:
        for event in [18, 360, 528, 552, 672]:
            ax.axvline(event, lw=.5, color=".72")
        ax.legend(loc="upper right", ncol=3)
    axes[0].set_ylabel("Temperatura (°C)")
    axes[1].set(xlabel="Tiempo desde el inicio (h)", ylabel="Diferencial (°C)")
    fig.tight_layout()
    fig.savefig(out / "historia.pdf")
    xyz, ijk = data["centers_m"], data["indices"]
    it = np.argmin(abs(data["times_s"] / 3600 - 214.25))
    values = data["temperature_C"][it]
    dx, dy, dz = data["spacing_m"]
    iy = ijk[np.argmin(abs(xyz[:, 1])), 1]
    iz = ijk[np.argmin(abs(xyz[:, 2] - 1.595)), 2]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.15), layout="constrained")
    for ax, mask, col, height, title, label, step in [
        (axes[0], ijk[:, 1] == iy, 2, dz, "Sección vertical", "z (m)", dz),
        (axes[1], ijk[:, 2] == iz, 1, dy, "Sección horizontal", "y (m)", dy),
    ]:
        section = np.full((ijk[:, col].max()+1, ijk[:, 0].max()+1), np.nan)
        section[ijk[mask, col], ijk[mask, 0]] = values[mask]
        x0 = xyz[:, 0].min() - dx / 2
        y0 = xyz[:, col].min() - height / 2
        image = ax.imshow(section, origin="lower", interpolation="nearest",
                          extent=[x0, x0 + dx*section.shape[1],
                                  y0, y0 + step*section.shape[0]],
                          cmap="inferno", vmin=26, vmax=50)
        ax.set(xlabel="x (m)", ylabel=label, title=title)
    fig.colorbar(image, ax=axes, label="Temperatura (°C)", shrink=.76)
    fig.savefig(out / "cortes.pdf")

    fig = plt.figure(figsize=(6.3, 3.55))
    ax = fig.add_subplot(projection="3d")
    # Quarter cutaway, displaying the stored cell centers behind the cut.
    keep = np.isfinite(values) & ~((xyz[:, 0] > 0) & (xyz[:, 1] < 0))
    artist = ax.scatter(*xyz[keep].T, c=values[keep], cmap="inferno",
                        vmin=26, vmax=50, s=2, depthshade=False, rasterized=True)
    ax.set(xlabel="x (m)", ylabel="y (m)", zlabel="z (m)")
    ax.zaxis.labelpad = 0
    ax.set_zticks([0, 2, 4])
    ax.set_box_aspect((18, 18, 5.5))
    ax.view_init(elev=25, azim=-56)
    fig.colorbar(artist, ax=ax, label="Temperatura (°C)", shrink=.65, pad=.17)
    fig.savefig(out / "campo_3d.pdf", dpi=235)

mc = json.loads((root / "results/e14/monte_carlo/summary.json").read_text())
fig, ax = plt.subplots(figsize=(7.2, 3.3))
for plan in mc["plans"]:
    if plan["plan"] not in {"curado_rapido", "curado_frio5"}:
        continue
    n = [row["N"] for row in plan["Pf_N"]]
    risk = 100 * np.array([row["Pf"] for row in plan["Pf_N"]])
    lo, hi = 100 * np.array([row["CI"] for row in plan["Pf_N"]]).T
    line, = ax.semilogx(n, risk, label=plan["plan"])
    ax.fill_between(n, lo, hi, color=line.get_color(), alpha=.16)
ax.set(xlabel="Número de sorteos del soporte", ylabel="Falla conjunta (%)",
       ylim=(45, 101))
ax.legend(loc="lower right")
fig.savefig(out / "monte_carlo.pdf")

f02 = json.loads((root / "results/f02/enumeration.json").read_text())
e14 = json.loads((root / "results/e14/official.json").read_text())
chunks = {}
historical = []
for case in e14["case_index"]:
    chunk = case["chunk"]
    if chunk not in chunks:
        chunks[chunk] = json.loads((root / chunk).read_text())["entries"]
    historical.append(chunks[chunk][case["entry"]]["row"])

def flatten(row):
    scenario = row["scenario"]
    curve, climate = scenario.rsplit("_", 1)
    peak = row["peak"]
    delta = row["delta_peak"]
    coords = peak["coordinate_m"] + delta["hot"]["coordinate_m"] + delta["cold"]["coordinate_m"]
    return [row["plan"], curve, climate, row["weight"], row["Tmax_C"],
            row["delta_C"], int(row["fail_T"]), int(row["fail_delta"]),
            int(row["fail_joint"]), peak["time_h"], delta["time_h"], *coords]

header = ["plan", "curva", "clima", "peso", "M_T_C", "M_delta_C",
          "I_T", "I_delta", "I_F", "t_T_h", "t_delta_h"]
header += [f"{peak}_{axis}_m" for peak in ("pico_T", "delta_caliente", "delta_frio")
           for axis in "xyz"]
with (out.parent / "escenarios_f02.csv").open("w", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(header)
    writer.writerows(flatten(row) for row in f02["rows"])
with (out.parent / "extremos_por_plan.csv").open("w", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["envolvente", *header])
    for name in [plan["plan"] for plan in plans]:
        rows = [row for row in historical + f02["rows"] if row["plan"] == name]
        for metric in ("Tmax_C", "delta_C"):
            writer.writerow([metric, *flatten(max(rows, key=lambda row: row[metric]))])


sources = np.loadtxt(root / "data/hydration/source_terms.txt")
fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.4), layout="constrained")
for group, ax in enumerate(axes):
    for index in range(4):
        ax.plot(sources[:, 0], sources[:, 1 + 4 * group + index],
                label=f"M{index + 1}", lw=1)
    ax.set(title=("Campaña SS", "Campaña 22A")[group],
           xlabel="Edad tabulada (h)", xlim=(0, 240), ylim=(0, 660))
    ax.legend(ncol=2, frameon=False)
axes[0].set_ylabel("Tasa volumétrica (W/m³)")
fig.savefig(out / "hidratacion.pdf")

with (out.parent / "riesgo_336h_e14.csv").open("w", newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(["plan", "casos", "peso_excedido_336h"])
    for name in dict.fromkeys(row["plan"] for row in historical):
        cases = [row for row in historical if row["plan"] == name]
        assert len(cases) == 24
        exceeded = [row["weight"] for row in cases
                    if row["first336_Tmax_C"] > 70 or row["first336_delta_C"] > 20]
        writer.writerow([name, len(cases), fsum(exceeded)])

circuits = f02["rows"][0]["water"]["circuits"]
fig, ax = plt.subplots(figsize=(6.4, 3.2), subplot_kw={"projection": "3d"})
colors = {3: "#15687c", 4: "#a84328", 5: "#493d78"}
seen = set()
for branch in circuits:
    pour = branch["pour"]
    ax.plot([branch["x_low_m"], branch["x_high_m"]], [branch["y_m"]] * 2,
            [branch["z_m"]] * 2, color=colors[pour],
            label=f"Vertida {pour}" if pour not in seen else None)
    seen.add(pour)
ax.set(xlabel="x (m)", ylabel="y (m)", zlabel="z (m)")
ax.set_box_aspect((10, 10, 5))
ax.view_init(elev=23, azim=-59)
ax.legend(loc="upper left", frameon=False)
fig.savefig(out / "ramales.pdf")
