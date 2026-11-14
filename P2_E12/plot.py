"""Figuras científicas desde el cálculo archivado de E12."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

from mcoc_p2.e07.voxel import VoxelGrid, Voxelization
from mcoc_p2.e09.plots import face_geometry, _set_3d


def plot(folder):
    report = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
    data = np.genfromtxt(folder / "series.csv", names=True, delimiter=",")
    peak = report["peak"]
    diff = report["differential"]
    h = data["time_s"] / 3600
    seam = report["weather"]["forecast_hours"]
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True, layout="constrained")
    ax, gap, air = axes
    for axis in axes:
        if 0 < seam < h[-1]:
            axis.axvline(seam, color="#777a85", linestyle=":", linewidth=1)
        axis.grid(alpha=.23)
    ax.plot(h, data["Tmax_C"], color="#b04833", label="Máximo en hormigón activo")
    ax.plot(h, data["core_C"], color="#d18723", label="Núcleo fijo")
    ax.plot(h, data["top25_C"], color="#4488a5", label="Sonda superior a 25 mm")
    ax.plot(h, data["S25min_C"], color="#135d64", label="Mínimo en S₂₅")
    ax.axhline(70, linestyle="--", color="#7d4540", linewidth=1, label="Límite de 70 °C")
    ax.scatter(peak["hour"], peak["temperature_C"], color="#b04833", zorder=3)
    ax.set_ylabel("Temperatura [°C]")
    ax.legend(loc="lower center", bbox_to_anchor=(.5, 1.02), ncol=3, fontsize=9, frameon=False)
    gap.plot(h, data["delta_C"], color="#5b4582", label="Máximo activo − mínimo en S₂₅")
    gap.axhline(20, linestyle="--", color="#7d4540", linewidth=1, label="Límite de 20 °C")
    gap.scatter(diff["hour"], diff["difference_C"], color="#5b4582", zorder=3)
    gap.set_ylabel("Diferencial [°C]")
    gap.legend(frameon=False, fontsize=9)
    air.plot(h[h < seam], data["air_C"][h < seam], color="#105c90", label="Pronóstico")
    air.plot(h[h >= seam], data["air_C"][h >= seam], color="#b26a1e", label="Análogo ERA5")
    air.set(xlabel="Horas desde la primera vertida", ylabel="Aire a 2 m [°C]", xlim=(0, 336))
    air.legend(frameon=False, fontsize=9)
    fig.suptitle("E12 · Temperatura del hormigón y cambio de fuente meteorológica", fontsize=15)
    fig.savefig(folder / "curvas.png", dpi=160)
    plt.close(fig)

    with np.load(folder / "fields.npz", allow_pickle=False) as fields:
        ids = fields["vertida_id"]
        start = fields["origin_m"]
        spacing = fields["spacing_m"]
        peak_field, diff_field = fields["peak"], fields["differential"]
    rows = report["grid"]["by_pour"]
    grid = VoxelGrid(tuple(start), tuple(spacing), ids.shape)
    voxels = Voxelization(grid, ids, {r["vertida_id"]: r["guid"] for r in rows},
                          {r["vertida_id"]: r["volume_reference_m3"] for r in rows})
    faces, quads = face_geometry(voxels, half=True)
    cut_y = grid.origin[1] + int(np.argmin(abs(grid.coordinates[1]))) * spacing[1]
    norm = Normalize(np.nanmin([peak_field, diff_field]), peak["temperature_C"])
    fig = plt.figure(figsize=(11, 6), layout="constrained")
    axes = []
    for i, (field, title, points) in enumerate((
        (peak_field, f"Máximo de temperatura · {peak['hour']:.2f} h", [peak["xyz_m"]]),
        (diff_field, f"Máximo diferencial · {diff['hour']:.2f} h", [diff["hot"]["xyz_m"], diff["cold"]["xyz_m"]]),
    ), 1):
        axis = fig.add_subplot(1, 2, i, projection="3d", computed_zorder=False)
        axes.append(axis)
        values = field[tuple(faces.indices.T)]
        rgba = plt.colormaps["inferno"](norm(values))
        rgba[~np.isfinite(values)] = (.82, .84, .86, 1.)
        axis.add_collection3d(Poly3DCollection(quads, facecolors=rgba, linewidths=0, edgecolors="none"))
        _set_3d(axis, voxels, -123, 27)
        axis.set_ylim(cut_y, grid.upper[1])
        for marker, (x, y, z) in enumerate(points):
            axis.scatter(x, y, z, color="white" if marker == 0 else "#4ad4ff",
                         edgecolors="#28252e", s=48, depthshade=False, zorder=10)
        axis.set_title(title, fontsize=12)
    fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap="inferno"), ax=axes, location="bottom",
                 shrink=.65, aspect=40, label="Temperatura en centros de celda [°C]")
    fig.suptitle("Corte 3D de la fundación · punto caliente en blanco, S₂₅ en celeste", fontsize=15)
    fig.savefig(folder / "cortes_3d.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    plot(parser.parse_args().result)
