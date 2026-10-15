"""Sample low scenery geometry against the racing ribbon, in source metres."""
import json,sys
from pathlib import Path
import bpy
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from terrain import HeightField
data=json.loads((ROOT/'source/geometry.json').read_text());P=np.array(data['points']);W=np.array(data['half_width'])
height=HeightField(data)
scale=data['metres_to_blender'];count=len(P);violations=[];tested=0;minimum=1e6
road=bpy.context.scene.objects['Road'].data
triangles=np.array([[tuple(road.vertices[i].co)[:2] for i in face.vertices] for face in road.polygons])/scale
assert triangles.shape[1]==3,'Road must be triangulated'
# Protect the marked pit travel corridor, including its entry and exit. Garage
# service equipment may stand on the wider apron beyond that corridor.
pit=json.loads((ROOT/'source/pit-shortcut.json').read_text());pr=np.array(pit['route']);pn=np.array(pit['route_normals']);ph=pit['route_half_width_metres']
left=pr-pn*ph;right=pr+pn*ph
pit_triangles=[]
for i in range(len(pr)-1):
    pit_triangles.extend([[left[i],right[i],right[i+1]],[left[i],right[i+1],left[i+1]]])
triangles=np.concatenate([triangles,np.array(pit_triangles)])

lo=triangles.min(axis=1);hi=triangles.max(axis=1)
def inside_road(samples,inclusive=False):
    """Check the actual exported ribbon, including variable-width corner joins."""
    result=np.zeros(len(samples),dtype=bool)
    for start in range(0,len(samples),256):
        points=samples[start:start+256,:2]
        candidate=((points[:,None,:]>=lo-1e-6)&(points[:,None,:]<=hi+1e-6)).all(axis=2)
        sample_index,triangle_index=np.nonzero(candidate)
        if not len(sample_index):continue
        a,b,c=triangles[triangle_index].transpose(1,0,2)
        v0=b-a;v1=c-a;v2=points[sample_index]-a
        det=v0[:,0]*v1[:,1]-v0[:,1]*v1[:,0]
        u=(v2[:,0]*v1[:,1]-v2[:,1]*v1[:,0])/det
        v=(v0[:,0]*v2[:,1]-v0[:,1]*v2[:,0])/det
        inside=((u>=-1e-5)&(v>=-1e-5)&(u+v<=1+1e-5)) if inclusive else ((u>1e-7)&(v>1e-7)&(u+v<1-1e-7))
        result[start+sample_index[inside]]=True
    return result
ignore=('Road','Kerbs','Grass shoulders','Barrier','Edge line','Airfield terrain','Historic runway',
        'Hamilton pit lane','Pit shortcut asphalt','Pit barrier','Pit perimeter fence','Pit shortcut direction arrows','Pit lane finish stripe','Starting grid','gravel runoff','braking wear','green exit paint')
for obj in bpy.context.scene.objects:
    if obj.type!='MESH' or any(x in obj.name for x in ignore):continue
    verts=np.array([tuple(obj.matrix_world@v.co) for v in obj.data.vertices])/scale
    relative_z=verts[:,2]-height(verts[:,:2])
    samples=list(verts[(relative_z>=-1e-5)&(relative_z<=4)])
    for face in obj.data.polygons:
        v=verts[list(face.vertices)]
        for point in [v.mean(axis=0)]+[(v[j]+v[(j+1)%len(v)])/2 for j in range(len(v))]:
            if -1e-5<=point[2]-height(point[:2])<=4:samples.append(point)
    if not samples:continue
    samples=np.array(samples);closest=np.argmin(np.linalg.norm(samples[:,None,:2]-P[None,:,:],axis=2),axis=1)
    clearance=np.full(len(samples),1e6)
    for offset in (-2,-1,0,1):
        a=(closest+offset)%count;b=(a+1)%count;d=P[b]-P[a]
        t=np.clip(np.sum((samples[:,:2]-P[a])*d,axis=1)/np.sum(d*d,axis=1),0,1)
        projection=P[a]+d*t[:,None];width=W[a]+(W[b]-W[a])*t
        clearance=np.minimum(clearance,np.linalg.norm(samples[:,:2]-projection,axis=1)-width)
    tested+=len(samples);minimum=min(minimum,float(clearance.min()))
    intruding=inside_road(samples)
    if intruding.any():
        index=np.flatnonzero(intruding)[0]
        violations.append({'mesh':obj.name,'sample':samples[index].tolist(),'intruding_samples':int(intruding.sum())})
# Road paint is deliberately inside the ribbon. Verify its footprint and depth separately.
paint_samples=0
for obj in bpy.context.scene.objects:
    if not obj.name.startswith('Onboard —') or 'green exit paint' not in obj.name:continue
    import xml.etree.ElementTree as ET
    sections=ET.parse(ROOT/'export/tracks/silverstone/data_track_sections').getroot()
    paint_sections=[q for q in sections if 'green_exit_paint' in q.get('gfx_path','')]
    assert len(paint_sections)==11 and all(q.get('flags')=='0' for q in paint_sections),'Road paint unexpectedly adds collision'
    verts=np.array([tuple(obj.matrix_world@v.co) for v in obj.data.vertices])/scale
    relative_z=verts[:,2]-height(verts[:,:2])
    assert np.allclose(relative_z,.26,atol=2e-5),obj.name+' is not a shallow road-paint overlay'
    assert inside_road(verts,inclusive=True).all(),obj.name+' has paint outside the asphalt ribbon'
    paint_samples+=len(verts)
report={'paint_vertices_verified_inside_road':paint_samples,'status':'passed' if not violations else 'failed','samples':tested,'minimum_estimated_clearance_metres':minimum,
        'road_intrusions':violations,'method':'Vertices, face centres and edge midpoints at 0–4 metres above local synthetic terrain checked against actual main asphalt and marked 13-metre pit travel corridor; centreline clearance is approximate at variable-width joins',
        'runtime_tested':False}
(ROOT/'source/clearance-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('SCENERY_CLEARANCE',json.dumps(report))
if violations:raise AssertionError('Scenery intersects the racing road; see clearance-report.json')
