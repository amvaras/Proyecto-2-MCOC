"""Verifica el archivo entregado y la capacidad de reconstruirlo."""

from pathlib import Path
import importlib.util

import pytest

pytest.importorskip("ifcopenshell", reason="Instalar extra [bim] para verificar IFC")
ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_delivered_ifc_schema_identity_dimensions_and_volume():
    report = load_script("check_ifc").inspect_model(ROOT / "geometry/foundation.ifc")
    assert report["elements"] == 5
    assert report["schema_validation_issues"] == 0


def test_rebuild_ifc_preserves_guids_and_geometry(tmp_path):
    path = tmp_path / "rebuilt.ifc"
    load_script("create_preliminary_ifc").create_model(path)
    inspector = load_script("check_ifc")
    original = inspector.inspect_model(ROOT / "geometry/foundation.ifc")
    rebuilt = inspector.inspect_model(path)
    assert original == rebuilt


@pytest.mark.parametrize("property_name", ["ZInferior_m", "ZSuperior_m"])
def test_verifier_rejects_properties_inconsistent_with_geometry(tmp_path, property_name):
    import ifcopenshell
    from ifcopenshell.api import pset
    model = ifcopenshell.open(str(ROOT / "geometry/foundation.ifc"))
    element = model.by_type("IfcFooting")[0]
    property_set = next(relation.RelatingPropertyDefinition for relation in element.IsDefinedBy
                        if relation.is_a("IfcRelDefinesByProperties")
                        and relation.RelatingPropertyDefinition.Name == "UANDES_HormigonMasivo")
    pset.edit_pset(model, pset=property_set, properties={property_name: 99.})
    path = tmp_path / "incorrect_properties.ifc"
    model.write(str(path))
    with pytest.raises(ValueError, match=property_name):
        load_script("check_ifc").inspect_model(path)


def test_verifier_rejects_broken_spatial_hierarchy(tmp_path):
    import ifcopenshell
    from ifcopenshell.api import aggregate
    model = ifcopenshell.open(str(ROOT / "geometry/foundation.ifc"))
    floor = model.by_type("IfcBuildingStorey")[0]
    aggregate.assign_object(model, products=[floor], relating_object=model.by_type("IfcSite")[0])
    path = tmp_path / "incorrect_hierarchy.ifc"
    model.write(str(path))
    with pytest.raises(ValueError, match="Jerarquia"):
        load_script("check_ifc").inspect_model(path)
