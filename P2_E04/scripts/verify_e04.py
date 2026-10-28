"""Genera evidencia E04 desde procesos reales; no publica ni cambia otras entregas."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=Path("results/e04/verificacion"))
    a = p.parse_args()
    out = a.output.resolve()
    if out.exists() and any(out.iterdir()):
        p.error("El destino contiene archivos; elige otra carpeta para preservar evidencia")
    out.mkdir(parents=True, exist_ok=True)
    (ROOT/"results/e04").mkdir(parents=True, exist_ok=True)
    report = dict(status="running", started_utc=datetime.now(timezone.utc).isoformat(),
                  python=platform.python_version(), platform=platform.platform(),
                  imported_solver=None, packages={}, commands=[])
    import mcoc_p2
    report["imported_solver"] = str(Path(mcoc_p2.__file__).resolve())
    if Path(mcoc_p2.__file__).resolve().parent != ROOT/"src/mcoc_p2":
        raise RuntimeError("El solver importado no pertenece a esta carpeta E04")
    for name in ("numpy","pytest","matplotlib","ifcopenshell","mcoc-p2"):
        report["packages"][name] = importlib.metadata.version(name)
    commands = [
        ("pip_check", ["-m","pip","check"]),
        ("pytest", ["-m","pytest","tests","-q","-p","no:cacheprovider",
                    f"--basetemp={ROOT/'results/e04/pytest_tmp'}",f"--junitxml={out/'pytest.xml'}"]),
        ("convergence", ["scripts/check_e04_convergence.py","--json",str(out/"convergence.json")]),
    ]
    for dim, case in ((2,"sine"),(3,"sine"),(3,"source"),(3,"robin"),(2,"flux"),(3,"two-materials")):
        commands.append((f"{case}_{dim}d", ["examples/run_e04.py","--dim",str(dim),"--case",case,
                                          "--n","12","--output",str(out/f"{case}_{dim}d")]))
    commands.extend([
        ("ifc_check", ["scripts/check_ifc.py","geometry/foundation.ifc","--json",str(out/"ifc_check.json")]),
        ("ifc_preview", ["scripts/render_ifc_preview.py","--output",str(out/"foundation_preview.png")]),
    ])
    manifest = out/"verification.json"
    try:
        for name, args in commands:
            print(f"Ejecutando {name}...", flush=True)
            completed = subprocess.run([sys.executable,"-X","utf8","-B",*args],cwd=ROOT,
                                       capture_output=True,text=True,encoding="utf-8")
            (out/f"{name}.txt").write_text(completed.stdout+completed.stderr,encoding="utf-8")
            report["commands"].append(dict(name=name,arguments=args,returncode=completed.returncode))
            manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            if completed.returncode:
                raise RuntimeError(f"Falló {name}; consultar {out/name}.txt")
        suites = ET.parse(out/"pytest.xml").getroot()
        report["tests"] = {key:sum(int(s.get(key,0)) for s in suites.iter("testsuite"))
                           for key in ("tests","failures","errors","skipped")}
        if any(report["tests"][key] for key in ("failures","errors","skipped")):
            raise RuntimeError("La entrega requiere todos los tests aprobados sin omisiones")
        report["status"] = "passed"
    except Exception:
        report["status"] = "failed"
        raise
    finally:
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        report["input_sha256"] = {path.relative_to(ROOT).as_posix():hashlib.sha256(path.read_bytes()).hexdigest()
                                  for folder in ("src","tests","examples","scripts","geometry")
                                  for path in sorted((ROOT/folder).rglob("*"))
                                  if path.suffix in (".py",".ifc")}
        manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(status=report["status"],tests=report["tests"]),indent=2))


if __name__ == "__main__":
    main()
