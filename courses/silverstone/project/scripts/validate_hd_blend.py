import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'silverstone-hd-preview.blend'))
manifest=json.loads((ROOT/'textures/hd/manifest.json').read_text());seen=set();packed=set()
for image in bpy.data.images:
 if '/textures/hd/' in image.filepath:
  name=Path(image.filepath).stem
  assert name in manifest and list(image.size)==manifest[name]['size'] and image.packed_file
  packed.add(name)
for material in bpy.data.materials:
 if not material.use_nodes:continue
 name=material.name.removeprefix('Render ')
 if name not in manifest:continue
 for node in material.node_tree.nodes:
  if node.type=='TEX_IMAGE':
   assert '/textures/hd/' in node.image.filepath and node.image.packed_file
   assert list(node.image.size)==manifest[name]['size'];seen.add(name)
assert packed==set(manifest) and set(manifest)-seen=={'sign_welcome','sign_race_control'}
assert any('Complete Course' in scene.name for scene in bpy.data.scenes)
assert any('Asset Library' in scene.name for scene in bpy.data.scenes)
report={'status':'passed','hd_images_packed':len(packed),'course_and_library_materials_updated':len(seen),'scenes':list(bpy.data.scenes.keys()),'checks':['All HD material nodes bind the expected resolution',f'All {len(packed)} HD PNGs packed for portability','Both course and reusable asset-library scenes present']}
(ROOT/'source/hd-blend-validation-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('HD_BLEND_PASSED',report)
