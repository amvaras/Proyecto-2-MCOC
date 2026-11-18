"""Preparar, ejecutar/reanudar y agregar E14 local o desde Slurm."""
from pathlib import Path
import argparse,json,sys
from mcoc_p2.e11.pipeline import ROOT
from mcoc_p2.housekeeping import configure_runtime
from mcoc_p2.e14.io import read,write
from mcoc_p2.e14.workflow import prepare,run_local,execute_chunk,aggregate
def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('prepare');a.add_argument('--config',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--kind',choices=['mc','enumeration'],default='mc');a.add_argument('--chunk-size',type=int,default=4);a.add_argument('--cache',type=Path)
    a=sub.add_parser('run');a.add_argument('--manifest',type=Path,required=True);a.add_argument('--workers',type=int,default=2);a.add_argument('--resume',action='store_true');a.add_argument('--retry-failed',action='store_true');a.add_argument('--force-solve',action='store_true')
    a=sub.add_parser('chunk');a.add_argument('--manifest',type=Path,required=True);a.add_argument('--index',type=int,required=True);a.add_argument('--retry-failed',action='store_true')
    a=sub.add_parser('aggregate');a.add_argument('--manifest',type=Path,required=True)
    args=p.parse_args()
    if args.command=='prepare':
        r=prepare(read(args.config),args.output,kind=args.kind,chunk_size=args.chunk_size,cache=args.cache);print(json.dumps(dict(manifest=str(args.output/'manifest.json'),fingerprint=r['fingerprint'],chunks=len(r['chunks']),estimate=r['estimate']),indent=2));return
    if args.command=='run':
        def progress(s):print(f"{s['completed_chunks']}/{s['total_chunks']} chunks · {s['last_status']} · {s['elapsed_s']:.1f} s",flush=True)
        if not args.resume and (args.manifest.parent/'chunks').exists():raise ValueError('Resultados existentes: --resume exige revalidar huella y chunks')
        r=run_local(args.manifest,args.workers,force=args.force_solve,retry_failed=args.retry_failed,progress=progress)
    elif args.command=='chunk':r=execute_chunk(args.manifest,args.index,retry_failed=args.retry_failed)
    else:r=aggregate(args.manifest);write(args.manifest.parent/'summary.json',r,replace=True)
    print(json.dumps({k:v for k,v in r.items() if k not in ('entries',)},ensure_ascii=False,indent=2))
if __name__=='__main__':configure_runtime(ROOT);main()
