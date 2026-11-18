"""Compara atributos y psets de IfcElement por GUID; no compara geometría.

Omite STEP ids, OwnerHistory y metadatos administrativos. No atribuye autoría.
"""
import argparse
import json
from pathlib import Path
import sys
import ifcopenshell
import ifcopenshell.util.element


def snapshot(path):
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"Archivo inexistente: {path}")
    try:
        model = ifcopenshell.open(str(path))
        if not model.by_type('IfcProject'):
            raise ValueError('Falta IfcProject')
        result = {}
        for element in model.by_type('IfcElement'):
            guid = element.GlobalId
            if not guid or guid in result:
                raise ValueError('GlobalId ausente o duplicado; no es posible emparejar')
            props = ifcopenshell.util.element.get_psets(element, psets_only=True)
            fields = {'Class': element.is_a(), 'Name': element.Name,
                      'Description': element.Description,
                      'PredefinedType': getattr(element, 'PredefinedType', None)}
            for pset, values in sorted(props.items()):
                for key, value in sorted(values.items()):
                    if key != 'id':
                        fields[f'{pset}.{key}'] = value
            result[guid] = fields
        return result
    except Exception as exc:
        raise ValueError(f'No se pudo leer IFC {path}: {exc}') from exc


def compare(before, after):
    old, new = snapshot(before), snapshot(after)
    changes = []
    for guid in sorted(old.keys() & new.keys()):
        for field in sorted(old[guid].keys() | new[guid].keys()):
            a, b = old[guid].get(field), new[guid].get(field)
            if a != b or (field in old[guid]) != (field in new[guid]):
                changes.append(dict(guid=guid, name=new[guid]['Name'], field=field,
                                    before=a, after=b,
                                    before_present=field in old[guid], after_present=field in new[guid]))
    return dict(before_elements=len(old), after_elements=len(new),
                added=[dict(guid=g, **new[g]) for g in sorted(new.keys()-old.keys())],
                removed=[dict(guid=g, **old[g]) for g in sorted(old.keys()-new.keys())],
                changes=changes,
                different=bool(changes or old.keys() != new.keys()),
                scope='Atributos y property sets de IfcElement; geometría no comparada',
                authorship='No comprobada por este programa')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    parser.add_argument('--json', type=Path)
    parser.add_argument('--require-change', action='store_true')
    args = parser.parse_args()
    try:
        report = compare(args.before, args.after)
        print(f"Elementos: {report['before_elements']} -> {report['after_elements']}")
        print(f"Agregados: {len(report['added'])}; eliminados: {len(report['removed'])}")
        for row in report['changes']:
            print(f"{row['name']} [{row['guid']}] {row['field']}: {row['before']!r} -> {row['after']!r}")
        for kind in ('added', 'removed'):
            for row in report[kind]:
                print(f"{kind}: {row['Name']} [{row['guid']}]")
        if not report['different']:
            print('Sin diferencias en atributos/propiedades comparados.')
        print(report['scope'])
        print('Este resultado no demuestra que la edición provenga de Bonsai.')
        if args.json:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        return 1 if args.require_change and not report['different'] else 0
    except (ValueError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
