"""Copia E05 fuera del proyecto, instala desde sus propias ruedas y verifica todo."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path("evidencias/e05_independencia"))
    args=parser.parse_args()
    out=args.output.resolve()
    if out.exists() and any(out.iterdir()):parser.error("Destino con contenido; elegir otro")
    out.mkdir(parents=True,exist_ok=True)
    temporary=Path(tempfile.mkdtemp(prefix="mcoc_e05_independiente_"))
    replica=temporary/"P2_E05_autonomo"
    report=dict(status="running",started_utc=datetime.now(timezone.utc).isoformat(),
                temporary_root=str(temporary),commands=[])
    def save():(out/"independence.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1","PYTHONIOENCODING":"utf-8",
         "PYTHONNOUSERSITE":"1","PIP_NO_INDEX":"1","PIP_DISABLE_PIP_VERSION_CHECK":"1",
         "PIP_CONFIG_FILE":os.devnull}
    env.pop("PYTHONPATH",None)
    def run(name,command):
        print("Independencia: "+name,flush=True)
        p=subprocess.run(list(map(str,command)),cwd=replica,env=env,capture_output=True,text=True,encoding="utf-8")
        (out/(name+".txt")).write_text(p.stdout+p.stderr,encoding="utf-8")
        report["commands"].append(dict(name=name,returncode=p.returncode))
        save()
        if p.returncode:raise RuntimeError("Falló prueba independiente: "+name)
    try:
        selected=[]
        for p in ROOT.rglob("*"):
            relative=p.relative_to(ROOT)
            if any(part in {".git","__pycache__",".pytest_cache"} or part.startswith(".venv")
                   or part.endswith(".egg-info") for part in relative.parts):continue
            if p==out or out in p.parents:continue
            if p.is_symlink() or p.is_junction():raise ValueError("No se permiten enlaces en la copia")
            if p.is_file() and p.suffix not in (".pyc",".pyo"):
                selected.append(p)
        for p in selected:
            dest=replica/p.relative_to(ROOT)
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(p,dest)
            if os.path.samefile(p,dest) or hashlib.sha256(p.read_bytes()).digest()!=hashlib.sha256(dest.read_bytes()).digest():
                raise RuntimeError("Copia física incorrecta")
        report["copied_files"]=len(selected)
        run("crear_entorno",[sys.executable,"-B","-m","venv",temporary/"venv"])
        python=temporary/"venv/Scripts/python.exe" if os.name=="nt" else temporary/"venv/bin/python"
        run("instalar_dependencias",[python,"-m","pip","install","--no-index","--find-links",
                                    replica/"vendor/wheels","-r",replica/"requirements-lock.txt"])
        run("instalar_paquete",[python,"-m","pip","install","--no-index","--no-build-isolation",
                               "--no-deps","-e",".[dev,plot,bim]"])
        run("verificacion_completa",[python,"-X","utf8","-B","scripts/verify_e05.py","--output",temporary/"resultados"])
        verification=json.loads((temporary/"resultados/verification.json").read_text(encoding="utf-8"))
        imported=Path(verification["imported_solver"]).resolve()
        if not imported.is_relative_to(replica):raise RuntimeError("Import fuera de la copia independiente")
        if verification["status"]!="passed":raise RuntimeError("Verificación independiente no aprobada")
        shutil.copytree(temporary/"resultados",out/"resultados",copy_function=shutil.copyfile)
        report.update(status="passed",tests=verification["tests"],
                      parameter_cases_passed=verification["parameter_cases_passed"],
                      imported_solver=str(imported),offline_installation=True,
                      previous_delivery_runtime_dependencies=False)
    except BaseException:
        report["status"]="failed"
        raise
    finally:
        report["finished_utc"]=datetime.now(timezone.utc).isoformat()
        save()
    print(json.dumps({key:report[key] for key in ("status","tests","parameter_cases_passed")},indent=2))


if __name__=="__main__":main()
