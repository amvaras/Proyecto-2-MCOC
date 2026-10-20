"""Ejecuta verificaciones y conserva salidas reales; no modifica Git ni publica."""

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidencias"


def run(command: list[str], log: str) -> dict:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    output = result.stdout + result.stderr
    (EVIDENCE / log).write_text(output, encoding="utf-8")
    print(f"{log}: exit={result.returncode}")
    if result.returncode:
        print(output)
        raise SystemExit(result.returncode)
    return {"command": ["python" if x == sys.executable else x for x in command],
            "exit_code": result.returncode, "log": log}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8").strip()


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    # Evita dejar un resumen viejo aparentemente válido si una nueva corrida falla.
    (EVIDENCE / "verification.json").write_text(
        json.dumps({"status": "running", "started_utc": datetime.now(timezone.utc).isoformat()}) + "\n",
        encoding="utf-8")
    checks = [run([sys.executable, "-m", "pip", "check"], "pip_check.txt"),
              run([sys.executable, "-m", "pytest", "-q"], "pytest.txt"),
              run([sys.executable, "examples/run_diffusion_1d.py", "--output", "docs/evidencias"], "example.txt"),
              run([sys.executable, "scripts/check_ifc.py", "geometry/foundation.ifc",
                   "--json", "docs/evidencias/ifc_check.json"], "ifc_check.txt"),
              run([sys.executable, "scripts/render_ifc_preview.py", "--output",
                   "docs/evidencias/foundation_preview.png"], "ifc_preview.txt")]
    files = [p for folder in ("src", "tests", "scripts", "geometry")
             for p in (ROOT / folder).rglob("*") if p.suffix in (".py", ".ifc")]
    files += [ROOT / "pyproject.toml", ROOT / "requirements-lock.txt"]
    hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(files)}
    report = dict(status="passed", completed_utc=datetime.now(timezone.utc).isoformat(),
                  python=platform.python_version(), platform=platform.system(),
                  architecture=platform.machine(),
                  dependencies={n: importlib.metadata.version(n) for n in
                                ("numpy", "matplotlib", "pytest", "ifcopenshell")},
                  checks=checks, branch=git("branch", "--show-current"),
                  base_head=git("rev-parse", "HEAD"),
                  note="Ejecucion del arbol local; base_head no identifica los cambios sin commit",
                  sha256=hashes, bonsai_visual_check=False)
    (EVIDENCE / "verification.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Verificacion completa; consultar docs/evidencias/verification.json")


if __name__ == "__main__":
    main()
