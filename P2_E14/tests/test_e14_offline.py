"""Verificación de resultados guardados: ningún solve térmico nuevo."""
import importlib.util,socket
from pathlib import Path
import pytest
from mcoc_p2.e14.io import ROOT

spec=importlib.util.spec_from_file_location('e14_offline',ROOT/'scripts/verify_e14_offline.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

def test_offline_audit_checks_all_cases_sources_and_tables_without_solver():
    with audit.offline_readonly():p,r=audit.inspect(fields=False)
    assert r['unique_cases_checked']==192 and r['new_thermal_simulations']==0
    assert len({x['physics_key'] for x in p['case_index']})==192
    assert len(p['plans'])==8 and not any(p['feasible'] for p in p['plans'])
    assert next(p for p in p['plans'] if p['plan']=='curado_frio5')['Pf_exact']==.85
    assert r['curves_checked']==8 and r['climate_histories_checked']==3 and r['figures_checked']==15

def test_offline_guard_rejects_connections_and_actual_solver_entry_points():
    from mcoc_p2.e14.model import Model
    from mcoc_p2.e08.solver import simulate
    import mcoc_p2.e08.solver as solver
    original=solver.simulate
    with audit.offline_readonly():
        with socket.socket() as s:
            with pytest.raises(RuntimeError,match='red bloqueada'):s.connect(('203.0.113.1',443))
        with pytest.raises(RuntimeError,match='simulación prohibida'):solver.simulate(None,None)
        with pytest.raises(RuntimeError,match='simulación prohibida'):Model().evaluate(None,None)
    assert solver.simulate is original

def test_inventory_rejects_altered_artifact_and_duplicate_path(tmp_path):
    p=tmp_path/'known.txt';p.write_bytes(b'known')
    row=dict(path=p.relative_to(ROOT).as_posix(),bytes=5,sha256=audit.sha(p));audit.check_inventory([row])
    p.write_bytes(b'other')
    with pytest.raises(ValueError,match='cambiado'):audit.check_inventory([row])
    with pytest.raises(ValueError,match='duplicadas'):audit.check_inventory([row,row])
