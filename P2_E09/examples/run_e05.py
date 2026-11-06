"""Batería E05: listar, seleccionar, configurar y comprobar casos científicos."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from mcoc_p2.verification_e05 import CASES, make_config, load_configuration, run_case


def plot_result(report, system, result, exact, output):
    if result is None:
        if "rows" not in report:
            return
        rows=report["rows"]
        steps=[row["spacing_m"][0] if report["case"]=="spatial" else row["effective_dt_s"] for row in rows]
        fig,ax=plt.subplots(figsize=(6,4),layout="constrained")
        ax.loglog(steps,[row["error_Linf_C"] for row in rows],"o-",label="error medido")
        ax.set(xlabel="dx [m]" if report["case"]=="spatial" else "dt [s]",ylabel="error L∞ [°C]",
               title=f"{report['dimension']}D · {report['case']} · órdenes {np.round(report['observed_orders'],3)}")
        ax.legend();ax.grid(alpha=.3)
        fig.savefig(output,dpi=140);plt.close(fig)
        return
    dim=report["dimension"]
    fig,axes=plt.subplots(2,2,figsize=(10,7),layout="constrained")
    initial,final=result.temperature[0],result.temperature[-1]
    if dim==1:
        x=system.grid.coordinates[0]
        axes[0,0].plot(x,initial,label="inicial")
        axes[0,0].plot(x,final,"o-",ms=3,label="final")
        if exact is not None:axes[0,0].plot(x,exact,"k--",label="exacta PDE")
        axes[0,0].set(xlabel="x [m]",ylabel="T [°C]",title="Valores en centros de celda")
        axes[0,0].legend()
        if exact is not None:
            axes[0,1].plot(x,final-exact)
            axes[0,1].set(xlabel="x [m]",ylabel="error [°C]",title="Error final")
        else:
            axes[0,1].plot(x,final-initial)
            axes[0,1].set(xlabel="x [m]",ylabel="ΔT [°C]",title="Cambio térmico")
        energies=[system.energy(t,report["config"]["initial_C"]) for t in result.temperature]
        axes[1,0].plot(result.times,np.array(energies)-energies[0])
        axes[1,0].set(xlabel="tiempo [s]",ylabel="ΔE [J]",title="Cambio de energía sensible")
    else:
        if dim==2:
            fields=[(initial,(0,1),"Inicial"),(final,(0,1),"Final")]
            axes[1,0].plot(system.grid.coordinates[0],final[:,system.grid.shape[1]//2])
            axes[1,0].set(xlabel="x [m]",ylabel="T [°C]",title="Fila central final")
        else:
            ix,iy,iz=[n//2 for n in system.grid.shape]
            fields=[(final[:,:,iz],(0,1),f"z={system.grid.coordinates[2][iz]:.3g} m"),
                    (final[:,iy,:],(0,2),f"y={system.grid.coordinates[1][iy]:.3g} m"),
                    (final[ix,:,:],(1,2),f"x={system.grid.coordinates[0][ix]:.3g} m")]
        low=min(float(initial.min()),float(final.min()))
        high=max(float(initial.max()),float(final.max()))
        if high-low<1e-8:low-=.5;high+=.5
        for ax,(field,(i,j),title) in zip(axes.flat,fields):
            im=ax.imshow(field.T,origin="lower",extent=(0,system.grid.lengths[i],0,system.grid.lengths[j]),
                         aspect="equal",cmap="inferno",vmin=low,vmax=high)
            ax.set(xlabel="xyz"[i]+" [m]",ylabel="xyz"[j]+" [m]",title=title)
            fig.colorbar(im,ax=ax,label="T [°C]",shrink=.8)
    flat=result.temperature.reshape((len(result.times),-1))
    axes[1,1].plot(result.times,flat.min(axis=1),label="mínimo")
    axes[1,1].plot(result.times,flat.max(axis=1),label="máximo")
    axes[1,1].set(xlabel="tiempo [s]",ylabel="T [°C]",title="Evolución de centros")
    axes[1,1].legend()
    fig.suptitle(f"E05 · {report['case']} · {report['status']} · dt={result.dt:.4g} s · caja ideal")
    fig.savefig(output,dpi=140);plt.close(fig)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    selection=parser.add_mutually_exclusive_group()
    selection.add_argument("--list",action="store_true")
    selection.add_argument("--case",choices=CASES)
    selection.add_argument("--category",choices=sorted(set(CASES.values())))
    selection.add_argument("--all",action="store_true")
    parser.add_argument("--config",type=Path)
    parser.add_argument("--output",type=Path)
    parser.add_argument("--dim",type=int,choices=(1,2,3),help="dimensión de casos no fijados por su nombre")
    parser.add_argument("--n",type=int,help="celdas por eje; reemplaza shape de la configuración")
    parser.add_argument("--shape",type=int,nargs="+",help="nx [ny nz], centros de celda")
    parser.add_argument("--lengths",type=float,nargs="+",help="Lx [Ly Lz] en m; un valor se repite")
    for flag in ("k","rho","cp","initial","amplitude","ambient","h","q-dot","flux","dt","t-end","atol-c","energy-rtol"):
        parser.add_argument("--"+flag,type=float)
    parser.add_argument("--face",choices=("x-","x+","y-","y+","z-","z+"))
    parser.add_argument("--heterogeneous",action="store_true",default=None,help="solo energy")
    args=parser.parse_args(argv)
    if args.list or not (args.case or args.category or args.all):
        for case,category in CASES.items():print(f"{case:12} {category}")
        return 0
    cases=[args.case] if args.case else [case for case,category in CASES.items() if args.all or category==args.category]
    try:
        document=load_configuration(args.config) if args.config else {}
        configs={}
        names={"dim":"dimension","lengths":"lengths_m","initial":"initial_C","amplitude":"amplitude_C",
               "ambient":"ambient_C","dt":"dt_s","t_end":"t_end_s","atol_c":"atol_C"}
        parameters=("dim","n","shape","lengths","k","rho","cp","initial","amplitude","ambient","h",
                    "q_dot","flux","dt","t_end","atol_c","energy_rtol","face","heterogeneous")
        for case in cases:
            values={**document.get("defaults",{}),**document.get("cases",{}).get(case,{})}
            for key in parameters:
                value=getattr(args,key)
                if value is not None:
                    if key=="dim" and case.startswith("exact_"):continue
                    values[names.get(key,key)]=value
            if args.n is not None and args.shape is None:values["shape"]=None
            configs[case]=make_config(case,values)
        output=args.output or Path("results/e05")/datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        if output.exists() and (not output.is_dir() or any(output.iterdir())):
            raise ValueError("El destino contiene archivos; elegir otra carpeta para conservar resultados")
        output.mkdir(parents=True,exist_ok=True)
        reports=[]
        for case in cases:
            report,system,result,exact=run_case(case,configs[case])
            folder=output/case;folder.mkdir()
            (folder/"summary.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
            if result is not None:
                arrays=dict(times_s=result.times,temperature_C=result.temperature)
                arrays.update({axis+"_m":coord for axis,coord in zip("xyz",system.grid.coordinates)})
                if exact is not None:arrays["exact_final_C"]=exact
                np.savez_compressed(folder/"solution.npz",**arrays)
            plot_result(report,system,result,exact,folder/"result.png")
            reports.append(report)
            print(f"{report['status']:4} {case}: "+", ".join(
                f"{c['name']}={c['measured']:.3g} (tolerancia {c['tolerance']:.3g})" for c in report["checks"]),flush=True)
        summary=dict(status="PASS" if all(r["status"]=="PASS" for r in reports) else "FAIL",cases=reports)
        (output/"battery.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
        print(f"Resultado: {summary['status']}; archivos en {output}")
        return 0 if summary["status"]=="PASS" else 1
    except (ValueError,TypeError,FloatingPointError,OverflowError,OSError) as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__=="__main__":
    raise SystemExit(main())
