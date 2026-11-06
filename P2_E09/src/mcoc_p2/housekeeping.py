"""Finalización conservadora para los ejecutores, sin tocar datos científicos."""
import atexit
import importlib.util
import os
from pathlib import Path
import warnings


def configure_runtime(root):
    root=Path(root).resolve()
    os.environ.setdefault('MPLCONFIGDIR',str(root/'.mplconfig'))
    def finish():
        script=root/'scripts/clean_project.py'
        if not script.is_file():return
        try:
            spec=importlib.util.spec_from_file_location('mcoc_safe_cleanup',script)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            module.cleanup_caches(root)
        except (OSError,ValueError) as exc:
            warnings.warn('Se conservaron caches por seguridad: '+str(exc))
    atexit.register(finish)
