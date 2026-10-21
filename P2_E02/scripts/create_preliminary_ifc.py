"""Genera la geometría docente en IFC4 mediante IfcOpenShell, sin interfaz Bonsai."""

import argparse
import math
from pathlib import Path
import uuid

import ifcopenshell
from ifcopenshell.api import context, geometry, material, pset, root, spatial, aggregate, unit
import numpy as np


def stable_guid(name: str) -> str:
    """Identidad reproducible del modelo docente al regenerarlo."""
    return ifcopenshell.guid.compress(uuid.uuid5(
        uuid.NAMESPACE_URL, f"https://github.com/amvaras/Proyecto-2-MCOC/E01/{name}").hex)


def octagonal_frustum(lower_apothem: float, upper_apothem: float,
                      height: float) -> tuple[list, list]:
    """Caras orientadas hacia afuera, anillos locales en z=0 y z=height."""
    angles = np.pi / 8 + np.arange(8) * np.pi / 4
    vertices = []
    for apothem, z in ((lower_apothem, 0.), (upper_apothem, height)):
        radius = apothem / math.cos(math.pi / 8)
        vertices.extend((float(radius * math.cos(a)), float(radius * math.sin(a)), z)
                        for a in angles)
    faces = [list(reversed(range(8))), list(range(8, 16))]
    faces.extend([i, (i+1) % 8, (i+1) % 8 + 8, i+8] for i in range(8))
    return vertices, faces


def create_model(destination: Path) -> None:
    model = ifcopenshell.file(schema="IFC4")
    project = root.create_entity(model, ifc_class="IfcProject", name="MCOC P2 - G2 - E01")
    project.GlobalId = stable_guid("project")
    unit.assign_unit(model, units=[unit.add_si_unit(model, unit_type=kind) for kind in
                                  ("LENGTHUNIT", "AREAUNIT", "VOLUMEUNIT")])
    model_context = context.add_context(model, context_type="Model")
    body = context.add_context(model, context_type="Model", context_identifier="Body",
                               target_view="MODEL_VIEW", parent=model_context)
    parent = project
    for cls, name in (("IfcSite", "Sitio local G2"), ("IfcBuilding", "Fundacion eolica"),
                      ("IfcBuildingStorey", "Nivel fundacion")):
        child = root.create_entity(model, ifc_class=cls, name=name)
        child.GlobalId = stable_guid(name)
        aggregate.assign_object(model, products=[child], relating_object=parent)
        geometry.edit_object_placement(model, product=child)
        parent = child
    concrete = material.add_material(model, name="Hormigon - propiedades por definir", category="concrete")
    layers = [(0., .55, 9., 9.), (.55, 1.10, 9., 9.),
              (1.10, 2.20, 9., 6.25), (2.20, 3.30, 6.25, 3.5),
              (3.30, 4.30, None, None)]
    for i, (z0, z1, a0, a1) in enumerate(layers, start=1):
        name = f"Vertida_{i:02d}"
        element = root.create_entity(model, ifc_class="IfcFooting", name=name,
                                     predefined_type="PAD_FOOTING")
        element.GlobalId = stable_guid(name)
        element.Description = "Modelo preliminar docente; generado en Python, sin uso de interfaz Bonsai"
        spatial.assign_container(model, products=[element], relating_structure=parent)
        placement = np.eye(4)
        placement[2, 3] = z0
        geometry.edit_object_placement(model, product=element, matrix=placement, is_si=True)
        if i < 5:
            vertices, faces = octagonal_frustum(a0, a1, z1-z0)
            representation = geometry.add_mesh_representation(model, context=body,
                                                               vertices=[vertices], faces=[faces])
            # La malla tiene dos tapas y ocho caras laterales.
            for item in representation.Items:
                if item.is_a("IfcPolygonalFaceSet"):
                    item.Closed = True
        else:
            profile = model.create_entity("IfcCircleProfileDef", ProfileType="AREA", Radius=3.5)
            representation = geometry.add_profile_representation(
                model, context=body, profile=profile, depth=z1-z0)
        geometry.assign_representation(model, product=element, representation=representation)
        material.assign_material(model, products=[element], type="IfcMaterial", material=concrete)
        properties = pset.add_pset(model, product=element, name="UANDES_HormigonMasivo")
        pset.edit_pset(model, pset=properties, properties={
            "VertidaID": i, "ZInferior_m": z0, "ZSuperior_m": z1,
            "Procedencia": "GUIA_BONSAI_FUNDACION.md; generacion Python/IfcOpenShell",
            "Estado": "Preliminar E01; sin plan constructivo optimizado",
        })
    destination.parent.mkdir(parents=True, exist_ok=True)
    model.write(str(destination))
    print(f"IFC4 escrito: {destination} (5 IfcFooting, metros, origen local)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("geometry/foundation.ifc"))
    args = parser.parse_args()
    if args.output.exists():
        parser.error("El destino ya existe; usa --output con otra ruta para no sobrescribir el IFC")
    create_model(args.output)


if __name__ == "__main__":
    main()
