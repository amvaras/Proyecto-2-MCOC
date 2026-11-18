"""Un proceso web, chunks de un input y cancelación al finalizar el input actual."""
from pathlib import Path
import argparse
from mcoc_p2.e11.pipeline import ROOT
from mcoc_p2.e14.io import read
from mcoc_p2.e14.workflow import prepare,run_local
from mcoc_p2.housekeeping import configure_runtime
def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--kind',choices=['mc','enumeration'],required=True);p.add_argument('--cancel',type=Path,required=True);p.add_argument('--resume',action='store_true');a=p.parse_args()
    if a.cancel.exists():raise SystemExit(2)
    if not a.resume or not (a.output/'manifest.json').exists():prepare(read(a.config),a.output,kind=a.kind,chunk_size=1)
    def callback(status):
        print(status,flush=True)
        if a.cancel.exists():raise InterruptedError('Cancelación cooperativa')
    try:run_local(a.output/'manifest.json',1,progress=callback,retry_failed=a.resume)
    except InterruptedError:raise SystemExit(2)
if __name__=='__main__':configure_runtime(ROOT);main()
