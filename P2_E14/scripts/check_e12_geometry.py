"""Área IFC exterior independiente: restar contactos horizontales verificados."""
import numpy as np
from mcoc_p2.e11.pipeline import ROOT,write_json
from mcoc_p2.e07.ifc import read_pours
import json
def main():
    s=json.loads((ROOT/'results/e13/representative/summary.json').read_text(encoding='utf8'))
    solids,_=read_pours(ROOT/s['configuration']['ifc']);total=contact=0.;previous=None;rows=[]
    for solid in solids:
        tri=solid.mesh.tri;area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2
        bottom=np.all(abs(tri[:,:,2]-solid.mesh.low[2])<1e-8,axis=1);bottom_area=float(area[bottom].sum())
        if previous is not None:
            assert abs(previous.mesh.high[2]-solid.mesh.low[2])<1e-8 and previous.mesh.convex
            assert np.all(previous.mesh.classify(tri[bottom].reshape(-1,3))>=0)
            contact+=bottom_area
        total+=float(area.sum());rows.append(dict(id=solid.pour_id,closed_area_m2=float(area.sum()),bottom_area_m2=bottom_area));previous=solid
    reference=total-2*contact
    g=json.loads((ROOT/'results/e13/representative/geometry.json').read_text(encoding='utf8'));voxel=g['final_exterior']['area_m2']
    # Comprobación analítica separada para el octágono/frustums/pedestal docente.
    t=np.tan(np.pi/8);P=lambda d:8*d*t;A=lambda d:2*d*d*t
    slant=np.hypot(1.1,(18-12.5)/2)
    analytic=A(18)+P(18)*1.1+(P(18)+P(12.5))/2*slant+(P(12.5)+P(7))/2*slant+A(7)+np.pi*7
    assert abs(reference-analytic)<.01  # La circunferencia IFC está triangulada.
    report=dict(status='PASS',method='Suma de áreas triangulares cerradas menos dos veces las bases de vertidas superiores; contacto completo comprobado por elevación, convexidad y pertenencia de cada vértice inferior',
                solids=rows,internal_contact_area_m2=contact,IFC_external_area_m2=reference,analytic_external_area_m2=float(analytic),
                voxel_external_area_m2=voxel,relative_area_bias=voxel/reference-1,
                limitation='La frontera staircase tiene área sesgada: refinamiento de centros no certifica convergencia del área real ni exactitud de S25. No se aplicó corrección cut-cell.')
    write_json(ROOT/'results/verification/surface_geometry.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()

