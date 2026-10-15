"""Supplement the HD preview with driver-height and whole-course review cameras."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
import numpy as np
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from terrain import HeightField
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'silverstone-hd-preview.blend'))
scene=bpy.data.scenes['Silverstone — Complete Course'];camera=scene.camera
scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=False
scene.render.resolution_x=1600;scene.render.resolution_y=1000
scene.render.threads_mode='FIXED';scene.render.threads=3
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
data=json.loads((ROOT/'source/geometry.json').read_text());points=np.asarray(data['points']);normals=np.asarray(data['normals']);height=HeightField(data);s=data['metres_to_blender'];views=[]
def render(name,pos,target,label,lens=32,ortho=None):
 camera.location=Vector(pos)*s;camera.rotation_euler=(Vector(target)*s-camera.location).to_track_quat('-Z','Y').to_euler()
 camera.data.type='ORTHO' if ortho else 'PERSP';camera.data.lens=lens;camera.data.clip_end=500
 if ortho:camera.data.ortho_scale=ortho*s
 scene.render.filepath=str(ROOT/'previews'/name);bpy.ops.render.render(write_still=True,scene=scene.name)
 views.append({'file':name,'label':label,'position':list(map(float,pos)),'target':list(map(float,target))})
 print('DETAIL_VIEW_READY',name,flush=True)
render('hamilton-driver-height.png',(-7,-82,3.2),(9,108,4.5),'Hamilton: lower walls at driver height',28)
render('pit-booms-detail.png',(32,-12,4.0),(54,27,4.0),'Pit booms, garage frames and metallic roof edges',32)
for name in ['Copse','Stowe']:
 i=data['landmarks'][name]['path_index'];p=points[i];t=points[(i+2)%len(points)]-points[(i-2)%len(points)];t/=np.linalg.norm(t)
 pos=p-t*115+normals[i]*14;target=p-normals[i]*45
 render(name.lower()+'-broadcast-detail.png',(*pos,float(height(pos))+19),(*target,float(height(target))+5),name+' broadcast platform and stands',32)
i=670;p=points[i];t=points[i+2]-points[i-2];t/=np.linalg.norm(t);pos=p-t*170-normals[i]*75;target=p+t*90
render('hangar-service-detail.png',(*pos,float(height(pos))+55),(*target,float(height(target))), 'Hangar Straight: service Armco and open airfield',30)
centre=(points.min(axis=0)+points.max(axis=0))/2;span=max(np.ptp(points[:,0])*1.05,np.ptp(points[:,1])*1.6)*1.12
render('full-track-topdown.png',(*centre,2200),(*centre,0),'Entire updated course',ortho=span)
(ROOT/'source/detail-review-cameras.json').write_text(json.dumps(views,indent=2)+'\n')
print('DETAIL_REVIEW_RENDERED',len(views))
