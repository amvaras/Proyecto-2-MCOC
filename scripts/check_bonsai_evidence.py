"""Contrasta archivos de capturas YA inspeccionadas y propiedades del IFC.

No automatiza la lectura semantica de las imagenes ni ejecuta Blender/Bonsai.
El registro revision_visual.json conserva la inspeccion humana de sus pixeles.
"""

import argparse
import hashlib
import json
from pathlib import Path
import struct

import ifcopenshell
import ifcopenshell.util.element

ROOT = Path(__file__).resolve().parents[1]


def check_evidence() -> dict:
    review = json.loads((ROOT / "Evidencias/bonsai/revision_visual.json").read_text(encoding="utf-8"))
    expected = {"vista_3d.png", "vista_superior.png", "vista_perfil.png"}
    expected.update(f"propiedades_vertida_{i:02d}.png" for i in range(1, 6))
    images = review["images"]
    if len(images) != 8 or {Path(row["file"]).name for row in images} != expected:
        raise ValueError("Se requieren las ocho capturas inspeccionadas")
    model = ifcopenshell.open(str(ROOT / "geometry/foundation.ifc"))
    for row in images:
        raw = (ROOT / row["file"]).read_bytes()
        if (raw[:8] != b"\x89PNG\r\n\x1a\n"
                or hashlib.sha256(raw).hexdigest() != row["sha256"]
                or struct.unpack(">II", raw[16:24]) != (row["width"], row["height"])):
            raise ValueError(f"La imagen no coincide con la inspeccion registrada: {row['file']}")
        if "observed_name" in row:
            matches = [element for element in model.by_type("IfcFooting")
                       if element.Name == row["observed_name"]]
            if len(matches) != 1:
                raise ValueError("Nombre observado no corresponde a un unico IfcFooting")
            element = matches[0]
            properties = ifcopenshell.util.element.get_psets(element)[row["observed_pset"]]
            if not element.GlobalId.startswith(row["visible_guid_prefix"]):
                raise ValueError("Prefijo visible de GlobalId no coincide con el IFC")
            for key in ("VertidaID", "ZInferior_m", "ZSuperior_m"):
                if properties[key] != row[key]:
                    raise ValueError(f"La propiedad visible {key} no coincide con el IFC")
    return dict(images_present=8, inspected_images_unchanged=True,
                observed_properties_match_ifc=True, source=review["source"],
                blender_version=review["blender_version"], bonsai_version=review["bonsai_version"],
                audit_method=review["audit_method"], auditor_opened_blender=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    text = json.dumps(check_evidence(), ensure_ascii=False, indent=2)
    print(text)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(text+"\n", encoding="utf-8")


if __name__ == "__main__":
    main()
