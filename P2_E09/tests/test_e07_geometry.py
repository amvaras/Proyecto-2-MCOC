from pathlib import Path
import numpy as np
import pytest
import ifcopenshell
import ifcopenshell.util.unit
from ifcopenshell.api import geometry
from mcoc_p2.e07.geometry import ClosedMesh
from mcoc_p2.e07.ifc import read_pours
from mcoc_p2.e07.voxel import VoxelGrid,voxelize
from e07_helpers import cube,solid

ROOT=Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('method',['auto','winding'])
def test_cube_boundary_faces_edges_vertices_and_outside(method):
    mesh=cube();points=np.array([[.5,.5,.5],[0,.2,.4],[0,0,.4],[0,0,0],[1,1,1],[-.001,.2,.4],[1.1,.5,.5]])
    np.testing.assert_array_equal(mesh.classify(points,method=method),[1,0,0,0,0,-1,-1])
    assert mesh.volume==pytest.approx(1)


def test_concave_mesh_winding_rejects_point_inside_bounding_box():
    ring=np.array([(0,0),(2,0),(2,1),(1,1),(1,2),(0,2)],float)
    v=np.vstack((np.column_stack((ring,np.zeros(6))),np.column_stack((ring,np.ones(6)))))
    top=np.array([(0,1,3),(1,2,3),(0,3,5),(3,4,5)])
    faces=[*top[:,::-1],*(top+6)]
    for i in range(6):
        j=(i+1)%6;faces.extend([(i,j,j+6),(i,j+6,i+6)])
    mesh=ClosedMesh(v,np.array(faces));assert not mesh.convex;assert mesh.volume==pytest.approx(3)
    np.testing.assert_array_equal(mesh.classify([[.5,1.5,.5],[1.5,.5,.5],[1.5,1.5,.5],[1,1,.5],[2,1,1]]),[1,1,-1,0,0])


def test_orientation_translation_and_scale_do_not_change_membership():
    original=cube();theta=.43;r=np.array([[np.cos(theta),-np.sin(theta),0],[np.sin(theta),np.cos(theta),0],[0,0,1]])
    mesh=ClosedMesh(original.vertices@r.T*2+[1000,-2000,7],original.triangles[:,::-1])
    assert mesh.orientation_reversed;assert mesh.volume==pytest.approx(8)
    points=np.array([[.5,.5,.5],[2,2,2]])@r.T*2+[1000,-2000,7]
    np.testing.assert_array_equal(mesh.classify(points),[1,-1])


@pytest.mark.parametrize('defect',['open','flipped','duplicate','degenerate','nan'])
def test_invalid_mesh_is_rejected(defect):
    m=cube();v=m.vertices.copy();f=m.triangles.copy()
    if defect=='open':f=f[:-1]
    elif defect=='flipped':f[0]=f[0,::-1]
    elif defect=='duplicate':f=np.vstack((f,f[0]))
    elif defect=='degenerate':v[1]=v[0]
    else:v[0,0]=np.nan
    with pytest.raises(ValueError):ClosedMesh(v,f)


@pytest.fixture(scope='module')
def real():return read_pours(ROOT/'geometry/foundation.ifc')


def test_real_ifc_identifiers_geometry_and_independent_volume(real):
    solids,meta=real
    assert meta['ifc_unit_to_m']==1 and meta['schema']=='IFC4'
    assert [s.pour_id for s in solids]==[1,2,3,4,5] and len({s.guid for s in solids})==5
    assert [s.name for s in solids]==[f'Vertida_{i:02}' for i in range(1,6)]
    assert all(s.mesh.convex for s in solids)
    exact=2*8*9**2*np.tan(np.pi/8)*.55+8*np.tan(np.pi/8)*1.1/3*((9**2+9*6.25+6.25**2)+(6.25**2+6.25*3.5+3.5**2))+np.pi*3.5**2
    assert sum(s.mesh.volume for s in solids)==pytest.approx(exact,rel=2e-5)
    assert np.array([s.mesh.low[2] for s in solids])==pytest.approx([0,.55,1.1,2.2,3.3])


def test_ifc_millimetres_are_converted_once(tmp_path,real):
    model=ifcopenshell.open(str(ROOT/'geometry/foundation.ifc'))
    converted=ifcopenshell.util.unit.convert_file_length_units(model,'MILLIMETRE')
    path=tmp_path/'mm.ifc';converted.write(str(path));solids,meta=read_pours(path)
    assert meta['ifc_unit_to_m']==.001
    for a,b in zip(solids,real[0]):
        assert a.mesh.volume==pytest.approx(b.mesh.volume,rel=1e-10)
        np.testing.assert_allclose(a.mesh.low,b.mesh.low,atol=1e-10)


def test_ifc_rotated_translated_placement_is_not_applied_twice(tmp_path):
    model=ifcopenshell.open(str(ROOT/'geometry/foundation.ifc'));el=next(e for e in model.by_type('IfcFooting') if e.Name=='Vertida_01')
    theta=.4;m=np.eye(4);m[:2,:2]=[[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]];m[:2,3]=[30,-20]
    geometry.edit_object_placement(model,product=el,matrix=m,is_si=True)
    path=tmp_path/'placed.ifc';model.write(str(path));s=read_pours(path)[0][0]
    np.testing.assert_array_equal(s.mesh.classify([[30,-20,.275],[0,0,.275]]),[1,-1])
    np.testing.assert_allclose(s.placement_si,m,atol=1e-10)


def test_voxel_cube_and_rectangular_steps_have_exact_known_volume():
    result=voxelize([solid(cube())],(.25,.2,.1),margin=0.)
    assert result.occupation_mask.sum()*result.grid.cell_volume==pytest.approx(1)
    assert result.report()['by_pour'][0]['volume_voxel_m3']==pytest.approx(1)
    assert np.array_equal(result.occupation_mask,result.vertida_id>0)


def test_boundary_centres_choose_lowest_id_and_order_is_invariant():
    a=solid(cube((0,0,0),(1,1,1)),1);b=solid(cube((0,0,1),(1,1,2)),2)
    x=voxelize([b,a],(1,1,2/3));y=voxelize([a,b],(1,1,2/3))
    np.testing.assert_array_equal(x.vertida_id,y.vertida_id)
    assert x.vertida_id[0,0,1]==1 and x.boundary_ties==1


def test_overlapping_solid_interiors_are_rejected():
    with pytest.raises(ValueError,match='Solapamiento'):voxelize([solid(cube(),1),solid(cube(),2)],.25)


@pytest.mark.parametrize('spacing',[0,-1,float('nan'),float('inf'),1e-5])
def test_resolution_guard_before_allocation(spacing):
    with pytest.raises(ValueError):voxelize([solid(cube())],spacing)


def test_real_volume_and_each_pour_change_with_resolution(real):
    reports=[voxelize(real[0],h).report() for h in (.6,.3,.15)]
    assert len({r['occupied_cells'] for r in reports})==3
    assert reports[-1]['relative_error']<.05
    assert all(r['cells']>0 and r['relative_error']<.2 for r in reports[-1]['by_pour'])
    # Ninguna suposición de convergencia monótona ni de orden dos para staircase.
    assert reports[-1]['grid_cells']<2_000_000


def test_box_convention_matches_existing_cartesian_grid():
    grid=VoxelGrid((10.,20.,30.),(.2,.3,.4),(3,4,5));old=grid.box_grid()
    assert old.cell_volume==pytest.approx(grid.cell_volume)
    for axis in range(3):np.testing.assert_allclose(grid.coordinates[axis],old.coordinates[axis]+grid.origin[axis])


@pytest.mark.parametrize('defect',['units','duplicate_id','elevation'])
def test_ifc_inconsistent_metadata_is_rejected(tmp_path,defect):
    from ifcopenshell.api import pset
    model=ifcopenshell.open(str(ROOT/'geometry/foundation.ifc'))
    if defect=='units':model.by_type('IfcProject')[0].UnitsInContext=None
    else:
        el=next(e for e in model.by_type('IfcFooting') if e.Name=='Vertida_02')
        prop=next(r.RelatingPropertyDefinition for r in el.IsDefinedBy if r.is_a('IfcRelDefinesByProperties') and r.RelatingPropertyDefinition.Name=='UANDES_HormigonMasivo')
        pset.edit_pset(model,pset=prop,properties={'VertidaID':1} if defect=='duplicate_id' else {'ZInferior_m':999.})
    path=tmp_path/'bad.ifc';model.write(str(path))
    with pytest.raises(ValueError):read_pours(path)
