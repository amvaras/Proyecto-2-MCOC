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
    hierarchy = []
    parent = None
    for cls in ("IfcProject", "IfcSite", "IfcBuilding", "IfcBuildingStorey"):
        objects = model.by_type(cls)
        require(len(objects) == 1, f"Se esperaba exactamente un {cls}")
        current = objects[0]
        if parent is not None:
            require(ifcopenshell.util.element.get_aggregate(current) == parent,
                    f"Jerarquia espacial incorrecta para {cls}")
        hierarchy.append(dict(ifc_class=cls, name=current.Name))
        parent = current
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
        require(container == parent, "Contenedor espacial incorrecto")
        require(ifcopenshell.util.element.get_material(element) is not None, "Falta material")
        shape = ifcopenshell.geom.create_shape(settings, element)
        vertices = np.array(shape.geometry.verts).reshape(-1, 3)
        faces = np.array(shape.geometry.faces).reshape(-1, 3)
        require(len(vertices) > 0 and len(faces) > 0 and np.all(np.isfinite(vertices)),
                "Geometria vacia o no finita")
        low, high = vertices.min(axis=0), vertices.max(axis=0)
        z0, z1 = elevations[i]
        require(np.allclose([low[2], high[2]], [z0, z1], atol=1e-7, rtol=0), "Cotas z incorrectas")
        width = 2 * apothems[i][0] if i < 4 else 7.
        # Teselación del círculo: tolerancia 2 mm, octágonos exactos a 1e-7 m.
        tolerance = 1e-7 if i < 4 else .002
        require(np.allclose(low[:2], [-width/2]*2, atol=tolerance, rtol=0)
                and np.allclose(high[:2], [width/2]*2, atol=tolerance, rtol=0), "Planta o centrado incorrectos")
        if i < 4:
            for elevation, apothem in zip((z0, z1), apothems[i]):
                ring = vertices[np.isclose(vertices[:, 2], elevation, atol=1e-7, rtol=0), :2]
                angles = np.pi/8 + np.arange(8)*np.pi/4
                expected = apothem / math.cos(math.pi/8) * np.column_stack(
                    (np.cos(angles), np.sin(angles)))
                distances = np.linalg.norm(ring[:, None, :] - expected[None, :, :], axis=2)
                require(len(ring) == 8 and np.all(distances.min(axis=0) < 1e-7)
                        and np.all(distances.min(axis=1) < 1e-7), "Anillo octagonal incorrecto")
        else:
            profiles = [item.SweptArea for representation in element.Representation.Representations
                        for item in representation.Items if item.is_a("IfcExtrudedAreaSolid")]
            require(len(profiles) == 1 and profiles[0].is_a("IfcCircleProfileDef")
                    and math.isclose(profiles[0].Radius, 3.5, abs_tol=1e-10, rel_tol=0),
                    "Perfil circular del pedestal incorrecto")
        edges = Counter(tuple(sorted((int(a), int(b)))) for face in faces
                        for a, b in zip(face, np.roll(face, -1)))
        require(all(count == 2 for count in edges.values()), "Malla abierta/no manifold")
        directed = Counter((int(a), int(b)) for face in faces
                           for a, b in zip(face, np.roll(face, -1)))
        require(all(directed[(a, b)] == directed[(b, a)] == 1 for a, b in directed),
                "Orientacion inconsistente entre triangulos")
        neighbors = {index: set() for index in range(len(vertices))}
        for a, b in edges:
            neighbors[a].add(b)
            neighbors[b].add(a)
        visited, pending = set(), [0]
        while pending:
            index = pending.pop()
            if index not in visited:
                visited.add(index)
                pending.extend(neighbors[index] - visited)
        require(len(visited) == len(vertices), "Malla con componentes desconectadas")
        triangles = vertices[faces]
        normals = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
        require(np.all(np.linalg.norm(normals, axis=1) > 1e-12), "Triangulos degenerados")
        volume = float(np.sum(np.einsum("ij,ij->i", triangles[:, 0],
                        np.cross(triangles[:, 1], triangles[:, 2]))) / 6)
        if i < 4:
            a0, a1 = apothems[i]
            # Área de octágono = 8*a²*tan(pi/8); volumen de tronco por integración.
            exact_volume = 8 * math.tan(math.pi/8) * (z1-z0) / 3 * (a0*a0 + a0*a1 + a1*a1)
        else:
            exact_volume = math.pi * 3.5**2 * (z1-z0)
        require(volume > 0 and math.isclose(volume, exact_volume, rel_tol=5e-4), "Volumen/orientacion incorrectos")
        sets = ifcopenshell.util.element.get_psets(element)
        require("UANDES_HormigonMasivo" in sets, "Falta UANDES_HormigonMasivo")
        properties = sets["UANDES_HormigonMasivo"]
        require(properties["VertidaID"] == i+1, "Propiedad VertidaID incorrecta")
        for key, measured in (("ZInferior_m", low[2]), ("ZSuperior_m", high[2])):
            declared = properties.get(key)
            require(isinstance(declared, (int, float)) and math.isfinite(declared)
                    and math.isclose(declared, measured, abs_tol=1e-7, rel_tol=0),
                    f"Propiedad {key} no coincide con geometria")
        require(bool(properties.get("Estado")) and bool(properties.get("Procedencia")),
                "Faltan Estado o Procedencia")
        rows.append(dict(name=element.Name, ifc_class=element.is_a(), guid=element.GlobalId,
                         bbox_min_m=low.tolist(), bbox_max_m=high.tolist(),
                         dimensions_m=(high-low).tolist(), volume_mesh_m3=volume,
                         volume_analytic_m3=exact_volume, triangles=len(faces),
                         properties={k: v for k, v in properties.items() if k != "id"}))
    pair_checks = []
    for i, first in enumerate(rows):
        for second in rows[i+1:]:
            overlap = (np.minimum(first["bbox_max_m"], second["bbox_max_m"])
                       - np.maximum(first["bbox_min_m"], second["bbox_min_m"]))
            # Una separacion de los interiores de AABB en cualquier eje prueba
            # ausencia de interseccion volumetrica; tocarse en una cara se admite.
            require(np.any(overlap <= 1e-7), "Posible solapamiento volumetrico")
            pair_checks.append(dict(first=first["name"], second=second["name"],
                                    interior_overlap=False))
    return dict(schema=model.schema, length_unit="m", elements=len(elements),
                schema_validation_issues=len(logger.statements),
                origin="local, sin georreferenciacion", spatial_hierarchy=hierarchy, items=rows,
                pairwise_overlap_checks=pair_checks,
                global_min_m=np.min([r["bbox_min_m"] for r in rows], axis=0).tolist(),
                global_max_m=np.max([r["bbox_max_m"] for r in rows], axis=0).tolist(),
                verification_method="Automatizada con IfcOpenShell; evidencia humana por separado")


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
