"""Verificacion tecnica E01 con historial de ejecuciones y evidencia humana separada."""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidencias/auditoria"


def run(command: list[str], log: str) -> dict:
    started = time.perf_counter()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    output = result.stdout + result.stderr
    (EVIDENCE / log).write_text(output, encoding="utf-8")
    print(f"{log}: exit={result.returncode}")
    if result.returncode:
        print(output)
        raise SystemExit(result.returncode)
    return {"command": ["python" if x == sys.executable else x for x in command],
            "exit_code": result.returncode, "log": log,
            "elapsed_s": time.perf_counter()-started}


def main() -> None:
    global EVIDENCE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=EVIDENCE)
    args = parser.parse_args()
    EVIDENCE = args.output if args.output.is_absolute() else ROOT / args.output
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    output_arg = str(EVIDENCE.relative_to(ROOT)) if EVIDENCE.is_relative_to(ROOT) else str(EVIDENCE)
    if (EVIDENCE / "verification.json").exists():
        archive = EVIDENCE / "historial" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        archive.mkdir(parents=True)
        for path in EVIDENCE.iterdir():
            if path.is_file():
                shutil.copy2(path, archive / path.name)
    # Evita dejar un resumen viejo aparentemente válido si una nueva corrida falla.
    (EVIDENCE / "verification.json").write_text(
        json.dumps({"status": "running", "started_utc": datetime.now(timezone.utc).isoformat()}) + "\n",
        encoding="utf-8")
    try:
        checks = [run([sys.executable, "-m", "pip", "check"], "pip_check.txt"),
                  run([sys.executable, "-m", "pytest", "-q",
                       "--junitxml="+str(Path(output_arg) / "pytest.xml")], "pytest.txt"),
                  run([sys.executable, "examples/run_diffusion_1d.py", "--output", output_arg], "example.txt"),
                  run([sys.executable, "scripts/check_diffusion_accuracy.py", "--benchmark", output_arg,
                       "--json", str(Path(output_arg) / "accuracy.json")], "accuracy.txt"),
                  run([sys.executable, "scripts/check_ifc.py", "geometry/foundation.ifc",
                       "--json", str(Path(output_arg) / "ifc_check.json")], "ifc_check.txt"),
                  run([sys.executable, "scripts/render_ifc_preview.py", "--output",
                       str(Path(output_arg) / "foundation_preview.png")], "ifc_preview.txt"),
                  run([sys.executable, "scripts/check_bonsai_evidence.py", "--json",
                       str(Path(output_arg) / "bonsai_evidence.json")], "bonsai_evidence.txt")]
    except SystemExit as error:
        (EVIDENCE / "verification.json").write_text(json.dumps(dict(
            status="failed", exit_code=error.code,
            completed_utc=datetime.now(timezone.utc).isoformat()))+"\n", encoding="utf-8")
        raise
    files = [p for folder in ("src", "tests", "scripts", "geometry")
             for p in (ROOT / folder).rglob("*") if p.suffix in (".py", ".ifc")]
    files += [ROOT / "pyproject.toml", ROOT / "requirements-lock.txt"]
    hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(files)}
    suites = list(ET.parse(EVIDENCE / "pytest.xml").getroot().iter("testsuite"))
    counts = {key: sum(int(suite.get(key, "0")) for suite in suites)
              for key in ("tests", "failures", "errors", "skipped")}
    counts["passed"] = counts["tests"]-counts["failures"]-counts["errors"]-counts["skipped"]
    counts["elapsed_s"] = sum(float(suite.get("time", "0")) for suite in suites)
    report = dict(status="passed", completed_utc=datetime.now(timezone.utc).isoformat(),
                  python=platform.python_version(), platform=platform.system(),
                  architecture=platform.machine(),
                  dependencies={n: importlib.metadata.version(n) for n in
                                ("numpy", "matplotlib", "pytest", "ifcopenshell")},
                  checks=checks, pytest=counts, file_sha256=hashes,
                  human_bonsai_evidence="Ocho capturas aportadas, inspeccionadas y contrastadas con IFC",
                  auditor_opened_blender=False)
    (EVIDENCE / "verification.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Verificacion tecnica completa; consultar {EVIDENCE / 'verification.json'}")


if __name__ == "__main__":
    main()
