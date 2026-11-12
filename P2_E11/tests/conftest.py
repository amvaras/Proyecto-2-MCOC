"""Temporales propios dentro de la entrega incluso al ejecutar pytest directamente."""
from pathlib import Path
import os
import shutil
import sys
import uuid
from mcoc_p2.housekeeping import configure_runtime

ROOT=Path(__file__).resolve().parents[1]


def pytest_configure(config):
    sys.dont_write_bytecode=True
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    configure_runtime(ROOT)
    if config.option.basetemp is not None:return
    work=ROOT/'.runtime'/('pytest-'+uuid.uuid4().hex[:8])
    work.mkdir(parents=True);(work/'.owned').write_text('pytest',encoding='utf-8')
    config.option.basetemp=str(work/'data')
    config._mcoc_owned_work=work


def pytest_unconfigure(config):
    work=getattr(config,'_mcoc_owned_work',None)
    if work is None:return
    if work.parent==ROOT/'.runtime' and (work/'.owned').read_text(encoding='utf-8')=='pytest':
        shutil.rmtree(work)
        try:work.parent.rmdir()
        except OSError:pass
