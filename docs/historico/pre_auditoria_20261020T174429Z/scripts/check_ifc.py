"""Inspecciona y verifica IFC4 E01; termina con error si no es coherente."""

import argparse
from collections import Counter
import json
import math
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.unit
import ifcopenshell.validate
import numpy as np


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def inspect_model(path: Path) -> dict:
    model = ifcopenshell.open(str(path))
    require(model.schema == "IFC4", "Se esperaba IFC4")
    logger = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(model, logger, express_rules=True)
    require(not logger.statements, f"Validacion IFC: {logger.statements}")
    require(ifcopenshell.util.unit.calculate_unit_scale(model) == 1., "Unidad debe ser metro")
    elements = sorted(model.by_type("IfcElement"), key=lambda e: e.Name or "")
    require(len(elements) == 5, "Se esperaban exactamente cinco elementos BIM")
    roots = model.by_type("IfcRoot")
    require(len({e.GlobalId for e in roots}) == len(roots), "GUID duplicados")
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)
    rows = []
    apothems = [(9., 9.), (9., 9.), (9., 6.25), (6.25, 3.5)]
    elevations = [(0., .55), (.55, 1.1), (1.1, 2.2), (2.2, 3.3), (3.3, 4.3)]
    for i, element in enumerate(elements):
        require(element.Name == f"Vertida_{i+1:02d}", "Nombre de vertida incorrecto")
        require(element.is_a() == "IfcFooting", "Clase debe ser IfcFooting")
        require(len(ifcopenshell.guid.expand(element.GlobalId)) == 32, "GUID invalido")
        container = ifcopenshell.util.element.get_container(element)
        require(container is not None and container.is_a("IfcBuildingStorey"), "Falta contenedor espacial")
        require(ifcopenshell.util.element.get_material(element) is not None, "Falta material")
        shape = ifcopenshell.geom.create_shape(settings, element)
        vertices = np.array(shape.geometry.verts).reshape(-1, 3)
        faces = np.array(shape.geometry.faces).reshape(-1, 3)
        low, high = vertices.min(axis=0), vertices.max(axis=0)
        z0, z1 = elevations[i]
        require(np.allclose([low[2], high[2]], [z0, z1], atol=1e-7, rtol=0), "Cotas z incorrectas")
        width = 2 * apothems[i][0] if i < 4 else 7.
        # Teselación del círculo: tolerancia 2 mm, octágonos exactos a 1e-7 m.
        tolerance = 1e-7 if i < 4 else .002
        require(np.allclose(low[:2], [-width/2]*2, atol=tolerance, rtol=0)
                and np.allclose(high[:2], [width/2]*2, atol=tolerance, rtol=0), "Planta o centrado incorrectos")
        edges = Counter(tuple(sorted((int(a), int(b)))) for face in faces
                        for a, b in zip(face, np.roll(face, -1)))
        require(all(count == 2 for count in edges.values()), "Malla abierta/no manifold")
        triangles = vertices[faces]
        volume = float(np.sum(np.einsum("ij,ij->i", triangles[:, 0],
                        np.cross(triangles[:, 1], triangles[:, 2]))) / 6)
        if i < 4:
            a0, a1 = apothems[i]
            # Área de octágono = 8*a²*tan(pi/8); volumen de tronco por integración.
            exact_volume = 8 * math.tan(math.pi/8) * (z1-z0) / 3 * (a0*a0 + a0*a1 + a1*a1)
        else:
            exact_volume = math.pi * 3.5**2 * (z1-z0)
        require(volume > 0 and math.isclose(volume, exact_volume, rel_tol=5e-4), "Volumen/orientacion incorrectos")
        properties = ifcopenshell.util.element.get_psets(element)["UANDES_HormigonMasivo"]
        require(properties["VertidaID"] == i+1, "Propiedad VertidaID incorrecta")
        rows.append(dict(name=element.Name, ifc_class=element.is_a(), guid=element.GlobalId,
                         bbox_min_m=low.tolist(), bbox_max_m=high.tolist(),
                         dimensions_m=(high-low).tolist(), volume_mesh_m3=volume,
                         volume_analytic_m3=exact_volume, triangles=len(faces)))
    return dict(schema=model.schema, length_unit="m", elements=len(elements),
                schema_validation_issues=len(logger.statements),
                origin="local, sin georreferenciacion", items=rows,
                global_min_m=np.min([r["bbox_min_m"] for r in rows], axis=0).tolist(),
                global_max_m=np.max([r["bbox_max_m"] for r in rows], axis=0).tolist(),
                bonsai_visual_check=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=Path("geometry/foundation.ifc"))
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    report = inspect_model(args.path)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
