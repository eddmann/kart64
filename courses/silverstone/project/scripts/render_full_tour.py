"""Render every missing circuit section from the existing ordinary-material scene.

Run: blender -b silverstone-preview.blend -t 4 --python scripts/render_full_tour.py
The course and mod are unchanged; this only writes additional camera views.
"""
import json, math, sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from terrain import HeightField
data=json.loads((ROOT/'source/geometry.json').read_text())
points=np.array(data['points']);normals=np.array(data['normals'])
height=HeightField(data);scale=data['metres_to_blender']
scene=bpy.data.scenes['Silverstone — Complete Course']
camera=scene.camera
scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=False
scene.render.resolution_x=1600;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGB'
scene.render.threads_mode='FIXED';scene.render.threads=4
out=ROOT/'previews';out.mkdir(exist_ok=True)
views=[]

def render(filename,position,target,label,ortho=None,lens=32):
    camera.location=Vector(position)*scale
    camera.rotation_euler=(Vector(target)*scale-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type='ORTHO' if ortho else 'PERSP';camera.data.lens=lens
    camera.data.clip_end=500
    if ortho:camera.data.ortho_scale=ortho*scale
    scene.render.filepath=str(out/filename)
    bpy.ops.render.render(write_still=True,scene=scene.name)
    views.append(dict(file=filename,label=label,position=list(map(float,position)),target=list(map(float,target))))
    print('TOUR_VIEW_FINISHED',filename,flush=True)

# Exact plan view: the entire road and its surroundings fit inside the frame.
centre=(points.min(axis=0)+points.max(axis=0))/2
span=max(np.ptp(points[:,0])*1.05,np.ptp(points[:,1])*1.6)*1.12
render('full-track-topdown.png',(*centre,2200),(*centre,0),'Entire circuit — top-down',ortho=span)
from bpy_extras.object_utils import world_to_camera_view
labels=[]
for number,(name,info) in enumerate(data['landmarks'].items(),1):
    p=points[info['path_index']]
    q=world_to_camera_view(scene,camera,Vector((*p,float(height(p))))*scale)
    labels.append(dict(number=number,name=name,pixel=[q.x*1600,(1-q.y)*1000]))
(ROOT/'source/full-tour-map-labels.json').write_text(json.dumps(labels,indent=2)+'\n')

for name in ('Brooklands','Luffield','Vale','Club'):
    i=data['landmarks'][name]['path_index'];p=points[i]
    tangent=p-points[(i-16)%len(points)];tangent/=np.linalg.norm(tangent)
    # Tight interconnected sections need a wider shot to explain their route.
    distance=200 if name in ('The Loop','Aintree','Luffield','Vale','Club') else 165
    altitude=85 if distance==200 else 68
    pos=p-tangent*distance-normals[i]*35
    target=p+normals[i]*(-18 if name in ('Luffield','Woodcote') else 0)
    filename=name.lower().replace(' ','-')+'.png'
    render(filename,(*pos,float(height(pos))+altitude),(*target,float(height(target))),name,lens=30)

for label,first,last,filename in (
    ('Wellington Straight','Aintree','Brooklands','wellington-straight.png'),
    ('Hangar Straight','Chapel','Stowe','hangar-straight.png')):
    a=data['landmarks'][first]['path_index'];b=data['landmarks'][last]['path_index']
    i=(a+round((b-a)%len(points)*.48))%len(points)
    p=points[i];tangent=points[(i+2)%len(points)]-points[(i-2)%len(points)]
    tangent/=np.linalg.norm(tangent)
    pos=p-tangent*210-normals[i]*85;target=p+tangent*190
    render(filename,(*pos,float(height(pos))+105),(*target,float(height(target))),label,lens=28)

event=points.mean(axis=0)+np.array([-130,30])
pos=event+np.array([150,-190])
render('infield-airfield.png',(*pos,float(height(pos))+90),(*event,float(height(event))+4),
       'Infield — pavilion, event tents, paths and historic runway remnants',lens=30)
(ROOT/'source/full-tour-cameras.json').write_text(json.dumps(views,indent=2)+'\n')
print('FULL_TOUR_COMPLETE',len(views),flush=True)
