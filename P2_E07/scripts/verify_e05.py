"""Ejecuta E05 con evidencia real; destinos nuevos, núcleo heredado y origen propio."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from mcoc_p2.verification_e05 import make_config,run_case

ROOT=Path(__file__).resolve().parents[1]


def parameter_sweep():
    """Ejercita parámetros reales: geometrías no cúbicas, signos, ejes y h."""
    reports=[]
    for dim in (1,2,3):
        base=dict(dimension=dim,shape=tuple(4+i for i in range(dim)),
                  lengths_m=tuple(1.2+.5*i for i in range(dim)),k=1.3,rho=2300.,cp=870.,t_end_s=3000.)
        for source in (-900.,0.,900.):
            reports.append(run_case("source",make_config("source",{**base,"q_dot":source}))[0])
        reports.append(run_case("energy",make_config("energy",{**base,"heterogeneous":True}))[0])
        for axis in "xyz"[:dim]:
            for side in "-+":
                for flux in (-135.,135.):
                    reports.append(run_case("neumann",make_config("neumann",{**base,"face":axis+side,"flux":flux}))[0])
        for h in (0.,12.,250.):
            for ambient in (10.,35.):
                reports.append(run_case("robin",make_config("robin",{**base,"h":h,"ambient_C":ambient}))[0])
        for case in ("spatial","temporal"):
            reports.append(run_case(case,make_config(case,{**base,"amplitude_C":7.}))[0])
    return reports


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=Path("evidencias/e05")/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    args=parser.parse_args()
    out=args.output.resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        parser.error("Destino existente con contenido; no se sobrescriben evidencias")
    out.mkdir(parents=True,exist_ok=True)
    manifest=out/"verification.json"
    report=dict(status="running",started_utc=datetime.now(timezone.utc).isoformat(),
                python=platform.python_version(),platform=platform.platform(),commands=[])
    def save():manifest.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    def run(name,arguments,expected=0):
        print("Ejecutando "+name,flush=True)
        started=time.perf_counter()
        completed=subprocess.run([sys.executable,"-X","utf8","-B",*map(str,arguments)],cwd=ROOT,
                                  env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1","PYTHONIOENCODING":"utf-8"},
                                  capture_output=True,text=True,encoding="utf-8")
        (out/(name+".txt")).write_text(completed.stdout+completed.stderr,encoding="utf-8")
        report["commands"].append(dict(name=name,arguments=list(map(str,arguments)),returncode=completed.returncode,
                                       expected_returncode=expected,elapsed_s=time.perf_counter()-started))
        save()
        if completed.returncode!=expected:raise RuntimeError(f"Falló {name}: consultar su log")
        return completed
    try:
        import mcoc_p2
        imported=Path(mcoc_p2.__file__).resolve()
        if imported.parent!=ROOT/"src/mcoc_p2":raise RuntimeError("Paquete importado desde otra carpeta")
        report["imported_solver"]=str(imported)
        report["packages"]={name:importlib.metadata.version(name) for name in
                             ("numpy","pytest","matplotlib","ifcopenshell","mcoc-p2")}
        baseline=json.loads((ROOT/"docs/E05_BASE_E04_INVENTARIO.json").read_text(encoding="utf-8"))
        inherited=[name for name in baseline["files"] if name.endswith(".py") and name.split("/")[0] in
                   ("src","tests","scripts","examples")]
        changed=[name for name in inherited if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=baseline["files"][name]["sha256"]]
        report["inherited_python_files_checked"]=len(inherited)
        report["inherited_python_files_changed"]=changed
        if changed:raise RuntimeError("Cambió código heredado sin justificación: "+str(changed))
        run("pip_check",["-m","pip","check"])
        run("pytest",["-m","pytest","tests","-q","-p","no:cacheprovider",f"--basetemp={out/'pytest_tmp'}",f"--junitxml={out/'pytest.xml'}"])
        suites=ET.parse(out/"pytest.xml").getroot()
        report["tests"]={key:sum(int(s.get(key,0)) for s in suites.iter("testsuite")) for key in
                         ("tests","failures","errors","skipped")}
        report["tests"]["elapsed_s"]=sum(float(s.get("time",0)) for s in suites.iter("testsuite"))
        if any(report["tests"][key] for key in ("failures","errors","skipped")):
            raise RuntimeError("Tests fallidos, con error u omitidos")
        run("listar",["examples/run_e05.py","--list"])
        run("battery",["examples/run_e05.py","--all","--config","configs/e05/lab.json","--output",out/"battery"])
        run("exact_3d_modificado",["examples/run_e05.py","--case","exact_3d","--shape",8,10,12,
            "--lengths",1.2,.9,1.6,"--k",3.1,"--rho",2300,"--cp",870,"--initial",18,
            "--amplitude",7,"--dt",20,"--t-end",3600,"--output",out/"exact_3d_modificado"])
        run("bordes_modificados",["examples/run_e05.py","--category","boundary","--dim",3,"--n",5,
            "--lengths",1.3,1.8,.7,"--face","z+","--flux",-135,"--initial",22,"--ambient",40,
            "--h",50,"--t-end",5400,"--output",out/"bordes_modificados"])
        run("fuente_negativa",["examples/run_e05.py","--case","source","--dim",1,"--n",7,
            "--q-dot",-1200,"--rho",2100,"--cp",1100,"--t-end",3700,"--output",out/"fuente_negativa"])
        run("adiabatico_heterogeneo",["examples/run_e05.py","--case","energy","--dim",1,"--n",11,
            "--heterogeneous","--lengths",1.7,"--amplitude",14,"--t-end",7200,"--output",out/"adiabatico_heterogeneo"])
        sweep=parameter_sweep()
        (out/"parameter_sweep.json").write_text(json.dumps(sweep,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
        if any(item["status"]!="PASS" for item in sweep):
            raise RuntimeError("Un cambio de parámetros no satisface sus criterios; consultar parameter_sweep.json")
        report["parameter_cases_passed"]=len(sweep)
        rejected=run("inestabilidad_esperada",["examples/run_e05.py","--case","exact_3d","--dt","1e20","--output",out/"inestable"],expected=2)
        if "cota" not in rejected.stdout:raise RuntimeError("El rechazo no fue por estabilidad")
        run("precision_fail_esperado",["examples/run_e05.py","--case","exact_2d","--n",3,
            "--atol-c","1e-12","--output",out/"precision_fail"],expected=1)
        if json.loads((out/"precision_fail/battery.json").read_text(encoding="utf-8"))["status"]!="FAIL":
            raise RuntimeError("La precisión insuficiente no se marcó FAIL")
        invalid=out/"unidades_invalidas.json"
        invalid.write_text('{"units":{"length":"mm"}}',encoding="utf-8")
        run("unidades_invalidas_esperadas",["examples/run_e05.py","--case","source","--config",invalid],expected=2)
        run("ifc_check",["scripts/check_ifc.py","geometry/foundation.ifc","--json",out/"ifc_check.json"])
        run("bonsai_heredado",["scripts/check_bonsai_evidence.py","--json",out/"bonsai_evidence.json"])
        report["status"]="passed"
    except BaseException:
        report["status"]="failed"
        raise
    finally:
        report["finished_utc"]=datetime.now(timezone.utc).isoformat()
        report["input_sha256"]={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                                for folder in ("src","tests","scripts","examples","configs","geometry")
                                for p in (ROOT/folder).rglob("*") if p.is_file() and p.suffix in (".py",".json",".ifc")}
        save()
    print(json.dumps({key:report[key] for key in ("status","tests","parameter_cases_passed")},indent=2))


if __name__=="__main__":
    main()
