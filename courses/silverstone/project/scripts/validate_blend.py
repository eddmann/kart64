"""Run in Blender after opening silverstone.blend to check portability and mesh geometry."""
import json
from pathlib import Path
import bpy
import numpy as np

root=Path(__file__).resolve().parents[1]
linked=[n.name for n in bpy.data.node_groups if n.library]
assert not linked, 'Shader groups still depend on external libraries: '+str(linked)
assert not any(o.library for o in bpy.data.objects), 'Objects depend on an external library'
assert not any(i.source=='FILE' and not i.packed_file for i in bpy.data.images), 'An unpacked image remains'
kerb_counts={}
for side in (-1,1):
    mesh=bpy.data.objects['Kerbs '+str(side)].data
    counts={}
    for face in mesh.polygons:
        name=mesh.materials[face.material_index].name
        counts[name]=counts.get(name,0)+1
    assert counts.get('Black',0)>counts.get('Red',0)*20,'Predominantly black/white kerb pattern did not reach the mesh'
    assert counts.get('Red',0)>0,'Selected red apex patches are absent'
    kerb_counts[str(side)]=counts
road=bpy.data.objects['Road']
assert all(face.normal.z>.99 for face in road.data.polygons), 'Road contains a flipped face'
assert all(face.area>1e-8 for face in road.data.polygons), 'Road has a degenerate face'
# Coarse grass tiles must remain below the finer elevated racing surface.
terrain=bpy.data.objects['Airfield terrain'].data
triangles=np.array([[tuple(terrain.vertices[i].co) for i in f.vertices] for f in terrain.polygons])
samples=np.array([tuple(v.co) for v in road.data.vertices])
low=triangles[:,:,:2].min(axis=1);high=triangles[:,:,:2].max(axis=1)
ground=np.full(len(samples),-np.inf)
for start in range(0,len(samples),128):
    xy=samples[start:start+128,:2]
    row,col=np.nonzero(((xy[:,None,:]>=low-1e-6)&(xy[:,None,:]<=high+1e-6)).all(axis=2))
    a,b,c=triangles[col].transpose(1,0,2)
    u=b[:,:2]-a[:,:2];v=c[:,:2]-a[:,:2];q=xy[row]-a[:,:2]
    det=u[:,0]*v[:,1]-u[:,1]*v[:,0]
    s=(q[:,0]*v[:,1]-q[:,1]*v[:,0])/det;t=(u[:,0]*q[:,1]-u[:,1]*q[:,0])/det
    valid=(s>=-1e-5)&(t>=-1e-5)&(s+t<=1+1e-5)
    z=a[:,2]+s*(b[:,2]-a[:,2])+t*(c[:,2]-a[:,2])
    np.maximum.at(ground,start+row[valid],z[valid])
assert np.isfinite(ground).all(), 'Road extends beyond the inner terrain'
geometry=json.loads((root/'source/geometry.json').read_text())
clearance=(samples[:,2]-ground)/geometry['metres_to_blender']
assert clearance.min()>.20, 'Terrain penetrates or approaches the road too closely'
kit=bpy.data.objects['Reusable Silverstone models']
track=bpy.data.objects['Silverstone — Track Root']
for o in list(track.children)+list(kit.children):
    if o.type=='MESH':
        assert all(len(f.vertices)==3 for f in o.data.polygons), o.name+' is not triangulated'
        assert all(f.area>1e-8 for f in o.data.polygons), o.name+' has a degenerate face'
        colours=np.array([tuple(c.color) for c in o.data.color_attributes['Col'].data])
        assert np.isfinite(colours).all() and (colours[:,:3]>=0).all() and (colours[:,:3]<=1).all(),o.name+' has invalid vertex colours'
        assert np.allclose(colours[:,3],1),o.name+' has corrupted vertex alpha'
sky=bpy.data.objects['Sky dome']
assert all(min(c.color[:3])>.2 for c in sky.data.color_attributes['Col'].data),'Sky has a black or corrupted colour'
expected=json.loads((root/'source/asset-library-manifest.json').read_text())['models']
assert len(kit.children)==len(expected) and all(o.asset_data is not None for o in kit.children),'Reusable asset library is incomplete'
report={'kerb_face_counts':kerb_counts,'status':'passed','linked_shader_groups':len(linked),
        'mesh_triangles':sum(len(o.data.polygons) for o in bpy.context.scene.objects if o.type=='MESH'),
        'road_normals':'all upward','degenerate_faces':0,'vertex_colours':'valid RGB, opaque alpha, nonblack sky',
        'minimum_ground_below_road_metres':float(clearance.min()),
        'asset_library_models':len(kit.children),'runtime_tested':False}
(root/'source/blend-validation-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('BLEND_VALIDATION',json.dumps(report))
