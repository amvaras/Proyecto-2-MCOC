"""Una representación geométrica por IfcFooting; salida mundial SI en metros."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import numpy as np
import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit
from .geometry import ClosedMesh


@dataclass
class PourSolid:
    pour_id:int
    guid:str
    name:str
    mesh:ClosedMesh
    properties:dict
    placement_si:np.ndarray
    geometry_id:str='synthetic'

    def summary(self):
        return dict(vertida_id=self.pour_id,guid=self.guid,name=self.name,properties=self.properties,
                    placement_world_m=self.placement_si.tolist(),geometry_id=self.geometry_id,
                    vertices=len(self.mesh.vertices),triangles=len(self.mesh.triangles),
                    bbox_min_m=self.mesh.low.tolist(),bbox_max_m=self.mesh.high.tolist(),
                    volume_mesh_m3=self.mesh.volume,convex=self.mesh.convex,
                    orientation_reversed=self.mesh.orientation_reversed)


def read_pours(path):
    model=ifcopenshell.open(str(path))
    projects=model.by_type('IfcProject')
    if len(projects)!=1 or projects[0].UnitsInContext is None or not any(getattr(u,'UnitType',None)=='LENGTHUNIT' for u in projects[0].UnitsInContext.Units):
        raise ValueError('IFC debe declarar unidad de longitud')
    scale=ifcopenshell.util.unit.calculate_unit_scale(model)
    if not np.isfinite(scale) or scale<=0:raise ValueError('Unidades IFC inválidas')
    settings=ifcopenshell.geom.settings();settings.set('use-world-coords',True)
    settings.set('convert-back-units',False)
    solids=[]
    for el in model.by_type('IfcFooting'):
        props=ifcopenshell.util.element.get_psets(el).get('UANDES_HormigonMasivo',{})
        identifier=props.get('VertidaID')
        if isinstance(identifier,bool) or not isinstance(identifier,int) or identifier<=0:raise ValueError('VertidaID debe ser entero positivo')
        shape=ifcopenshell.geom.create_shape(settings,el)
        # create_shape aplica placements/mapped items y convierte a SI. No duplicar transformación.
        mesh=ClosedMesh(np.asarray(shape.geometry.verts).reshape(-1,3),np.asarray(shape.geometry.faces,dtype=int).reshape(-1,3))
        placement=ifcopenshell.util.placement.get_local_placement(el.ObjectPlacement).copy();placement[:3,3]*=scale
        props={k:v for k,v in props.items() if k!='id'}
        for name,z in (('ZInferior_m',mesh.low[2]),('ZSuperior_m',mesh.high[2])):
            if name in props and not np.isclose(props[name],z,atol=1e-7,rtol=0):raise ValueError(name+' no coincide con elevación global SI')
        solids.append(PourSolid(identifier,el.GlobalId,el.Name,mesh,props,placement,str(shape.geometry.id)))
    if not solids:raise ValueError('IFC sin IfcFooting')
    if len({p.pour_id for p in solids})!=len(solids) or len({p.guid for p in solids})!=len(solids):raise ValueError('Identificadores IFC/VertidaID duplicados')
    return sorted(solids,key=lambda p:p.pour_id),dict(schema=model.schema,ifc_unit_to_m=scale,
               coordinates='world SI m',source_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())
