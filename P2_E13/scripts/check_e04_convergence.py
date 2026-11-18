"""Mide órdenes espacial y temporal por separado para el núcleo 2D/3D."""
import argparse
import json
from pathlib import Path
import numpy as np
from mcoc_p2 import CartesianGrid, CartesianSystem, Material, Dirichlet, solve_nd


def study(dim):
    m = Material(2.,2400.,900.)
    spatial = []
    for n in (6,12,24):
        s = CartesianSystem(CartesianGrid((1.,)*dim, (n,)*dim), m,
                            {a+b:Dirichlet(20) for a in "xyz"[:dim] for b in "-+"})
        mode = np.prod([np.sin(np.pi*x) for x in np.meshgrid(*s.grid.coordinates,indexing="ij")],axis=0)
        r = solve_nd(system=s,initial=20+10*mode,dt=5.,t_end=10000.,save_every=100000)
        error = float(np.max(abs(r.temperature[-1]-(20+10*mode*np.exp(-m.alpha*dim*np.pi**2*10000)))))
        spatial.append(dict(n=n,dx_m=1/n,dt_s=r.dt,error_C=error))
    temporal = []
    n=6
    s = CartesianSystem(CartesianGrid((1.,)*dim,(n,)*dim),m,
                        {a+b:Dirichlet(20) for a in "xyz"[:dim] for b in "-+"})
    mode=np.prod([np.sin(np.pi*x) for x in np.meshgrid(*s.grid.coordinates,indexing="ij")],axis=0)
    rate=4*m.alpha*n*n*dim*np.sin(np.pi/(2*n))**2
    for dt in (500.,250.,125.):
        r=solve_nd(system=s,initial=20+10*mode,dt=dt,t_end=50000.,save_every=100000)
        error=float(np.max(abs(r.temperature[-1]-(20+10*mode*np.exp(-rate*50000)))))
        temporal.append(dict(n=n,dt_s=r.dt,error_C=error))
    ratios_space=[a["error_C"]/b["error_C"] for a,b in zip(spatial,spatial[1:])]
    ratios_time=[a["error_C"]/b["error_C"] for a,b in zip(temporal,temporal[1:])]
    if not all(3.7<r<4.5 for r in ratios_space) or not all(1.98<r<2.05 for r in ratios_time):
        raise RuntimeError("Convergencia fuera de tolerancia")
    return dict(dimensions=dim,spatial=spatial,spatial_ratios=ratios_space,
                spatial_orders=np.log2(ratios_space).tolist(),temporal=temporal,
                temporal_ratios=ratios_time,temporal_orders=np.log2(ratios_time).tolist())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json",type=Path,default=Path("results/e04/convergence.json"))
    a=p.parse_args()
    report=dict(status="passed",studies=[study(d) for d in (2,3)])
    a.json.parent.mkdir(parents=True,exist_ok=True)
    a.json.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2))


if __name__=="__main__":
    main()
