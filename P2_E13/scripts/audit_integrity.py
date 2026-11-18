"""Compara inventarios originales y revisiones explícitas sin reescribir la base."""
import hashlib
import json
from pathlib import Path


def inspect_inventory(root, files, names=None, revisions=None):
    root = Path(root).resolve()
    selected = sorted(files if names is None else names)
    registry = root/'docs/AUDITORIA_CAMBIOS.json' if revisions is None else Path(revisions)
    entries = json.loads(registry.read_text(encoding='utf-8'))['files'] if registry.exists() else {}
    unchanged, revised, unexpected = [], [], []
    for name in selected:
        path = (root/name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            unexpected.append(name)
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        expected = files[name]['sha256']
        if actual == expected:
            unchanged.append(name)
            continue
        entry = entries.get(name, {})
        if (expected in entry.get('original_sha256', [])
                and actual == entry.get('current_sha256')
                and isinstance(entry.get('reason'), str) and entry['reason'].strip()):
            revised.append(dict(path=name, original_sha256=expected, current_sha256=actual,
                                reason=entry['reason']))
        else:
            unexpected.append(name)
    if unexpected:
        raise ValueError('Integridad: archivos con cambios no registrados o ausentes: '+str(unexpected))
    return dict(checked=len(selected), unchanged=len(unchanged), documented_revisions=revised,
                unexpected_changes=[], registry=str(registry.relative_to(root)) if registry.is_relative_to(root) else str(registry))
