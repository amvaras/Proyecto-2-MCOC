"""Comprueba el inventario de E01; solo control de conservación, no runtime E02."""
import argparse
import hashlib
import json
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('root',type=Path,help='Raíz E01 que se desea comprobar')
a=p.parse_args()
manifest=json.loads((Path(__file__).resolve().parents[1]/'docs/E01_INVENTARIO_BASE.json').read_text())
errors=[]
for row in manifest['files']:
    file=a.root/row['path']
    if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=row['sha256']:
        errors.append(row['path'])
print(json.dumps({'checked':len(manifest['files']),'changed_or_missing':errors},indent=2))
raise SystemExit(bool(errors))
