"""Vistas de geometría IFC leída por IfcOpenShell; no son capturas Bonsai."""

import argparse
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ifc", type=Path, default=Path("geometry/foundation.ifc"))
    parser.add_argument("--output", type=Path, default=Path("results/foundation_preview.png"))
    args = parser.parse_args()
    model = ifcopenshell.open(str(args.ifc))
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)
    elements = sorted(model.by_type("IfcFooting"), key=lambda e: e.Name)
    colours = ["#497aa8", "#76a8cc", "#e0a04a", "#c06a40", "#778858"]
    triangles, face_colours, exterior, exterior_colours = [], [], [], []
    for i, (element, colour) in enumerate(zip(elements, colours)):
        shape = ifcopenshell.geom.create_shape(settings, element)
        vertices = np.array(shape.geometry.verts).reshape(-1, 3)
        faces = np.array(shape.geometry.faces).reshape(-1, 3)
        triangles.extend(vertices[faces])
        face_colours.extend([colour] * len(faces))
        mesh = vertices[faces]
        horizontal = np.ptp(mesh[:, :, 2], axis=1) < 1e-8
        exposed = np.ones(len(mesh), dtype=bool)
        if i > 0:  # Tapas inferiores en contacto con otra vertida.
            exposed &= ~(horizontal & np.isclose(mesh[:, 0, 2], vertices[:, 2].min()))
        if i < 3:  # Tapas superiores completamente cubiertas por la siguiente.
            exposed &= ~(horizontal & np.isclose(mesh[:, 0, 2], vertices[:, 2].max()))
        exterior.extend(mesh[exposed])
        exterior_colours.extend([colour] * int(exposed.sum()))
    triangles = np.array(triangles)
    face_colours = np.array(face_colours)
    fig = plt.figure(figsize=(12, 8))
    grid = fig.add_gridspec(2, 2, width_ratios=(1.3, 1), height_ratios=(3, 1))
    ax3d = fig.add_subplot(grid[:, 0], projection="3d")
    # Ocultar caras internas de contacto y caras opuestas a la cámara evita
    # artefactos del ordenado por profundidad de mplot3d (no tiene z-buffer).
    exterior = np.array(exterior)
    direction = np.array([np.cos(np.deg2rad(25))*np.cos(np.deg2rad(-55)),
                          np.cos(np.deg2rad(25))*np.sin(np.deg2rad(-55)),
                          np.sin(np.deg2rad(25))])
    normals = np.cross(exterior[:, 1]-exterior[:, 0], exterior[:, 2]-exterior[:, 0])
    visible = normals @ direction > 1e-10
    ax3d.add_collection3d(Poly3DCollection(exterior[visible],
                                         facecolor=np.array(exterior_colours)[visible],
                                         edgecolor="none", antialiased=False, zsort="average"))
    ax3d.set(xlim=(-10, 10), ylim=(-10, 10), zlim=(0, 4.5),
             xlabel="x [m]", ylabel="y [m]", zlabel="z [m]", title="Vista 3D")
    ax3d.set_zticks([0, 1.1, 2.2, 3.3, 4.3])
    ax3d.set_box_aspect((20, 20, 4.5))
    ax3d.set_proj_type("ortho")
    ax3d.view_init(elev=25, azim=-55)
    for subplot, dimensions, depth, reverse, title in (
            (grid[0, 1], [0, 1], 2, False, "Planta"),
            (grid[1, 1], [0, 2], 1, True, "Vista lateral")):
        ax = fig.add_subplot(subplot)
        order = np.argsort(triangles[:, :, depth].mean(axis=1))
        if reverse:
            order = order[::-1]
        ax.add_collection(PolyCollection(triangles[order][:, :, dimensions],
                                         facecolors=face_colours[order], edgecolors="none",
                                         antialiased=False))
        ax.set_aspect("equal")
        ax.set(xlim=(-10, 10), ylim=(-10, 10) if depth == 2 else (0, 4.5),
               xlabel="x [m]", ylabel="y [m]" if depth == 2 else "z [m]", title=title)
        ax.set_xticks([-9, -4.5, 0, 4.5, 9])
        ax.set_yticks([-9, -4.5, 0, 4.5, 9] if depth == 2 else [0, 1.1, 3.3, 4.3])
        ax.grid(alpha=.2)
    fig.suptitle("IFC4 preliminar · geometría leída con IfcOpenShell (sin interfaz Bonsai)")
    fig.legend(handles=[Patch(color=c, label=e.Name) for c, e in zip(colours, elements)],
               loc="lower center", ncol=5)
    fig.subplots_adjust(left=.02, right=.96, bottom=.13, top=.91, wspace=.16, hspace=.4)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=160)
    plt.close(fig)
    print(f"Vista IFC guardada: {args.output}")


if __name__ == "__main__":
    main()
