"""Render previews from the exported geometry and the reusable asset-library scene."""
import bpy,numpy as np
from mathutils import Vector
from terrain import HeightField

def render_previews(scene,root,library_scene,library_root,materials,textures,data,destination,samples=12):
 s=data['metres_to_blender'];preview={}
 for name,source in materials.items():
  m=bpy.data.materials.new('Render '+name);m.use_nodes=True;m.diffuse_color=source.diffuse_color
  bsdf=m.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.85
  bsdf.inputs['Base Color'].default_value=source.diffuse_color
  if name=='Tyre wear':
   # Match the dark game primitive against the sRGB asphalt image.
   bsdf.inputs['Base Color'].default_value=tuple(((c+.055)/1.055)**2.4 for c in source.diffuse_color[:3])+(1,)
  if name=='Sky':
   # Match the game vertex-colour backdrop with an unlit render material.
   attr=m.node_tree.nodes.new('ShaderNodeVertexColor');attr.layer_name='Col'
   emission=m.node_tree.nodes.new('ShaderNodeEmission')
   m.node_tree.links.new(attr.outputs['Color'],emission.inputs['Color'])
   m.node_tree.links.new(emission.outputs[0],m.node_tree.nodes.get('Material Output').inputs[0])
   m.cycles.emission_sampling='NONE'
  if name in textures:
   import json
   hd_manifest=json.loads((destination/'textures/hd/manifest.json').read_text())
   hd_image=bpy.data.images.load(str(destination/'textures/hd'/hd_manifest[name]['file']),check_existing=True);hd_image.pack()
   tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=hd_image;tex.interpolation='Linear' if max(textures[name].size)>64 else 'Closest'
   m.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
   if name in ('grass','leaves'):
    attr=m.node_tree.nodes.new('ShaderNodeVertexColor');attr.layer_name='Col'
    mix_colour=m.node_tree.nodes.new('ShaderNodeMixRGB');mix_colour.blend_type='MULTIPLY';mix_colour.inputs[0].default_value=1
    m.node_tree.links.new(tex.outputs['Color'],mix_colour.inputs[1]);m.node_tree.links.new(attr.outputs['Color'],mix_colour.inputs[2])
    m.node_tree.links.new(mix_colour.outputs[0],bsdf.inputs['Base Color'])
   if name in ('fence','cloud','spectators'):
    transparent=m.node_tree.nodes.new('ShaderNodeBsdfTransparent');mix=m.node_tree.nodes.new('ShaderNodeMixShader')
    m.node_tree.links.new(tex.outputs['Alpha'],mix.inputs[0]);m.node_tree.links.new(transparent.outputs[0],mix.inputs[1])
    surface=bsdf
    if name=='cloud':
     surface=m.node_tree.nodes.new('ShaderNodeEmission');m.node_tree.links.new(tex.outputs['Color'],surface.inputs['Color'])
     m.cycles.emission_sampling='NONE'
    m.node_tree.links.new(surface.outputs[0],mix.inputs[2]);m.node_tree.links.new(mix.outputs[0],m.node_tree.nodes.get('Material Output').inputs[0])
  preview[name]=m
 for parent in (root,library_root):
  for obj in parent.children:
   if obj.type=='MESH':
    for i,mat in enumerate(obj.data.materials):obj.data.materials[i]=preview[mat.name]
    if obj.name=='Sky dome' or obj.name.startswith('Sky clouds'):
     obj.visible_shadow=False;obj.visible_diffuse=False;obj.visible_glossy=False
     obj.visible_transmission=False;obj.visible_volume_scatter=False
    if obj.name.startswith('Ground —') or 'gravel runoff' in obj.name or obj.name.startswith('Historic runway'):
     # Ground surface stamps use small export depth offsets. They should not
     # cast raised-platform shadows in the preview; the game uses vertex shade.
     obj.visible_shadow=False
 def setup(target):
  target.render.engine='CYCLES';target.cycles.samples=samples;target.cycles.use_denoising=False
  target.view_settings.view_transform='Standard';target.view_settings.look='None'
  target.world=bpy.data.worlds.new('Silverstone sky '+target.name);target.world.use_nodes=True
  target.world.node_tree.nodes['Background'].inputs[0].default_value=(.56,.73,.87,1)
  target.world.node_tree.nodes['Background'].inputs[1].default_value=.65
  light=bpy.data.lights.new('Afternoon sun','SUN');light.energy=2.0;light.angle=.10
  obj=bpy.data.objects.new('Afternoon sun',light);target.collection.objects.link(obj);obj.rotation_euler=(.35,-.55,-.7)
  camera=bpy.data.objects.new('Preview camera',bpy.data.cameras.new('Preview camera'));target.collection.objects.link(camera);target.camera=camera
  target.render.resolution_x=1600;target.render.resolution_y=1000;target.render.resolution_percentage=100
  return camera
 camera=setup(scene)
 def render(name,position,look_at,ortho=None,lens=40):
  camera.location=Vector(position)*s;camera.rotation_euler=(Vector(look_at)*s-camera.location).to_track_quat('-Z','Y').to_euler()
  camera.data.type='ORTHO' if ortho else 'PERSP';camera.data.lens=lens
  if ortho:camera.data.ortho_scale=ortho*s
  scene.render.filepath=str(destination/'previews'/name);bpy.ops.render.render(write_still=True,scene=scene.name)
 points=np.array(data['points']);centre=points.mean(axis=0);span=max(np.ptp(points[:,0]),np.ptp(points[:,1]))
 render('silverstone-overview.png',(*tuple(centre+np.array([450,-550])),1400),(*centre,0),span*1.66)
 render('hamilton-straight.png',(-7,-90,24),(38,65,1),lens=35)
 render('wing-paddock.png',(135,-150,65),(57,65,10),lens=36)
 render('pit-detail.png',(30,-12,9),(54,17,4),lens=32)
 render('sky-trackside.png',(-9,-90,3.2),(0,85,4.5),lens=28)
 height=HeightField(data)
 for name,file in [('Village','village.png'),('Copse','copse.png'),('Becketts','becketts.png'),('Stowe','stowe.png')]:
  idx=data['landmarks'][name]['path_index'];p=points[idx];delta=p-points[(idx-14)%len(points)];delta/=np.linalg.norm(delta)
  pos=p-delta*170+np.array([-delta[1],delta[0]])*35
  if name=='Village':
   pos=p-delta*190-np.array(data['normals'][idx])*115
   render(file,(*pos,85+float(height(pos))),(*(p-np.array(data['normals'][idx])*95),float(height(p))),lens=24)
   continue
  render(file,(*pos,70+float(height(pos))),(*p,float(height(p))),lens=36)
 kit_camera=setup(library_scene);kit_camera.data.type='ORTHO';kit_camera.data.ortho_scale=600*s
 kit_camera.location=Vector((480,-460,510))*s
 kit_camera.rotation_euler=(Vector((160,200,0))*s-kit_camera.location).to_track_quat('-Z','Y').to_euler()
 mesh=bpy.data.meshes.new('Asset display stage');mesh.from_pydata([(-70*s,-90*s,-.1*s),(400*s,-90*s,-.1*s),
  (400*s,500*s,-.1*s),(-70*s,500*s,-.1*s)],[],[(0,1,2,3)]);mesh.materials.append(preview['structural_concrete'])
 obj=bpy.data.objects.new('Asset display stage',mesh);library_scene.collection.objects.link(obj)
 library_scene.render.filepath=str(destination/'previews/asset-library.png');bpy.ops.render.render(write_still=True,scene=library_scene.name)
 bpy.ops.file.pack_all()
 bpy.ops.wm.save_as_mainfile(filepath=str(destination/'silverstone-preview.blend'))
