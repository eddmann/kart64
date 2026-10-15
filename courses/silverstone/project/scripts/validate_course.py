"""Check exported resource references, coordinate limits, path and offset geometry."""
import json
import xml.etree.ElementTree as ET
import zipfile
import struct
from pathlib import Path
import numpy as np
from terrain import HeightField

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'export'
TRACK=OUT/'tracks/silverstone'
checks=[]


def check(condition,message):
    if not condition:raise AssertionError(message)
    checks.append(message)


for directory in ('textures','textures/hd'):
    manifest=json.loads((ROOT/directory/'manifest.json').read_text())
    check(len({name.casefold() for name in manifest})==len(manifest),
          f'{directory} material names are distinct on case-insensitive filesystems')
    check(len({entry['file'].casefold() for entry in manifest.values()})==len(manifest),
          f'{directory} filenames are distinct on case-insensitive filesystems')


def intersections(a):
    d=np.roll(a,-1,axis=0)-a
    cross=lambda u,v:u[...,0]*v[...,1]-u[...,1]*v[...,0]
    for i in range(len(a)):
        js=np.arange(i+2,len(a))
        if i==0:js=js[js!=len(a)-1]
        den=cross(d[i],d[js]);valid=abs(den)>1e-7
        t=np.divide(cross(a[js]-a[i],d[js]),den,out=np.zeros(len(js)),where=valid)
        u=np.divide(cross(a[js]-a[i],d[i]),den,out=np.zeros(len(js)),where=valid)
        if np.any(valid&(t>1e-7)&(t<1-1e-7)&(u>1e-7)&(u<1-1e-7)):return True
    return False


data=json.loads((ROOT/'source/geometry.json').read_text())
p=np.array(data['points']);n=np.array(data['normals']);w=np.array(data['half_width']);s=np.array(data['shoulder'])
terrain_height=HeightField(data)
for label,width in [('road',w),('kerb',w+1.5),('barrier',w+1.5+s)]:
    for side in (-1,1):check(not intersections(p+n*(side*width[:,None])),f'{label} boundary {side} has no self-intersections')
paths=ET.parse(TRACK/'data_paths').getroot()
path=paths.find("TrackWaypoint[@type='0']")
check(path is not None,'Main path exists')
xyz=np.array([[int(q.get(a)) for a in ('X','Y','Z')] for q in list(path)[:-1]])
check(len(xyz)==data['sample_count'],'Path count matches source geometry')
check(np.array_equal(xyz[0],[0,0,0]),'Path starts at world origin')
check(xyz[1][2]<0 and abs(xyz[1][0])<=1,'Path starts in the engine grid direction')
check(np.max(np.linalg.norm(np.roll(xyz,-1,axis=0)-xyz,axis=1))<60,'Path closes with continuous waypoint spacing')
check(np.all(xyz[-10:,2]>0) and np.all(abs(xyz[-10:,0])<12),'Final ten points approach the grid from behind')
# Source and exported road coincide after the Blender-to-N64 rotation.
factor=data['game_units_per_metre']
expected=np.column_stack((p[:,0]*factor,np.array(data['heights'])*factor,-p[:,1]*factor))
check(np.max(abs(xyz-expected))<1,'Exported path matches road coordinate space')
resources={f.relative_to(OUT).as_posix():f for f in OUT.rglob('*') if f.is_file()}
check(len({name.casefold() for name in resources})==len(resources),
      'Exported resource paths are distinct on case-insensitive filesystems')
roots={}
vertex_count=0;coordinates=[]
binary_textures={}
for name,f in resources.items():
    if f.suffix or f.name=='mods.toml':continue
    raw=f.read_bytes()
    if not raw.lstrip().startswith(b'<'):
        check(len(raw)>=92 and struct.unpack_from('<I',raw,4)[0]==0x4F544558,f'Binary resource has OTEX header: {name}')
        version=struct.unpack_from('<I',raw,8)[0]
        width,height=struct.unpack_from('<II',raw,68)
        size=struct.unpack_from('<I',raw,88)[0]
        check(version==1 and size==width*height*2 and len(raw)==92+size,f'RGBA16 texture header and payload agree: {name}')
        check(size<=4096,f'Texture fits N64 TMEM: {name}')
        binary_textures[name]=(width,height)
        continue
    node=ET.parse(f).getroot();roots[name]=node
    for child in node.iter():
        for key in ('Path','gfx_path'):
            target=child.get(key)
            if target:check(target in resources,f'Resource reference resolves: {target}')
        if child.tag=='Vtx':
            check(all(abs(int(child.get(a)))<=32767 for a in ('S','T')),f'Texture UV coordinates fit: {name}')
            coordinates.append([int(child.get(a)) for a in ('X','Y','Z')]);vertex_count+=1
coordinates=np.array(coordinates)
check(np.max(abs(coordinates))<32767,'Every exported vertex fits signed 16-bit coordinates')
road_node=roots['tracks/silverstone/mk64_Road_mesh_vtx']
road_vertices=np.array([[int(q.get(a)) for a in ('X','Y','Z')] for q in road_node])
road_xy=np.column_stack((road_vertices[:,0],-road_vertices[:,2]))/factor
check(np.max(abs(road_vertices[:,1]-terrain_height(road_xy)*factor))<1.1,'Exported road collision follows the synthetic terrain field')
grade=np.abs(np.diff(np.r_[data['heights'],data['heights'][0]]))/(data['lap_metres']/len(p))
check(grade.max()<.04,'Racing path elevation changes stay below a four-percent grade')
for name,node in roots.items():
    if node.tag!='DisplayList':continue
    if '/mat_' in name and '/mat_revert_' not in name:
        cycle=node.find('SetCycleType');geometry=node.find('SetGeometryMode')
        check(cycle is not None and cycle.get('G_CYC_1CYCLE')=='1',f'Material establishes its cycle mode: {name}')
        check(geometry is not None and geometry.get('G_SHADE')=='1' and geometry.get('G_ZBUFFER')=='1',f'Material establishes shading and depth state: {name}')
        check(node.find('SetRenderMode') is not None,f'Material establishes its render mode: {name}')
        if node.find('SetTextureImage') is None:
            check(node.find('Texture').get('On')=='0',f'Solid material disables texture sampling: {name}')
    for cmd in node:
        if cmd.tag=='LoadVertices':
            count=len(roots[cmd.get('Path')])
            check(int(cmd.get('VertexOffset'))+int(cmd.get('Count'))<=count,f'Vertex load fits buffer: {name}')
    tex=node.find('SetTextureImage');tile=node.find('SetTileSize')
    if tex is not None and tile is not None:
        width,height=binary_textures[tex.get('Path')]
        check(int(tile.get('Lrs'))==4*(width-1) and int(tile.get('Lrt'))==4*(height-1),f'Texture tile bounds match image: {name}')
sections=roots['tracks/silverstone/data_track_sections']
build=json.loads((ROOT/'source/build-report.json').read_text())
check(len(sections)==build['mesh_objects'],'All scene meshes have exported sections')
check(build['mesh_triangles']<build['triangle_budget'],'Course stays below its declared native desktop triangle budget')
collidable=[q for q in sections if q.get('flags')!='0']
check(len(collidable)==9,'Road, kerbs, grass, pit asphalt and three wall meshes generate collision')
check(sorted(int(q.get('surface')) for q in collidable)==[1,1,1,1,4,4,4,8,8],'Collision surfaces use asphalt, stone and grass')
walls=[q for q in collidable if q.get('surface')=='4']
check(all(q.get('drawlayer')=='0' for q in walls),'All three-metre collision wall meshes use the invisible draw layer')
ordered=list(sections)
wall_indices=[ordered.index(q) for q in walls]
floor_indices=[ordered.index(q) for q in collidable if q.get('surface')!='4']
check(max(wall_indices)<min(floor_indices),'Collision walls precede all floors for the native collision-filter state')
visible=[q for q in sections if 'Barrier_visible' in q.get('gfx_path','')]
check(len(visible)==2 and all(q.get('flags')=='0' and q.get('drawlayer')=='1' for q in visible),'Lower visible barrier bases do not add collision')
sky_sections=[q for q in sections if 'Sky_' in q.get('gfx_path','')]
check(len(sky_sections)==5 and all(q.get('flags')=='0' for q in sky_sections),'Sky dome and four cloud sectors export without collision')
scene=json.loads((TRACK/'scene.json').read_text())
check(scene['Props']['ResourceName']=='eddmann:silverstone','Track metadata uses its own resource ID')
props=scene['Props'];factor_minimap=props['MinimapPlayerScaleFactor']
check(len(props['Skybox'])==24 and all(0<=v<=255 for v in props['Skybox']),'Engine skybox contains eight valid RGB colours')
sky_vertices=np.concatenate([np.array([[int(q.get(a)) for a in ('X','Y','Z')] for q in roots[name]])
                            for name in roots if 'mk64_Sky_' in name and name.endswith('_vtx')])
sky_dome=list(roots['tracks/silverstone/mk64_Sky_dome_mesh_vtx'])
check(all(int(q.get('A'))==255 and min(int(q.get(a)) for a in ('R','G','B'))>50 for q in sky_dome),
      'Exported sky has opaque alpha and nonblack vertex colours')
low_sky=[q for q in sky_dome if int(q.get('Y'))<=0]
check(bool(low_sky) and all([int(q.get(a)) for a in ('R','G','B')]==props['Skybox'][3:6] for q in low_sky),
      'Exported sky horizon matches the engine skybox palette')
for location in xyz[::20]:
    check(np.linalg.norm(sky_vertices-location,axis=1).max()<props['FarPersp'],'Sky remains inside the configured far clipping distance from the racing path')
from PIL import Image
minimap=Image.open(TRACK/'minimap.png')
marker=np.column_stack((p[:,0]*factor*factor_minimap+props['MinimapPlayerX'],
                       -p[:,1]*factor*factor_minimap+props['MinimapPlayerY']))
check(np.all(marker>=4) and np.all(marker<=92),'Minimap marker coordinates fit the outlined image with padding')
check(props['MinimapFinishlineX']==0 and props['MinimapFinishlineY']==0,'Minimap finish line coincides with the world-origin grid')
cx,cy=props['MinimapPosition']
check(cx+minimap.width/2<=320 and cy+minimap.height/2<=240,'Single-player minimap fits the base viewport')
check(len(scene['Actors'])==30 and all(a['Name']=='mk:item_box' for a in scene['Actors']),'Six rows of five stock item boxes are configured')
world=np.column_stack((p[:,0]*factor,-p[:,1]*factor))
for actor in scene['Actors']:
    loc=actor['Location'];distance=np.min(np.linalg.norm(world-[loc['x'],loc['z']],axis=1))
    check(distance<=72.1 and abs(loc['y']-terrain_height([loc['x']/factor,-loc['z']/factor])*factor)<1e-5,'Item box row lies inside the racing road and follows local elevation')
check((ROOT/'silverstone.blend').stat().st_size>1000000,'Editable Blender scene exists')
with zipfile.ZipFile(ROOT/'silverstone.o2r') as z:
    check(z.testzip() is None,'Mod archive passes CRC check')
    check(len({name.casefold() for name in z.namelist()})==len(z.namelist()),
          'Archive resource paths are distinct on case-insensitive filesystems')
    check(set(z.namelist())==set(resources),'Mod archive includes every exported resource at the correct path')
    check(all(i.compress_type==zipfile.ZIP_STORED for i in z.infolist()),'Mod uses stored ZIP entries')
report={'status':'passed','check_count':len(checks),'resource_files':len(resources),
        'binary_textures':len(binary_textures),'mesh_triangles':build['mesh_triangles'],'item_boxes':len(scene['Actors']),
        'exported_vertices':vertex_count,'coordinate_min':coordinates.min(axis=0).tolist(),
        'coordinate_max':coordinates.max(axis=0).tolist(),'path_points':len(xyz),
        'boundary_intersections':0,'runtime_tested':False,
        'elevation_range_metres':[min(data['heights']),max(data['heights'])],'maximum_path_grade_percent':float(grade.max()*100),
        'checks_summary':['Closed path at origin, aligned to grid','Six offset boundaries do not cross themselves',
                          'Resource references resolve','Vertex buffers and signed 16-bit coordinates fit',
                          'Expected collision flags and surfaces','Stored archive and metadata verified']}
(ROOT/'source/validation-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
