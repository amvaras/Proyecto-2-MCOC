"""VTK ImageData: celdas XYZ, x varía más rápido (flatten F), unidades explícitas."""
import hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import pyvista as pv


def image_data(ids,origin,spacing,temperature,active):
    ids=np.asarray(ids);T=np.asarray(temperature);active=np.asarray(active,dtype=bool)
    if ids.shape!=T.shape or ids.shape!=active.shape:raise ValueError('Campos XYZ con igual shape')
    if not np.isfinite(T[active]).all() or np.any(active&(ids==0)):raise ValueError('Máscara o temperatura activa inválida')
    grid=pv.ImageData(dimensions=tuple(np.array(ids.shape)+1),spacing=tuple(spacing),origin=tuple(origin))
    for name,data in dict(temperature_C=np.where(active,T,0.),vertida_id=ids,occupied=(ids>0).astype(np.uint8),active=active.astype(np.uint8)).items():
        grid.cell_data[name]=data.flatten(order='F')
    grid.field_data['temperature_units']=np.array(['degC']);grid.field_data['length_units']=np.array(['m'])
    grid.field_data['undefined_temperature']=np.array(['0 is fill; use active and occupied'])
    return grid


def check_vtk(grid,ids,origin,spacing,temperature,active):
    if tuple(grid.dimensions)!=tuple(np.array(ids.shape)+1) or grid.n_cells!=ids.size:raise ValueError('Dimensiones VTK')
    np.testing.assert_allclose(grid.origin,origin,atol=1e-12,rtol=0);np.testing.assert_allclose(grid.spacing,spacing,atol=1e-12,rtol=0)
    centers=grid.cell_centers().points
    index=np.indices(ids.shape).reshape(3,-1).T
    vtk_index=index[:,0]+ids.shape[0]*(index[:,1]+ids.shape[1]*index[:,2])
    np.testing.assert_allclose(centers[vtk_index],np.asarray(origin)+(index+.5)*spacing,atol=1e-12,rtol=0)
    for name,expected in dict(vertida_id=ids,occupied=ids>0,active=active,temperature_C=np.where(active,temperature,0.)).items():
        np.testing.assert_array_equal(grid.cell_data[name].reshape(ids.shape,order='F'),expected)
    return dict(status='PASS',cells=grid.n_cells,active_cells=int(active.sum()),array_order='VTK x-fast; NumPy XYZ flattened F; tested every cell and field',exact_temperature_equality=True)


def export_result(folder,output,hours):
    folder=Path(folder);output=Path(output)
    if output.exists() and any(output.iterdir()):raise ValueError('VTK existente; elegir carpeta nueva para conservar exportación')
    s=json.loads((folder/'summary.json').read_text(encoding='utf-8'))
    with np.load(folder/'grid.npz') as z:g={k:z[k] for k in z.files}
    with np.load(folder/'fields.npz') as z:f={k:z[k] for k in z.files}
    frames=sorted({int(np.argmin(abs(f['times_s']/3600-h))) for h in hours if 0<=h<=f['times_s'][-1]/3600}|{0,len(f['times_s'])//2,len(f['times_s'])-1})
    if len(frames)<3:raise ValueError('Se requieren tres estados VTK para E11')
    output.mkdir(parents=True,exist_ok=True);rows=[];root=ET.Element('VTKFile',type='Collection',version='0.1',byte_order='LittleEndian');collection=ET.SubElement(root,'Collection')
    for j,frame in enumerate(frames):
        T=np.zeros(g['vertida_id'].size);active=np.zeros_like(T,dtype=bool)
        T[g['occupied_flat_indices']]=f['weather_C'][frame];active[g['occupied_flat_indices']]=f['active'][frame]
        T=T.reshape(g['vertida_id'].shape);active=active.reshape(T.shape)
        grid=image_data(g['vertida_id'],g['origin_m'],g['spacing_m'],T,active)
        grid.field_data['elapsed_s']=np.array([f['times_s'][frame]])
        grid.field_data['simulation_start_utc']=np.array([s['simulation_start_utc']])
        name=f'state_{j:02d}.vti';grid.save(output/name,binary=True)
        reopened=pv.read(output/name);check=check_vtk(reopened,g['vertida_id'],g['origin_m'],g['spacing_m'],T,active)
        rows.append(dict(file=name,frame=frame,time_h=float(f['times_s'][frame]/3600),sha256=hashlib.sha256((output/name).read_bytes()).hexdigest(),validation=check))
        ET.SubElement(collection,'DataSet',timestep=str(float(f['times_s'][frame])),group='',part='0',file=name)
    ET.ElementTree(root).write(output/'e11.pvd',encoding='utf-8',xml_declaration=True)
    (output/'manifest.json').write_text(json.dumps(dict(states=rows,field_sha256=hashlib.sha256((folder/'fields.npz').read_bytes()).hexdigest()),indent=2)+'\n',encoding='utf-8')
    reader=pv.get_reader(output/'e11.pvd')
    if reader.time_values!=[r['time_h']*3600 for r in rows]:raise ValueError('Tiempos PVD')
    reader.set_active_time_value(reader.time_values[-1]);reader.read()
    collection_path=(output/'e11.pvd').resolve();project=Path(__file__).resolve().parents[3]
    collection_name=collection_path.relative_to(project).as_posix() if collection_path.is_relative_to(project) else collection_path.as_posix()
    return dict(states=rows,collection=collection_name,pvd_read_verified=True)
