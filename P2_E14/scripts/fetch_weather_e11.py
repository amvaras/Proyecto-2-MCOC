"""Adquirir snapshot nuevo; nunca actualizar uno existente."""
import argparse,json
from mcoc_p2.e11.weather import acquire,validate
from mcoc_p2.housekeeping import configure_runtime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--days',type=int,default=3)
    a=p.parse_args();folder=acquire(days=a.days)
    print(folder.relative_to(ROOT).as_posix());print(json.dumps(validate(folder).metadata,ensure_ascii=False,indent=2))
if __name__=='__main__':configure_runtime(ROOT);main()
