"""Write compact marked-asset libraries without including the whole race course."""
import bpy,json
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
outputs=[]
expected=len(json.loads((ROOT/'source/asset-library-manifest.json').read_text())['models'])
texture_count=len(json.loads((ROOT/'textures/hd/manifest.json').read_text()))
for source,out,hd in [('silverstone-hd-preview.blend','silverstone-hd-assets.blend',True),('silverstone.blend','silverstone-fast64-assets.blend',False)]:
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/source));scene=bpy.data.scenes['Silverstone — Asset Library']
 marks=[o for o in scene.objects if o.asset_data]
 assert len(marks)==expected
 ids={scene}
 if hd:ids.update(i for i in bpy.data.images if '/textures/hd/' in i.filepath)
 bpy.data.libraries.write(str(ROOT/out),ids,path_remap='RELATIVE',fake_user=True,compress=True)
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/out))
 bpy.context.window.scene=bpy.data.scenes['Silverstone — Asset Library']
 for screen in bpy.data.screens:
  for area in screen.areas:
   if area.type=='VIEW_3D':
    area.spaces.active.region_3d.view_location=Vector((6.6,9,0))
    area.spaces.active.region_3d.view_distance=30
 bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/out),compress=True)
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/out))
 assert bpy.context.scene.name=='Silverstone — Asset Library'
 assert len([o for o in bpy.data.objects if o.asset_data])==expected
 assert not any(o.library for o in bpy.data.objects)
 assert not any(i.source=='FILE' and not i.packed_file for i in bpy.data.images)
 if hd:assert len([i for i in bpy.data.images if '/textures/hd/' in i.filepath])==texture_count
 outputs.append({'file':out,'marked_models':expected,'size_bytes':(ROOT/out).stat().st_size,'all_file_images_packed':True})
(ROOT/'source/reusable-library-validation.json').write_text(json.dumps({'status':'passed','outputs':outputs},indent=2)+'\n')
print('REUSABLE_LIBRARIES_PASSED',outputs)
