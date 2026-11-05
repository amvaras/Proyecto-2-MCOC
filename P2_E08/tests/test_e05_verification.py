"""E05: controles configurables, referencias independientes y pruebas negativas.

La física básica y las seis caras/signos del núcleo siguen en test_thermal_nd;
estos casos cubren la interfaz de laboratorio y parámetros no cúbicos nuevos.
"""
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
from numpy.testing import assert_allclose

from mcoc_p2 import CartesianGrid, CartesianSystem, Material, Robin
from mcoc_p2.verification_e05 import make_config, load_configuration, run_case

pytestmark=pytest.mark.e05
ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def evidence(record_property):
    def save(report):
        record_property("e05_scientific_report",json.dumps(report,ensure_ascii=False,allow_nan=False))
    return save


@pytest.mark.parametrize("dim,shape,lengths",[(1,(17,),(.8,)),(2,(10,14),(1.3,.7)),(3,(6,8,10),(1.1,.8,1.7))])
def test_configured_exact_modes_use_physical_centers_and_faces(dim,shape,lengths,evidence):
    cfg=make_config(f"exact_{dim}d",dict(shape=shape,lengths_m=lengths,k=3.1,rho=2350.,cp=880.,
                                        initial_C=18.,amplitude_C=8.,t_end_s=3000.))
    report,system,result,reference=run_case(f"exact_{dim}d",cfg)
    evidence(report)
    coordinates=np.meshgrid(*system.grid.coordinates,indexing="ij")
    mode=np.ones(shape)
    for coordinate,length in zip(coordinates,lengths):mode*=np.sin(np.pi*coordinate/length)
    rate=3.1/(2350*880)*sum((np.pi/L)**2 for L in lengths)
    expected=18+8*mode*np.exp(-rate*3000)
    assert_allclose(reference,expected,rtol=0,atol=2e-14)
    assert_allclose(result.temperature[0],18+8*mode,rtol=0,atol=2e-14)
    assert np.all(result.temperature[0]>18)  # Los centros NO son las caras Dirichlet.
    assert report["status"]=="PASS",report["checks"]
    assert report["error_Linf_C"]<cfg.atol_C
    assert report["error_L2_rms_C"]<=report["error_Linf_C"]
    assert_allclose(report["fourier_per_axis"],[3.1/(2350*880)*result.dt/d**2 for d in system.grid.spacing])


@pytest.mark.parametrize("dim",[1,2,3])
@pytest.mark.parametrize("source",[-1500.,0.,1500.])
def test_configured_source_signed_power_volume_and_temperature(dim,source,evidence):
    lengths=tuple(1.+.4*i for i in range(dim))
    cfg=make_config("source",dict(dimension=dim,n=5,lengths_m=lengths,q_dot=source,
                                  rho=2200.,cp=1000.,t_end_s=5000.))
    report,system,result,_=run_case("source",cfg)
    evidence(report)
    assert report["status"]=="PASS"
    expected=20+source*5000/(2200*1000)
    assert_allclose(result.temperature[-1],expected,rtol=0,atol=2e-12)
    expected_energy=source*np.prod(lengths)*5000
    assert_allclose(system.energy(result.temperature[-1],20),expected_energy,rtol=1e-12,atol=1e-7)


@pytest.mark.parametrize("dim",[1,2,3])
def test_configured_heterogeneous_energy_is_not_constant_temperature(dim,evidence):
    cfg=make_config("energy",dict(dimension=dim,n=5,heterogeneous=True,
                                  lengths_m=tuple(1+.2*i for i in range(dim)),t_end_s=20000.))
    report,system,result,_=run_case("energy",cfg)
    evidence(report)
    assert report["status"]=="PASS"
    energies=np.array([system.energy(t,20) for t in result.temperature])
    assert_allclose(energies,energies[0],rtol=5e-13,atol=1e-6)
    assert np.ptp(result.temperature[-1])<np.ptp(result.temperature[0])
    assert not np.array_equal(result.temperature[0],result.temperature[-1])


@pytest.mark.parametrize("dim,face,flux",[(1,"x-",-73.),(2,"y+",83.),(3,"z-",-97.)])
def test_configured_neumann_on_different_axes_and_areas(dim,face,flux,evidence):
    lengths=tuple(1.2+.5*i for i in range(dim))
    report,system,result,_=run_case("neumann",make_config("neumann",dict(
        dimension=dim,n=5,lengths_m=lengths,face=face,flux=flux,t_end_s=1234.)))
    evidence(report)
    assert report["status"]=="PASS"
    axis="xyz".index(face[0])
    area=np.prod([L for i,L in enumerate(lengths) if i!=axis])
    assert_allclose(system.energy(result.temperature[-1],20),-flux*area*1234,rtol=1e-12,atol=1e-7)


@pytest.mark.parametrize("h",[0.,12.,1200.])
@pytest.mark.parametrize("ambient",[10.,40.])
def test_configured_robin_heating_cooling_zero_h_and_balance(h,ambient,evidence):
    cfg=make_config("robin",dict(dimension=3,shape=(4,5,6),lengths_m=(1.,1.4,2.),
                                 h=h,ambient_C=ambient,initial_C=20.,t_end_s=5000.))
    report,system,result,_=run_case("robin",cfg)
    evidence(report)
    assert report["status"]=="PASS",report["checks"]
    energy=system.energy(result.temperature[-1],20)
    if h==0:assert_allclose(result.temperature,20.,rtol=0,atol=0)
    else:assert energy*(ambient-20)>0


def test_robin_corner_adds_three_distinct_face_powers():
    grid=CartesianGrid((1.,1.5,2.),(4,5,6))
    h,k,temperature,ambient=17.,2.3,50.,20.
    system=CartesianSystem(grid,Material(k,2300,910),{a+"-":Robin(h,ambient) for a in "xyz"})
    expected=0.
    for axis,dx in enumerate(grid.spacing):
        area=np.prod([d for i,d in enumerate(grid.spacing) if i!=axis])
        expected-=area*(temperature-ambient)/(dx/(2*k)+1/h)
    assert_allclose(system.power(temperature)[0,0,0],expected,rtol=2e-15)


def test_robin_sensitivity_to_h_is_real_and_saturates_conductively():
    mean=[]
    for h in (1.,10.,1000.):
        report,_,result,_=run_case("robin",make_config("robin",dict(
            dimension=1,n=12,h=h,initial_C=50,ambient_C=20,t_end_s=20000)))
        assert report["status"]=="PASS"
        mean.append(result.temperature[-1].mean())
    assert mean[0]>mean[1]>mean[2]>20


@pytest.mark.parametrize("dim",[1,2,3])
def test_robin_stable_near_limit_and_rejects_excess_for_configured_h(dim):
    cfg=make_config("robin",dict(dimension=dim,n=5,h=300.,t_end_s=1000.))
    _,system,_,_=run_case("robin",cfg)
    values={"dimension":dim,"n":5,"h":300.,"t_end_s":1000.,"dt_s":.99*system.stable_dt}
    assert run_case("robin",make_config("robin",values))[0]["status"]=="PASS"
    values["dt_s"]=1.01*system.stable_dt
    with pytest.raises(ValueError,match="cota"):run_case("robin",make_config("robin",values))


@pytest.mark.parametrize("dim",[1,2,3])
@pytest.mark.parametrize("case",["spatial","temporal"])
def test_configurable_convergence_separates_space_from_time(case,dim,evidence):
    report,*_=run_case(case,make_config(case,dict(dimension=dim,k=.8,rho=2000.,cp=750.,
                        lengths_m=tuple(1.3-.2*i for i in range(dim)),t_end_s=8000.,amplitude_C=6.)))
    evidence(report)
    assert report["status"]=="PASS",report
    assert all(np.isfinite(report["observed_orders"]))


def test_accuracy_failure_is_not_reported_as_pass():
    report,*_=run_case("exact_2d",make_config("exact_2d",dict(n=3,atol_C=1e-12,t_end_s=10000.)))
    assert report["status"]=="FAIL"
    assert any(not c["passed"] for c in report["checks"])


def test_refinement_respects_changed_shape_and_effective_dt():
    spatial,*_=run_case("spatial",make_config("spatial",dict(dimension=2,shape=(5,7),t_end_s=6000.)))
    assert [row["shape"] for row in spatial["rows"]]==[(5,7),(10,14),(20,28)]
    temporal,*_=run_case("temporal",make_config("temporal",dict(dimension=1,n=9,k=.5,t_end_s=100.)))
    assert [row["shape"] for row in temporal["rows"]]==[(9,),(9,),(9,)]
    assert all(a["effective_dt_s"]>b["effective_dt_s"] for a,b in zip(temporal["rows"],temporal["rows"][1:]))
    assert temporal["status"]=="PASS"
    with pytest.raises(ValueError,match="malla fina"):
        run_case("spatial",make_config("spatial",dict(dimension=3,n=64)))


@pytest.mark.parametrize("values",[
    {"k":0},{"rho":-1},{"cp":np.inf},{"q_dot":np.nan},{"h":-1},
    {"n":1},{"n":True},{"shape":(3,4,5)},{"lengths_m":(1.,2.,3.)},
    {"t_end_s":0},{"dt_s":-1},{"initial_C":1+2j},{"face":"z+"},
    {"energy_rtol":-1},{"unknown_parameter":4},
])
def test_invalid_configurations_are_rejected(values):
    with pytest.raises((ValueError,TypeError)):
        config=make_config("source",values)
        run_case("source",config)


def test_semantic_configuration_rejects_vacuous_and_incompatible_references():
    with pytest.raises(ValueError,match="amplitud"):make_config("exact_2d",dict(amplitude_C=0))
    with pytest.raises(ValueError,match="homogeneas"):make_config("exact_3d",dict(heterogeneous=True))
    with pytest.raises(ValueError,match="dimension"):make_config("exact_1d",dict(dimension=3))


@pytest.mark.parametrize("content",["{",'[]','{"units":{"length":"mm"}}',
                                      '{"units":{"q_dot":"W/m^2"}}',
                                      '{"defaults":{"unknown":2}}','{"cases":{"missing":{}}}'])
def test_config_file_syntax_units_and_schema_errors(tmp_path,content):
    path=tmp_path/"invalid.json";path.write_text(content,encoding="utf-8")
    with pytest.raises(ValueError):load_configuration(path)


def test_config_file_missing_and_utf8_bom(tmp_path):
    with pytest.raises(ValueError,match="leer"):load_configuration(tmp_path/"absent.json")
    path=tmp_path/"valid.json";path.write_text('{"defaults":{"n":5}}',encoding="utf-8-sig")
    assert load_configuration(path)["defaults"]["n"]==5


def test_cli_lists_changes_parameters_and_preserves_existing_results(tmp_path):
    command=[sys.executable,"-X","utf8","-B",str(ROOT/"examples/run_e05.py")]
    listing=subprocess.run(command+["--list"],capture_output=True,text=True,encoding="utf-8")
    assert listing.returncode==0 and "exact_3d" in listing.stdout and "robin" in listing.stdout
    path=tmp_path/"custom.json"
    path.write_text(json.dumps({"defaults":{"n":4,"rho":2200.,"cp":1000.},
                               "cases":{"source":{"dimension":3,"lengths_m":[1.,1.5,2.]}}}),encoding="utf-8")
    output=tmp_path/"good"
    args=["--case","source","--config",str(path),"--q-dot","-1500","--t-end","1234","--output",str(output)]
    good=subprocess.run(command+args,capture_output=True,text=True,encoding="utf-8")
    assert good.returncode==0,good.stdout+good.stderr
    report=json.loads((output/"source/summary.json").read_text(encoding="utf-8"))
    assert report["config"]["q_dot"]==-1500 and report["dimension"]==3
    data=np.load(output/"source/solution.npz")
    assert_allclose(data["temperature_C"][-1],20-1500*1234/(2200*1000),atol=1e-12,rtol=0)
    original=(output/"battery.json").read_bytes()
    again=subprocess.run(command+args,capture_output=True)
    assert again.returncode==2 and (output/"battery.json").read_bytes()==original
    bad=subprocess.run(command+["--case","exact_2d","--dt","1e20","--output",str(tmp_path/"unstable")],capture_output=True)
    assert bad.returncode==2 and b"cota" in bad.stdout
    failed=subprocess.run(command+["--case","exact_2d","--n","3","--atol-c","1e-12","--output",str(tmp_path/"fail")],capture_output=True)
    assert failed.returncode==1
    assert json.loads((tmp_path/"fail/battery.json").read_text())["status"]=="FAIL"
