"""Comprueba la copia congelada sin escribir archivos ni requerir dependencias."""

import hashlib
import json
from pathlib import Path
import sys


def main() -> int:
    root = Path(__file__).resolve().parent
    inventory_name = "INVENTARIO_SHA256.json"
    inventory = json.loads((root / inventory_name).read_text(encoding="utf-8"))
    paths = list(root.rglob("*"))
    if any(path.is_symlink() or path.is_junction() for path in paths):
        print("ERROR: la copia contiene enlaces simbolicos o junctions")
        return 1
    actual = {path.relative_to(root).as_posix() for path in paths if path.is_file()}
    expected = {row["path"] for row in inventory["files"]}
    if actual != expected | {inventory_name}:
        print("ERROR: lista de archivos diferente del inventario")
        print("Faltantes:", sorted(expected - actual))
        print("Adicionales:", sorted(actual - expected - {inventory_name}))
        return 1
    directories = sorted(path.relative_to(root).as_posix() for path in paths if path.is_dir())
    if directories != inventory["directories"]:
        print("ERROR: estructura de carpetas diferente del inventario")
        return 1
    for row in inventory["files"]:
        path = root / row["path"]
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        if path.stat().st_size != row["bytes"] or digest.hexdigest() != row["sha256"]:
            print("ERROR: contenido modificado:", row["path"])
            return 1
    print(f"Integridad correcta: {len(expected)} archivos inventariados y el propio inventario.")
    print("La comprobacion no modifico la carpeta congelada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
